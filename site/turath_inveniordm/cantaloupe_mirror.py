import json
import logging
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_PAGE_WIDTH = 1240
DEFAULT_PAGE_HEIGHT = 1754
HOCR_PAGE_BBOX_PATTERN = re.compile(
    r"class=[\'\"]ocr_page[\'\"].*?bbox\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
    re.DOTALL,
)

# DPI used when rendering PDF pages to JPEG images
PDF_RENDER_DPI = 120


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
    Convert a record's PDF into per-page JPEG images saved at:

        cantaloupe-files/{parent_id}/pages/001.jpg  (available immediately)
        cantaloupe-files/{parent_id}/pages/002.jpg  (available seconds later)
        ...

    Progressive strategy:
    1. Write dimensions.json with default values for all pages immediately
       so the IIIF manifest is valid right away.
    2. Convert and save each page one by one — Cantaloupe can serve each
       page the moment its JPEG file lands on disk.
    3. Update dimensions.json with real pixel sizes after each page.

    PDF source priority:
    - Local copy in cantaloupe-files/{parent_id}/{pdf_key} (script flow, instant)
    - S3 / MinIO download via record.files API (UI flow)

    Returns the pages directory Path on success, or None if no PDF found.
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
    dims_file = record_dir / "dimensions.json"

    # Clear stale pages from previous publishes
    if pages_dir.exists():
        shutil.rmtree(pages_dir)
    pages_dir.mkdir(parents=True, exist_ok=True)

    # --- Load PDF bytes ---
    # Prefer local copy (written by records_crud.py before publish) to avoid
    # downloading from S3/MinIO which can be slow for large files.
    local_pdf_path = record_dir / pdf_key
    if local_pdf_path.exists():
        logger.info("Using local PDF copy: %s", local_pdf_path)
        pdf_bytes = local_pdf_path.read_bytes()
    else:
        logger.info("Downloading PDF from storage: %s", pdf_key)
        file_obj = record.files[pdf_key]
        with file_obj.get_stream("rb") as source:
            pdf_bytes = source.read()

    # --- Progressive conversion ---
    scale = PDF_RENDER_DPI / 72.0
    mat = fitz.Matrix(scale, scale)

    with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf_doc:
        page_count = len(pdf_doc)

        # Write initial dimensions.json with defaults for ALL pages immediately.
        # This makes the IIIF manifest valid before any page is rendered,
        # so Mirador can open the record right away.
        default_dims = [{"w": DEFAULT_PAGE_WIDTH, "h": DEFAULT_PAGE_HEIGHT}] * page_count
        dims_file.write_text(json.dumps(default_dims), encoding="utf-8")
        logger.info("Wrote initial dimensions.json (%d pages) for %s", page_count, parent_id)

        dims: List[Dict[str, int]] = []
        for page_index in range(page_count):
            page = pdf_doc.load_page(page_index)
            pix = page.get_pixmap(matrix=mat)

            page_filename = f"{page_index + 1:03d}.jpg"
            pix.save(str(pages_dir / page_filename))

            dims.append({"w": pix.width, "h": pix.height})

            # Update dimensions.json progressively: real dims for converted
            # pages, defaults for pages not yet rendered.
            updated = dims + default_dims[len(dims):]
            dims_file.write_text(json.dumps(updated), encoding="utf-8")

    # Final write with all real dimensions
    dims_file.write_text(json.dumps(dims), encoding="utf-8")
    logger.info("Converted %d pages for %s", page_count, parent_id)

    return pages_dir


def sync_hocr_files_parallel(record, hocr_dir: str, max_workers: int = 8) -> int:
    """
    Download HOCR files from record storage to the local filesystem in parallel.

    Uses a thread pool to fetch multiple files simultaneously, dramatically
    reducing sync time for books with many pages (e.g. 175 files).

    Returns the number of HOCR files successfully synced.
    """
    if not record.files.enabled:
        return 0

    record_hocr_keys = [k for k in record.files.entries.keys() if k.endswith(".hocr")]
    if not record_hocr_keys:
        return 0

    os.makedirs(hocr_dir, exist_ok=True)

    def _download_one(file_key: str) -> bool:
        try:
            file_obj = record.files[file_key]
            with file_obj.get_stream("rb") as source:
                content = source.read()
            target = os.path.join(hocr_dir, file_key)
            with open(target, "wb") as f:
                f.write(content)
            return True
        except Exception as exc:
            logger.error("Failed to sync %s: %s", file_key, exc)
            return False

    success = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_download_one, k): k for k in record_hocr_keys}
        for future in as_completed(futures):
            if future.result():
                success += 1

    return success
