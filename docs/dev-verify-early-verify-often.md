---
trigger: always_on
---

# Development Rule: Verify Early, Verify Often

## Golden Rule
**NEVER proceed to the next subtask without verification of the current one.**

---

## Why This Matters

### The Problem
Building features in steps without verification leads to:
- ❌ Debugging nightmares (which step broke?)
- ❌ Wasted time (fixing 5 steps when only step 2 failed)
- ❌ Compound errors (broken foundation = broken building)
- ❌ Lost confidence (is ANYTHING working?)

### The Solution
✅ Verify each step immediately after completion
✅ Know with certainty what works before moving forward
✅ Catch issues at the source (1 step to fix, not 5)
✅ Build confidence incrementally

---

## The Verification Workflow

### After EVERY subtask completion:

```
1. ✅ Complete Task Implementation
   └─> Ask: "What did we just build?"

2. 🧪 Create Verification Test
   └─> Ask: "How can we prove it works?"

3. ▶️ Run Verification
   └─> Ask: "Does it pass?"

4. 📊 Document Results
   └─> Record: Pass/Fail + Evidence

5. 🚦 Decision Point
   ├─> ✅ PASS → Proceed to next task
   └─> ❌ FAIL → Fix before continuing
```

---

## Verification Levels by Subtask Type

### Level 1: Module/Function Creation
**What to verify:**
- ✅ Module imports without errors
- ✅ Functions exist with correct signatures
- ✅ Core logic works with test inputs
- ✅ Edge cases handled (None, empty, invalid)

**How to verify:**
```bash
# Import test
pipenv run python -c "from module import function; print('✅ Import successful')"

# Unit test (create test_*.py file)
pipenv run python test_module.py

# Expected output: All tests pass
```

**Example:** T1 (Create previewer module)
- Created: `test_mirador_previewer.py`
- Verified: 10 file types, manifest extraction, error handling
- Result: ✅ ALL TESTS PASSED

---

### Level 2: Configuration/Registration
**What to verify:**
- ✅ Config file syntax is valid
- ✅ Entry points are registered
- ✅ System can discover the component

**How to verify:**
```bash
# Check registration
pipenv run python -c "from importlib.metadata import entry_points; print(list(entry_points().select(group='target_group')))"

# Check config loads
pipenv run python -c "from app import create_app; app = create_app(); print(app.config.get('KEY'))"

# Expected output: Component appears in list
```

**Example:** T2 (Register entry point)
- Check: Entry point in `setup.cfg`
- Install: `pipenv install -e site`
- Verify: Entry point appears in discovery

---

### Level 3: Template/UI Creation
**What to verify:**
- ✅ Template file exists in correct location
- ✅ Template syntax is valid (no Jinja errors)
- ✅ Template can be rendered (even without full context)

**How to verify:**
```bash
# Check file exists
ls -la path/to/template.html

# Basic render test (if possible)
pipenv run python -c "from flask import Flask, render_template; app = Flask(__name__); app.config['TEMPLATES_AUTO_RELOAD'] = True; with app.app_context(): render_template('template.html')"

# Expected output: No syntax errors
```

**Example:** T3 (Create template)
- Check: File at correct path
- Verify: Jinja2 syntax valid
- Test: Renders without errors

---

### Level 4: Integration/E2E
**What to verify:**
- ✅ Full workflow works end-to-end
- ✅ System behaves as expected in browser
- ✅ No console errors
- ✅ Network requests succeed

**How to verify:**
```bash
# Start system
invenio-cli run

# Manual browser test
open "https://127.0.0.1:5000/target-url"

# Check browser console
# - No errors (red messages)
# - Expected requests (network tab)
# - Feature works visually

# Expected output: ✅ Feature works as designed
```

**Example:** T6 (Test with sample records)
- Start: InvenioRDM
- Visit: Record with PDF
- Check: Mirador loads, manifest fetches
- Verify: No errors in console

---

## Verification Script Template

For each subtask, create a verification script:

```python
#!/usr/bin/env python3
"""
Verification script for T<N>: <Task Name>

Run with: pipenv run python verify_t<N>.py
"""

import sys

def verify_implementation():
    """Verify the implementation works."""
    print(f"🧪 Verifying T<N>: <Task Name>...")
    
    # Test 1: Basic functionality
    try:
        # Your verification code here
        print("  ✅ Test 1: <Description>")
    except Exception as e:
        print(f"  ❌ Test 1 failed: {e}")
        return False
    
    # Test 2: Edge cases
    try:
        # Your verification code here
        print("  ✅ Test 2: <Description>")
    except Exception as e:
        print(f"  ❌ Test 2 failed: {e}")
        return False
    
    return True

def main():
    print("=" * 60)
    print(f"🔍 T<N> Verification")
    print("=" * 60)
    
    if verify_implementation():
        print("\n✅ ALL CHECKS PASSED - T<N> is working!")
        return 0
    else:
        print("\n❌ VERIFICATION FAILED - Review errors above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

---

## Cascade's Responsibilities

### Before Moving to Next Task:

1. **Create Verification**
   - Ask: "How can we verify this step?"
   - Create appropriate test/check
   - Run it immediately

2. **Report Results**
   - Show output clearly
   - Explain what passed/failed
   - Document evidence

3. **Get Approval**
   - Present verification results
   - Ask: "T<N> verified and complete. Proceed to T<N+1>?"
   - Wait for user confirmation

### When Verification Fails:

1. **STOP** - Do not proceed to next task
2. **Analyze** - What specifically failed?
3. **Fix** - Address the root cause
4. **Re-verify** - Run tests again
5. **Document** - What was broken? What fixed it?

---

## Red Flags (When to Stop)

🚨 **STOP if you encounter:**
- Import errors after creating a module
- Missing entry points after registration
- Template syntax errors
- Config not loading
- Any "it should work" assumptions

🛑 **DO NOT:**
- Skip verification "to save time"
- Move forward with partial failures
- Assume "we'll test it all at the end"
- Say "it works on my machine" without proof

---

## Verification Checklist Template

Copy this for each subtask:

```markdown
## T<N> Verification Checklist

### What We Built:
- [ ] <Deliverable 1>
- [ ] <Deliverable 2>

### What We Verified:
- [ ] <Test 1>: Result
- [ ] <Test 2>: Result
- [ ] <Test 3>: Result

### Evidence:
```bash
# Command run
<command>

# Output
<output showing success>
```

### Status:
- [ ] ✅ All tests passed
- [ ] 📝 Results documented
- [ ] 🚀 Ready for next task
```

---

## Example: T1 Verification (Reference)

### What We Built:
- ✅ `site/turath_inveniordm/previewer/__init__.py`
- ✅ `site/turath_inveniordm/previewer/mirador_previewer.py`
- ✅ Functions: `can_preview()`, `preview()`

### What We Verified:
- ✅ Module imports successfully
- ✅ File type detection (10 test cases, all passed)
- ✅ Manifest URL extraction works
- ✅ Error handling for missing manifest

### Evidence:
```bash
pipenv run python site/turath_inveniordm/previewer/test_mirador_previewer.py

# Output:
✅ ALL TESTS PASSED - T1 Module is working correctly!
```

### Status:
- ✅ All tests passed
- ✅ Results documented in terminal output
- ✅ Ready for T2

---

## Summary

### The Rule:
**Each subtask must have verification BEFORE moving to the next subtask.**

### The Process:
1. Implement subtask
2. Create verification test
3. Run verification
4. Document results
5. Get approval
6. THEN proceed

### The Benefit:
✅ Confidence in every step
✅ Easy debugging (know exactly what broke)
✅ Fast development (fix issues immediately)
✅ Quality output (every piece verified)

---

**Remember:** 5 minutes of verification now saves 50 minutes of debugging later. 🧪
