# Batch Book Upload Guide

## 🚀 Quick Start

### 1. Test with Dry Run (2 books)
```bash
cd /Users/alaaalbarazi/Projects/Turath/turath-rdm

.venv/bin/python scripts/batch_upload_books.py \
  --books-root "/Users/alaaalbarazi/Projects/Turath/chronicals/renamed_books" \
  --base-url https://127.0.0.1:5000 \
  --include-hocr \
  --book-ids "001_تاريخ_نجد" "003_تحفة_المشتاق_في_أخبار_نجد_والحجاز_والعراق" \
  --dry-run
```

### 2. Upload 2 Books (Test)
```bash
cd /Users/alaaalbarazi/Projects/Turath/turath-rdm

.venv/bin/python scripts/batch_upload_books.py \
  --books-root "/Users/alaaalbarazi/Projects/Turath/chronicals/renamed_books" \
  --base-url https://127.0.0.1:5000 \
  --include-hocr \
  --book-ids "001_تاريخ_نجد" "003_تحفة_المشتاق_في_أخبار_نجد_والحجاز_والعراق"
```

### 3. Upload ALL Books (32 books)
```bash
cd /Users/alaaalbarazi/Projects/Turath/turath-rdm

.venv/bin/python scripts/batch_upload_books.py \
  --books-root "/Users/alaaalbarazi/Projects/Turath/chronicals/renamed_books" \
  --base-url https://127.0.0.1:5000 \
  --include-hocr
```

---

## 📋 Features

### ✅ What It Does:
- Uploads multiple books in sequence
- Includes PDF + all HOCR files
- Loads metadata from `metadata.json` for each book
- Shows progress with timestamps
- Handles errors gracefully (continues on failure by default)
- Generates summary report
- Saves results to `batch_upload_results.json`

### 📊 Output Example:
```
[1/2] Uploading: 001_تاريخ_نجد
Started at: 14:30:15
--------------------------------------------------------------------------------
Loading metadata for: 001_تاريخ_نجد
✓ Using custom fields from metadata.json
Creating draft record...
✅ SUCCESS - 001_تاريخ_نجد uploaded in 45.2s

[2/2] Uploading: 003_تحفة_المشتاق_في_أخبار_نجد_والحجاز_والعراق
...

================================================================================
BATCH UPLOAD SUMMARY
================================================================================
Total books: 2
✅ Successful: 2
❌ Failed: 0
⏱️  Total time: 92.5s (1.5 minutes)
📊 Average time per book: 46.3s
```

---

## 🔧 Options

### Required:
- `--books-root` - Path to renamed_books directory

### Optional:
- `--base-url` - InvenioRDM URL (default: https://127.0.0.1:5000)
- `--include-hocr` - Upload HOCR files (recommended)
- `--book-ids` - Specific book IDs to upload (default: all books)
- `--dry-run` - Preview without uploading
- `--skip-errors` - Continue on errors (default: True)

---

## 📁 Structure Expected

Each book directory should have:
```
001_تاريخ_نجد/
├── 001_تاريخ_نجد.pdf          # PDF file
├── hocr/                       # HOCR directory
│   ├── 001.hocr
│   ├── 002.hocr
│   └── ...
└── metadata.json               # Metadata with custom fields
```

---

## 🎯 Book Selection

### Upload ALL books:
```bash
.venv/bin/python scripts/batch_upload_books.py \
  --books-root "/path/to/renamed_books" \
  --base-url https://127.0.0.1:5000 \
  --include-hocr
```

### Upload specific books:
```bash
.venv/bin/python scripts/batch_upload_books.py \
  --books-root "/path/to/renamed_books" \
  --base-url https://127.0.0.1:5000 \
  --include-hocr \
  --book-ids "001_تاريخ_نجد" "003_تحفة_المشتاق_في_أخبار_نجد_والحجاز_والعراق"
```

---

## 📝 Results File

After upload, check `batch_upload_results.json`:
```json
{
  "timestamp": "2025-11-17T14:30:00",
  "total_duration_seconds": 92.5,
  "total_books": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "book_id": "001_تاريخ_نجد",
      "success": true,
      "record_id": "abc123",
      "duration": 45.2
    },
    ...
  ]
}
```

---

## 🚨 Troubleshooting

### Error: "RDM_API_TOKEN not found"
```bash
# Set your API token
export RDM_API_TOKEN="your-token-here"
```

### Error: "ModuleNotFoundError: No module named 'requests'"
```bash
# Use .venv/bin/python instead of python3
.venv/bin/python scripts/batch_upload_books.py ...
```

### Error: "Book directory not found"
```bash
# Make sure the book ID matches the folder name exactly
ls /Users/alaaalbarazi/Projects/Turath/chronicals/renamed_books/
```

### Upload stuck or slow?
- Check InvenioRDM is running: `invenio-cli run`
- Check network: `curl -k https://127.0.0.1:5000/api/records`
- Reduce batch size: use `--book-ids` for smaller batches

---

## ⏱️ Estimated Times

**Per book (approximate)**:
- Book with 175 HOCR files: ~45-60 seconds
- Book with 464 HOCR files: ~90-120 seconds

**For 32 books total**:
- Estimated: 30-45 minutes
- Actual may vary based on:
  - File sizes
  - Network speed
  - Server performance

---

## 🔄 Workflow

1. **Prepare books** (already done):
   ```bash
   cd /Users/alaaalbarazi/Projects/Turath/chronicals
   python3 generate_book_metadata.py
   ```

2. **Start InvenioRDM**:
   ```bash
   cd /Users/alaaalbarazi/Projects/Turath/turath-rdm
   invenio-cli run
   ```

3. **Test with 2 books**:
   ```bash
   .venv/bin/python scripts/batch_upload_books.py \
     --books-root "/Users/alaaalbarazi/Projects/Turath/chronicals/renamed_books" \
     --base-url https://127.0.0.1:5000 \
     --include-hocr \
     --book-ids "001_تاريخ_نجد" "003_تحفة_المشتاق_في_أخبار_نجد_والحجاز_والعراق"
   ```

4. **Verify in browser**:
   - Open: https://127.0.0.1:5000
   - Check uploaded records

5. **Upload remaining books**:
   ```bash
   .venv/bin/python scripts/batch_upload_books.py \
     --books-root "/Users/alaaalbarazi/Projects/Turath/chronicals/renamed_books" \
     --base-url https://127.0.0.1:5000 \
     --include-hocr
   ```

---

## 📚 Related Scripts

- `records_crud.py` - Single book upload (used internally)
- `generate_book_metadata.py` - Generate metadata.json files (run first)

---

**Last Updated**: November 17, 2025
