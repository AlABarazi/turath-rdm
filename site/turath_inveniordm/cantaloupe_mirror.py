import json
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DEFAULT_PAGE_WIDTH = 1240
DEFAULT_PAGE_HEIGHT = 1754
HOCR_PAGE_BBOX_PATTERN = re.compile(
    r"class=[\'\"]ocr_page[\'\"].*?bbox\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
    re.DOTALL,
)

# DPI used when rendering PDF pages to JPEG images
PDF_RENDER_DPI = 150


def get_cantaloupe_files_base() -> Path:
    base = os.environ.get("CANTALOUPE_FILES_BASE")
    if base:
        return Path(base)
    return Path("cantaloupe-files")


def get_hocr_page_dimensions(hocr_content: str) -> Optional[Tuple[int, int]]:
    match = HOCR_PAGE_BBOX_PATTERN.search(hocr_content)
    if not match:
        return None

    x1, y1, x2, y2 = map(int, match.groups())
    return x2 - x1, y2 - y1


def create_dimensions_cache_from_hocr_dir(
    hocr_dir: Path,
    output_file: Path,
) -> List[Dict[str, int]]:
    hocr_paths = sorted(hocr_dir.glob("*.hocr"))
    page_numbers: List[Tuple[int, Path]] = []
    for hocr_path in hocr_paths:
        match = re.search(r"(\d{3})\.hocr$", hocr_path.name)
        if not match:
            continue
        page_numbers.append((int(match.group(1)), hocr_path))

    if not page_numbers:
        dims = [{"w": DEFAULT_PAGE_WIDTH, "h": DEFAULT_PAGE_HEIGHT}]
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(dims), encoding="utf-8")
        return dims

    max_page = max(page for page, _ in page_numbers)
    hocr_map = {page: path for page, path in page_numbers}

    dims: List[Dict[str, int]] = []
    for page in range(1, max_page + 1):
        hocr_path = hocr_map.get(page)
        if not hocr_path:
            dims.append({"w": DEFAULT_PAGE_WIDTH, "h": DEFAULT_PAGE_HEIGHT})
            continue

        content = hocr_path.read_text(encoding="utf-8", errors="ignore")
        page_dims = get_hocr_page_dimensions(content)
        if not page_dims:
            dims.append({"w": DEFAULT_PAGE_WIDTH, "h": DEFAULT_PAGE_HEIGHT})
            continue

        width, height = page_dims
        dims.append({"w": width, "h": height})

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(dims), encoding="utf-8")
    return dims


def cleanup_cantaloupe_record_dir(parent_id: str) -> None:
    base_dir = get_cantaloupe_files_base()
    record_dir = base_dir / parent_id
    if record_dir.exists():
        shutil.rmtree(record_dir)


def mirror_pdf_pages_to_cantaloupe_filesystem(
    record, record_pid: str
) -> Optional[Path]:
    """
    Convert a record's PDF into per-page JPEG images and save them to the
    Cantaloupe filesystem at:

        cantaloupe-files/{parent_id}/pages/001.jpg
        cantaloupe-files/{parent_id}/pages/002.jpg
        ...

    A dimensions.json cache is written to cantaloupe-files/{parent_id}/
    with the actual pixel dimensions of each rendered page.

    Cantaloupe's Java2dProcessor serves JPEG files natively without the
    tiling artifacts caused by PdfBoxProcessor on PDF sources.

    Returns the pages directory Path on success, or None if no PDF is found.
    """
    if not record.files.enabled:
        return None

    pdf_key = None
    for file_key in record.files.entries.keys():
        if file_key.lower().endswith(".pdf"):
            pdf_key = file_key
            break

    if not pdf_key:
        return None

    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise RuntimeError(
            "PyMuPDF (pymupdf) is required for PDF-to-image conversion. "
            "Install it with: pipenv install pymupdf"
        )

    parent_id = record.parent.pid.pid_value
    base_dir = get_cantaloupe_files_base()
    record_dir = base_dir / parent_id
    pages_dir = record_dir / "pages"

    # Clear any existing pages so stale images don't linger after a re-publish
    if pages_dir.exists():
        shutil.rmtree(pages_dir)
    pages_dir.mkdir(parents=True, exist_ok=True)

    # Read the PDF from record storage (S3 / MinIO) into memory
    file_obj = record.files[pdf_key]
    with file_obj.get_stream("rb") as source:
        pdf_bytes = source.read()

    # Render each page at PDF_RENDER_DPI and save as JPEG
    scale = PDF_RENDER_DPI / 72.0
    mat = fitz.Matrix(scale, scale)

    dims: List[Dict[str, int]] = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf_doc:
        for page_index in range(len(pdf_doc)):
            page = pdf_doc.load_page(page_index)
            pix = page.get_pixmap(matrix=mat)

            page_filename = f"{page_index + 1:03d}.jpg"
            pix.save(str(pages_dir / page_filename))

            dims.append({"w": pix.width, "h": pix.height})

    # Write dimensions cache from actual rendered image sizes
    dims_file = record_dir / "dimensions.json"
    dims_file.write_text(json.dumps(dims), encoding="utf-8")

    return pages_dir
