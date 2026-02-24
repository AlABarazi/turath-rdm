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


def mirror_pdf_to_cantaloupe_filesystem(record, record_pid: str) -> Optional[Path]:
    if not record.files.enabled:
        return None

    pdf_key = None
    for file_key in record.files.entries.keys():
        if file_key.lower().endswith(".pdf"):
            pdf_key = file_key
            break

    if not pdf_key:
        return None

    parent_id = record.parent.pid.pid_value
    base_dir = get_cantaloupe_files_base()
    record_dir = base_dir / parent_id
    record_dir.mkdir(parents=True, exist_ok=True)

    target_pdf_path = record_dir / pdf_key
    file_obj = record.files[pdf_key]
    with file_obj.get_stream("rb") as source:
        with open(target_pdf_path, "wb") as target:
            shutil.copyfileobj(source, target)

    return target_pdf_path
