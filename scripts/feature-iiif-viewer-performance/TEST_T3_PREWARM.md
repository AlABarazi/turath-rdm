# T3 Pre-warming Test Plan

## ✅ Implementation Complete

### What Was Added:
1. `prewarm_iiif_cache()` function - Pre-warms Cantaloupe cache by requesting pages
2. `--prewarm-pages` CLI argument - Controls pre-warming behavior
3. Integration into `upload_book()` - Automatically pre-warms after upload
4. `records_crud.py` now returns `record_id` for pre-warming

### Files Modified:
- `scripts/batch_upload_books.py` - Added pre-warming logic
- `scripts/records_crud.py` - Returns record_id

---

## 🧪 Test Steps

### Test 1: No Pre-warming (Baseline)
```bash
cd /Users/alaaalbarazi/Projects/Turath/turath-rdm

# Upload without pre-warming
.venv/bin/python scripts/batch_upload_books.py \
  --books-root "/Users/alaaalbarazi/Projects/Turath/chronicals/renamed_books" \
  --book-ids "001_تاريخ_نجد" \
  --base-url https://127.0.0.1:5000 \
  --include-hocr \
  --prewarm-pages 0
```

**Expected**: Upload completes, no pre-warming message

### Test 2: Pre-warm First 5 Pages (Quick Test)
```bash
cd /Users/alaaalbarazi/Projects/Turath/turath-rdm

# Upload with pre-warming of first 5 pages
.venv/bin/python scripts/batch_upload_books.py \
  --books-root "/Users/alaaalbarazi/Projects/Turath/chronicals/renamed_books" \
  --book-ids "001_تاريخ_نجد" \
  --base-url https://127.0.0.1:5000 \
  --include-hocr \
  --prewarm-pages 5
```

**Expected**:
- Upload completes
- Shows "🔥 Pre-warming first 5 pages..."
- Progress updates at page 5
- Shows "✅ Pre-warmed 5/5 pages in X.Xs"
- Total time: +5-10 seconds

### Test 3: Pre-warm First 10 Pages (Default)
```bash
cd /Users/alaaalbarazi/Projects/Turath/turath-rdm

# Upload with default pre-warming (10 pages)
.venv/bin/python scripts/batch_upload_books.py \
  --books-root "/Users/alaaalbarazi/Projects/Turath/chronicals/renamed_books" \
  --book-ids "001_تاريخ_نجد" \
  --base-url https://127.0.0.1:5000 \
  --include-hocr
```

**Expected**:
- Upload completes
- Shows "🔥 Pre-warming first 10 pages..."
- Progress update at page 10
- Shows "✅ Pre-warmed 10/10 pages in X.Xs"
- Total time: +10-20 seconds

### Test 4: Verify Cache Works
```bash
# After Test 2 or 3, check Cantaloupe cache
docker exec turath-rdm-cantaloupe-1 du -sh /var/cache/cantaloupe/

# Should show larger cache size (~few MB for 5-10 pages)

# Test page load speed for pre-warmed page
time curl -k -o /dev/null -s "https://127.0.0.1:5000/iiif/2/{RECORD_ID}/p001/full/400,/0/default.jpg"

# Should be <0.5 seconds
```

---

## 📊 Expected Results

| Test | Pre-warm | Upload Time | Cache Size | Page 1 Load Time |
|------|----------|-------------|------------|------------------|
| Test 1 | None | ~1-2 min | 0 MB | 2-5s (first view) |
| Test 2 | 5 pages | ~1-2 min + 10s | ~1-2 MB | <0.5s |
| Test 3 | 10 pages | ~1-2 min + 20s | ~2-4 MB | <0.5s |

---

## 🚀 Next Steps After Testing

1. ✅ Verify pre-warming works (Test 2)
2. ✅ Verify cache persists (Test 4)
3. ⏳ Add Option 2 (Background pre-warming) if needed
4. ⏳ Add Option 3 (Full parallel pre-warming) if needed
5. ⏳ Update GitHub issue #58 with progress
6. ⏳ Move to T4 (Performance Testing)

---

## 🐛 Troubleshooting

### If pre-warming fails:
- Check InvenioRDM is running: `curl -k https://127.0.0.1:5000/ping`
- Check Cantaloupe is running: `curl http://127.0.0.1:8182/iiif/2/`
- Check record_id is valid
- Check HOCR files were uploaded

### If pages are still slow:
- Verify cache directory: `docker exec turath-rdm-cantaloupe-1 ls -la /var/cache/cantaloupe/`
- Check Cantaloupe logs: `docker logs turath-rdm-cantaloupe-1 --tail 50`
- Verify cache is enabled in config

---

**Status**: Ready to test! 🧪
