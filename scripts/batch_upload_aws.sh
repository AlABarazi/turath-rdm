#!/bin/bash
# Batch upload all books from processed_books to AWS InvenioRDM
set -euo pipefail

export RDM_API_TOKEN="ZhnBQfz23FIINaQebNr3YOEjPlOXnhhFOfIQzYhXBj017k8eHJLhOniMhhE6"
BOOKS_ROOT="/Users/alaaalbarazi/Projects/Turath/chronicals/processed_books"
BASE_URL="https://invenio.turath-project.com"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$SCRIPT_DIR/batch_upload_aws.log"

success=0
fail=0
failed_books=""
total=0

# Count books first
for book_dir in "$BOOKS_ROOT"/*/; do
    [ -d "$book_dir" ] || continue
    book_id=$(basename "$book_dir")
    [[ "$book_id" == .* ]] && continue
    # Must have PDF and metadata.json
    if ls "$book_dir"*.pdf 1>/dev/null 2>&1 && [ -f "$book_dir/metadata.json" ]; then
        total=$((total + 1))
    fi
done

echo "========================================"
echo "BATCH UPLOAD: $total books to $BASE_URL"
echo "Started: $(date)"
echo "Log: $LOG_FILE"
echo "========================================"

num=0
for book_dir in "$BOOKS_ROOT"/*/; do
    [ -d "$book_dir" ] || continue
    book_id=$(basename "$book_dir")
    [[ "$book_id" == .* ]] && continue
    
    # Must have PDF and metadata.json
    ls "$book_dir"*.pdf 1>/dev/null 2>&1 || continue
    [ -f "$book_dir/metadata.json" ] || continue
    
    num=$((num + 1))
    echo ""
    echo "[$num/$total] Uploading: $book_id"
    echo "  Started: $(date +%H:%M:%S)"
    
    if python3 "$SCRIPT_DIR/records_crud.py" ingest-book \
        --books-root "$BOOKS_ROOT" \
        --book-id "$book_id" \
        --include-hocr \
        --base-url "$BASE_URL" >> "$LOG_FILE" 2>&1; then
        success=$((success + 1))
        # Extract record ID from log
        record_id=$(grep -o "'record_id': '[^']*'" "$LOG_FILE" | tail -1 | cut -d"'" -f4)
        echo "  ✅ SUCCESS (record: $record_id)"
    else
        fail=$((fail + 1))
        failed_books="$failed_books\n  - $book_id"
        echo "  ❌ FAILED"
    fi
done

echo ""
echo "========================================"
echo "BATCH COMPLETE: $(date)"
echo "  Success: $success / $total"
echo "  Failed:  $fail / $total"
if [ -n "$failed_books" ]; then
    echo -e "  Failed books:$failed_books"
fi
echo "  Full log: $LOG_FILE"
echo "========================================"
