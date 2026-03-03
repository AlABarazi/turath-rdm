"""
Standalone test: convert an existing mirrored PDF to per-page JPEG images.

Usage:
    python scripts/test_pdf_to_images.py <parent_id>
    python scripts/test_pdf_to_images.py  # uses first available record

The script reads the PDF from cantaloupe-files/{parent_id}/ and writes
JPEG images to cantaloupe-files/{parent_id}/pages/.
"""
import json
import shutil
import sys
from pathlib import Path

CANTALOUPE_FILES = Path("cantaloupe-files")
DPI = 150


def convert(parent_id: str) -> None:
    record_dir = CANTALOUPE_FILES / parent_id

    # Find the PDF
    pdf_paths = sorted(p for p in record_dir.iterdir() if p.suffix.lower() == ".pdf")
    if not pdf_paths:
        print(f"No PDF found in {record_dir}")
        sys.exit(1)
    pdf_path = pdf_paths[0]
    print(f"Converting: {pdf_path}")

    import fitz  # PyMuPDF

    pages_dir = record_dir / "pages"
    if pages_dir.exists():
        shutil.rmtree(pages_dir)
    pages_dir.mkdir()

    scale = DPI / 72.0
    mat = fitz.Matrix(scale, scale)
    dims = []

    with fitz.open(str(pdf_path)) as doc:
        page_count = len(doc)
        print(f"Pages: {page_count}")
        for i in range(page_count):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=mat)
            fname = f"{i + 1:03d}.jpg"
            pix.save(str(pages_dir / fname))
            dims.append({"w": pix.width, "h": pix.height})
            print(f"  {fname}  {pix.width}x{pix.height}px")

    dims_file = record_dir / "dimensions.json"
    dims_file.write_text(json.dumps(dims), encoding="utf-8")
    print(f"\ndimensions.json written: {dims_file}")
    print(f"Pages dir: {pages_dir}")
    print("\nDone. Re-fetch the IIIF manifest in Mirador to pick up the new image URLs.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pid = sys.argv[1]
    else:
        dirs = sorted(p.name for p in CANTALOUPE_FILES.iterdir() if p.is_dir())
        if not dirs:
            print("No records found in cantaloupe-files/")
            sys.exit(1)
        pid = dirs[0]
        print(f"No parent_id given, using first: {pid}")

    convert(pid)
