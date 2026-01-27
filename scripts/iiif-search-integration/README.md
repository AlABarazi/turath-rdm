# IIIF Search Integration - Test Scripts

**Purpose**: Test HOCR filesystem sync signal handlers (T1)  
**Adapted from**: `feature-hocr-fulltext-search` test scripts  
**Status**: Ready for T1 execution

---

## 📋 Available Test Scripts

### 1. `test_hocr_sync_publish.py` - Publish Testing
**Tests**: Signal fires on publish, HOCR files sync to filesystem

```bash
# Test with new record (no files)
python scripts/iiif-search-integration/test_hocr_sync_publish.py

# Test with existing record (edit → republish)
python scripts/iiif-search-integration/test_hocr_sync_publish.py <record_pid>
```

**Verifies**:
- ✅ `after_record_insert` signal fires
- ✅ HOCR directory created
- ✅ Files synced to `/hocr_mount/books/{pid}/hocr/`

---

### 2. `test_hocr_sync_delete.py` - Deletion Testing
**Tests**: All deletion scenarios (soft, hard, versioning)

```bash
# Test soft delete (normal UI delete)
python scripts/iiif-search-integration/test_hocr_sync_delete.py soft <record_pid>

# Test new version creation
python scripts/iiif-search-integration/test_hocr_sync_delete.py version <record_pid>

# Show hard delete instructions
python scripts/iiif-search-integration/test_hocr_sync_delete.py hard <record_pid>
```

**Verifies**:
- ✅ Soft delete (`is_deleted` flag) triggers cleanup
- ✅ New version creates new PID
- ✅ Old version HOCR cleaned up
- ✅ Hard delete triggers cleanup (rare)

---

### 3. `test_hocr_sync_filesystem.py` - Filesystem Verification
**Tests**: Direct filesystem inspection

```bash
# List all synced records
python scripts/iiif-search-integration/test_hocr_sync_filesystem.py

# Inspect specific record
python scripts/iiif-search-integration/test_hocr_sync_filesystem.py <record_pid>
```

**Verifies**:
- ✅ Directory structure correct
- ✅ File counts match
- ✅ File content valid HOCR
- ✅ Multiple records coexist

---

## 🧪 Complete T1 Testing Workflow

### Step 1: Setup (One-time)
```bash
# Ensure HOCR mount directory exists
mkdir -p ./hocr_mount/books

# Set environment variable (or add to docker-compose.yml)
export HOCR_MOUNT_BASE=/hocr_mount/books

# Make scripts executable
chmod +x scripts/iiif-search-integration/*.py
```

### Step 2: Test Basic Sync (Scenario 1)
```bash
# Create and publish test record
python scripts/iiif-search-integration/test_hocr_sync_publish.py

# Expected output:
# ✅ Record published: abc123-xyz
# ⏳ Watch for signal message...
# ✅ HOCR directory exists

# Verify filesystem
python scripts/iiif-search-integration/test_hocr_sync_filesystem.py abc123-xyz
```

### Step 3: Test Edit → Republish (Scenario 2)
```bash
# Use existing record with HOCR files
python scripts/iiif-search-integration/test_hocr_sync_publish.py <record_with_hocr>

# Expected:
# ✅ Old HOCR directory cleared
# ✅ New HOCR files synced
# ✅ Same PID used (not new PID!)
```

### Step 4: Test Soft Delete (Scenario 3 - CRITICAL)
```bash
# Test soft delete
python scripts/iiif-search-integration/test_hocr_sync_delete.py soft <record_pid>

# Expected:
# 🪦 Record soft deleted - cleaning up HOCR
# ✅ Directory removed
```

### Step 5: Test Versioning (Scenario 4 - CRITICAL)
```bash
# Create new version
python scripts/iiif-search-integration/test_hocr_sync_delete.py version <record_pid>

# Expected:
# 🔄 Record xyz789 is new version 2
# ✅ New PID created (not same as old)
# ✅ New version HOCR synced
# ✅ Old version HOCR cleaned up
```

### Step 6: Verify All Records
```bash
# List all synced records
python scripts/iiif-search-integration/test_hocr_sync_filesystem.py

# Expected:
# ✅ Found N synced records
# (Lists all records with HOCR files)
```

---

## 🎯 Acceptance Criteria Mapping

Each script maps to acceptance criteria from T1-details.md:

| Script | Acceptance Criteria Tested |
|--------|---------------------------|
| `test_hocr_sync_publish.py` | Initial publish, edit → republish, same PID |
| `test_hocr_sync_delete.py` | Soft delete, versioning, new PID cleanup |
| `test_hocr_sync_filesystem.py` | Directory structure, multiple records |

---

## 🚨 Critical Edge Cases to Test

Based on lessons from `feature-hocr-fulltext-search`:

### ✅ MUST TEST:
1. **Soft Delete**: `is_deleted=True` flag (most common)
2. **Versioning**: Each version gets NEW PID
3. **Old Versions**: `is_latest=false` should be skipped
4. **Same PID on Edit**: Edit keeps same PID (not new)

### ⚠️ COMMON MISTAKES:
- Assuming `before_record_delete` signal fires (it doesn't!)
- Assuming edit creates new PID (it doesn't!)
- Not cleaning up old versions (they accumulate!)

---

## 📊 Expected Signal Messages

When running tests, watch logs for these messages:

```bash
# Success messages
✅ Synced X HOCR files for record {pid}
🪦 Record {pid} soft deleted - cleaning up HOCR
🔄 Record {pid} is new version {n}
📜 Record {pid} is old version - skipping sync
🗑️ Hard delete signal for {pid}

# Error messages (debug)
❌ Failed to sync {file} for {pid}: {error}
❌ Failed to cleanup HOCR for {pid}: {error}
```

---

## 🔍 Debugging Tips

### Signal Not Firing?
```bash
# Check signal registration
docker-compose logs web-ui | grep "HOCR sync signal handlers registered"

# Check for Python errors
docker-compose logs web-ui | grep -A 5 "Error"

# Verify signals.py imported
docker-compose exec web-ui python -c "import site.turath_inveniordm.signals; print('✅ Signals module loads')"
```

### Files Not Syncing?
```bash
# Check HOCR mount exists
ls -la ./hocr_mount/books/

# Check permissions
docker-compose exec web-ui ls -la /hocr_mount/books/

# Check environment variable
docker-compose exec web-ui env | grep HOCR_MOUNT_BASE

# Manual test: Read record and check files
docker-compose exec web-ui python scripts/test_record_files.py <record_pid>
```

### Cleanup Not Working?
```bash
# Check if record is soft deleted (has is_deleted flag)
curl -k "https://127.0.0.1:5000/api/records/<pid>" | jq '.is_deleted'

# Check if old versions exist
curl -k "https://127.0.0.1:5000/api/records/<pid>" | jq '.versions'

# Manually trigger cleanup test
docker-compose exec web-ui python -c "
from site.turath_inveniordm.signals import cleanup_hocr_from_filesystem
cleanup_hocr_from_filesystem('test-pid')
"
```

---

## 📝 Test Results Template

Use this checklist after running all tests:

```markdown
## T1 Testing Results - [Date]

### Basic Functionality
- [ ] ✅/❌ Publish new record → HOCR synced
- [ ] ✅/❌ Edit → Republish → HOCR re-synced  
- [ ] ✅/❌ Multiple records coexist
- [ ] ✅/❌ Filesystem structure correct

### Critical Edge Cases
- [ ] ✅/❌ Soft delete → HOCR removed
- [ ] ✅/❌ New version → New PID created
- [ ] ✅/❌ New version → Old HOCR cleaned up
- [ ] ✅/❌ Old version skipped (is_latest=false)

### Signal Messages
- [ ] ✅/❌ "✅ Synced X files" appears
- [ ] ✅/❌ "🪦 soft deleted" appears
- [ ] ✅/❌ "🔄 new version X" appears
- [ ] ✅/❌ "📜 old version - skipping" appears

### Issues Found
- Issue 1: [Description]
  - Fix: [Solution]
- Issue 2: [Description]
  - Fix: [Solution]

### Status
- [ ] All tests passed
- [ ] Ready for T2 (Search Service)
```

---

## 🚀 Next Steps After T1

Once all tests pass:

1. **Document results** in test results template
2. **Update T1-details.md** acceptance criteria (check boxes)
3. **Commit test scripts** to git
4. **Proceed to T2** (Search Service implementation)

---

## 💡 Tips from HOCR Project

### What Went Wrong in HOCR Project (that we're avoiding):

1. **Assumed delete signals fire** → They don't! Used soft delete flag instead ✅
2. **Didn't test versioning** → Discovered it the hard way ✅
3. **Skipped edge case testing** → Bugs appeared in production ✅

### What We're Doing Right:

1. **Testing edge cases first** → Prevent bugs before they happen
2. **Using real signal discovery** → Based on actual InvenioRDM behavior
3. **Comprehensive test suite** → 3 scripts covering all scenarios

---

## 📚 Reference Documentation

- **T1 Implementation Guide**: `docs/rdm/planning/iiif-search-integration/sub-tasks/T1-details.md`
- **Critical Lessons**: `docs/rdm/planning/iiif-search-integration/explore/critical-lessons-from-hocr-project.md`
- **Old Test Scripts**: `scripts/feature-hocr-fulltext-search/` (reference only)

---

## 🤝 Contributing

When adding new test scripts:

1. Follow naming convention: `test_hocr_sync_<feature>.py`
2. Include docstring explaining what's tested
3. Add usage examples to this README
4. Map to acceptance criteria in T1-details.md

---

**Last Updated**: November 20, 2025  
**Status**: Ready for T1 testing  
**Next**: Execute T1 with comprehensive testing
