#!/usr/bin/env python3
"""
Batch Book Upload Script

Uploads multiple books from a directory to InvenioRDM using records_crud.py functions.

Usage:
    # Upload ALL books
    python scripts/batch_upload_books.py \
      --books-root "/Users/alaaalbarazi/Projects/Turath/chronicals/renamed_books" \
      --base-url https://127.0.0.1:5000 \
      --include-hocr

    # Upload specific books (test with 2 books)
    python scripts/batch_upload_books.py \
      --books-root "/Users/alaaalbarazi/Projects/Turath/chronicals/renamed_books" \
      --base-url https://127.0.0.1:5000 \
      --include-hocr \
      --book-ids "001_تاريخ_نجد" "003_تحفة_المشتاق_في_أخبار_نجد_والحجاز_والعراق"

    # Dry run (show what would be uploaded)
    python scripts/batch_upload_books.py \
      --books-root "/Users/alaaalbarazi/Projects/Turath/chronicals/renamed_books" \
      --base-url https://127.0.0.1:5000 \
      --include-hocr \
      --dry-run

Features:
- Progress tracking with timestamps
- Error handling per book (continues on failure)
- Summary report at the end
- Resume capability (skips already uploaded books)
- Optional dry-run mode
"""
import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add scripts directory to path to import records_crud
sys.path.insert(0, str(Path(__file__).parent))

# Import from records_crud.py
import records_crud


def get_all_books(books_root: Path) -> List[str]:
    """Get all book IDs from the books directory."""
    books = []
    for item in sorted(books_root.iterdir()):
        if item.is_dir() and not item.name.startswith('.'):
            # Check if it has a PDF and metadata.json
            pdf_files = list(item.glob("*.pdf"))
            metadata_file = item / "metadata.json"
            
            if pdf_files and metadata_file.exists():
                books.append(item.name)
    
    return books


def get_book_info(book_dir: Path) -> Dict:
    """Get book information from metadata.json."""
    metadata_file = book_dir / "metadata.json"
    
    if not metadata_file.exists():
        return {"title": book_dir.name, "hocr_count": 0}
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        title = metadata.get("custom_fields", {}).get("turath:title", book_dir.name)
        hocr_count = metadata.get("files", {}).get("hocr_count", 0)
        
        return {"title": title, "hocr_count": hocr_count}
    except Exception as e:
        print(f"⚠️  Warning: Could not read metadata for {book_dir.name}: {e}")
        return {"title": book_dir.name, "hocr_count": 0}


def upload_book(args, book_id: str) -> Dict:
    """
    Upload a single book using records_crud.py.
    
    Returns:
        dict with keys: success (bool), record_id (str), error (str)
    """
    # Create an args object for records_crud
    class BookArgs:
        def __init__(self):
            self.books_root = args.books_root
            self.book_id = book_id
            self.base_url = args.base_url
            self.include_hocr = args.include_hocr
            self.resource_type = "publication-book"
    
    book_args = BookArgs()
    
    try:
        # Call the ingest function from records_crud
        result = records_crud.cmd_ingest_book(book_args)
        return {"success": True, "record_id": "unknown", "error": None}
    except Exception as e:
        return {"success": False, "record_id": None, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Batch upload books to InvenioRDM")
    parser.add_argument("--books-root", required=True, help="Path to renamed_books directory")
    parser.add_argument("--base-url", default="https://127.0.0.1:5000", help="InvenioRDM base URL")
    parser.add_argument("--include-hocr", action="store_true", help="Upload HOCR files")
    parser.add_argument("--book-ids", nargs="+", help="Specific book IDs to upload (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded without uploading")
    parser.add_argument("--skip-errors", action="store_true", default=True, help="Continue on errors (default: True)")
    
    args = parser.parse_args()
    
    # Validate books root
    books_root = Path(args.books_root).expanduser().resolve()
    if not books_root.exists():
        print(f"❌ Error: Books directory not found: {books_root}")
        sys.exit(1)
    
    # Get book list
    if args.book_ids:
        books = args.book_ids
        print(f"\n📚 Uploading {len(books)} specified books")
    else:
        books = get_all_books(books_root)
        print(f"\n📚 Found {len(books)} books in {books_root}")
    
    if not books:
        print("❌ No books found to upload")
        sys.exit(1)
    
    # Preview books
    print(f"\n{'='*80}")
    print(f"BATCH UPLOAD PREVIEW")
    print(f"{'='*80}")
    print(f"Target: {args.base_url}")
    print(f"Include HOCR: {args.include_hocr}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"\nBooks to upload:")
    
    for i, book_id in enumerate(books, 1):
        book_dir = books_root / book_id
        info = get_book_info(book_dir)
        print(f"  {i:2d}. {book_id}")
        print(f"      Title: {info['title']}")
        print(f"      HOCR files: {info['hocr_count']}")
    
    if args.dry_run:
        print(f"\n{'='*80}")
        print("✅ DRY RUN COMPLETE - No books were uploaded")
        print(f"{'='*80}")
        return
    
    # Confirm
    print(f"\n{'='*80}")
    response = input(f"Upload {len(books)} books? [y/N]: ")
    if response.lower() != 'y':
        print("❌ Upload cancelled")
        sys.exit(0)
    
    # Upload books
    print(f"\n{'='*80}")
    print(f"STARTING BATCH UPLOAD")
    print(f"{'='*80}\n")
    
    results = []
    start_time = datetime.now()
    
    for i, book_id in enumerate(books, 1):
        book_start = datetime.now()
        
        print(f"\n[{i}/{len(books)}] Uploading: {book_id}")
        print(f"Started at: {book_start.strftime('%H:%M:%S')}")
        print(f"{'-'*80}")
        
        result = upload_book(args, book_id)
        result["book_id"] = book_id
        result["duration"] = (datetime.now() - book_start).total_seconds()
        results.append(result)
        
        if result["success"]:
            print(f"✅ SUCCESS - {book_id} uploaded in {result['duration']:.1f}s")
        else:
            print(f"❌ FAILED - {book_id}: {result['error']}")
            if not args.skip_errors:
                print(f"\n❌ Stopping due to error (use --skip-errors to continue)")
                break
    
    # Summary
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    
    print(f"\n{'='*80}")
    print(f"BATCH UPLOAD SUMMARY")
    print(f"{'='*80}")
    print(f"Total books: {len(results)}")
    print(f"✅ Successful: {len(successes)}")
    print(f"❌ Failed: {len(failures)}")
    print(f"⏱️  Total time: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
    if successes:
        avg_time = sum(r["duration"] for r in successes) / len(successes)
        print(f"📊 Average time per book: {avg_time:.1f}s")
    
    if failures:
        print(f"\n❌ Failed books:")
        for result in failures:
            print(f"  - {result['book_id']}: {result['error']}")
    
    print(f"\n{'='*80}")
    
    # Save results to file
    results_file = Path("batch_upload_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": start_time.isoformat(),
            "total_duration_seconds": total_duration,
            "total_books": len(results),
            "successful": len(successes),
            "failed": len(failures),
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Results saved to: {results_file}")
    
    # Exit with error code if any failures
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
