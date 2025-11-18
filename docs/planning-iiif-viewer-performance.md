# IIIF Viewer Performance Optimization - Planning

**Feature Branch**: `feature/iiif-viewer-performance`  
**Status**: Planning Complete - Ready for Implementation

---

## 📍 Planning Documentation Location

Full planning documents are stored in Google Drive:

```
/Users/alaaalbarazi/Library/CloudStorage/GoogleDrive-alaabarazi@gmail.com/My Drive/Coding/resources/docs/rdm/planning/iiif-viewer-performance/
```

### Documents:
- **master-plan.md** - High-level overview & strategy
- **task-breakdown.md** - 5 major work packages (T1-T5)
- **sub-tasks/** - Detailed implementation steps
  - T1-details.md - Cantaloupe config optimization  
  - T2-details.md - Manifest generation fix
  - T3-details.md - Cache pre-warming implementation
- **README.md** - Quick start guide

---

## 🎯 Quick Summary

### Problem
Large PDF books (175-464 pages) take 5+ minutes to load due to:
- Manifest generation making 464 HTTP requests
- Cantaloupe source caching disabled
- High-resolution processing (150 DPI)

### Solution
**3-Phase Optimization**:
1. **Phase 1** (Required): Config optimization + manifest fix → 50% faster
2. **Phase 2** (Optional): Cache pre-warming → 90% faster (instant first 10 pages)
3. **Phase 3**: Testing & documentation

### Impact
- **Before**: 5-10 minutes first view
- **After**: <10 seconds all views, instant first 10 pages

---

## 📋 Task Breakdown

| ID | Task | Effort | Dependencies |
|----|------|---------|--------------|
| T1 | Cantaloupe Config | S (2-3h) | None |
| T2 | Manifest Fix | S (1-2h) | None |
| T3 | Cache Pre-warming | M (1-2d) | T1, T2 |
| T4 | Testing | S (3-4h) | T1, T2, T3 |
| T5 | Documentation | S (2-3h) | T4 |

**Total**: 2-3 days

---

## 🚀 Quick Start

```bash
# View all planning docs
open "/Users/alaaalbarazi/Library/CloudStorage/GoogleDrive-alaabarazi@gmail.com/My Drive/Coding/resources/docs/rdm/planning/iiif-viewer-performance"
```

---

## ✅ Changes Already Made

1. ✅ **Manifest Generation Fix** (T2 - Completed Nov 17, 2025)
   - Disabled slow dimension fetching
   - Using default A4 dimensions (1240×1754)
   - CSP updated to allow Mirador scripts
   - **Files**: `site/turath_inveniordm/iiif_patch.py`, `invenio.cfg`

2. ✅ **Partial Cantaloupe Fix** (T1 - Completed Nov 17, 2025)
   - Source caching enabled
   - **File**: `docker/cantaloupe/cantaloupe.properties`

---

## ⏳ Remaining Tasks

### T1: Complete Cantaloupe Optimization (2-3 hours)
- [ ] Lower DPI from 150 to 100
- [ ] Add JPEG compression (quality=75)
- [ ] Enable progressive JPEG
- [ ] Optimize HTTP timeout
- [ ] Test and verify cache hit rate

### T3: Implement Cache Pre-warming (1-2 days)
- [ ] Add `prewarm_cache()` function to batch upload script
- [ ] Add `--prewarm-pages` CLI flag
- [ ] Implement parallel pre-warming (5 workers)
- [ ] Add background pre-warming option
- [ ] Test with 175-page and 464-page books

### T4: Performance Testing (3-4 hours)
- [ ] Benchmark before/after for both book sizes
- [ ] Measure cache hit rates
- [ ] Validate multi-user access
- [ ] Verify access control still works

### T5: Documentation (2-3 hours)
- [ ] Update README with performance section
- [ ] Document Cantaloupe config rationale
- [ ] Update BATCH_UPLOAD_GUIDE with pre-warming options
- [ ] Create performance benchmarks doc

---

## 📊 Expected Results

### Upload Time
- No pre-warming: 40s (175 pages)
- First 10 pages: +20s
- All pages: +3-5 minutes (464 pages)

### Page Load Time
- Phase 1: 2-3s first view, <1s cached
- Phase 2: <1s (instant for pre-warmed pages)

### ROI (10 users, 464-page book)
- Before: 50 minutes total wait
- After: 6 minutes total (**88% reduction**)

---

## 🔗 Related Files

### To Modify:
- `docker/cantaloupe/cantaloupe.properties` - T1 remaining changes
- `scripts/batch_upload_books.py` - T3 pre-warming
- `scripts/BATCH_UPLOAD_GUIDE.md` - T5 documentation

### Already Modified:
- ✅ `site/turath_inveniordm/iiif_patch.py` - Manifest fix
- ✅ `invenio.cfg` - CSP fix
- ✅ `docker/cantaloupe/cantaloupe.properties` - Cache enabled

---

**For detailed step-by-step instructions, see the planning docs in Google Drive!** 🚀
