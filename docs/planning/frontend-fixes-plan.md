---
description: Plan to fix Turath InvenioRDM frontend display, HOCR indexing, thumbnails, and record page routing in AWS.
---

# Frontend + Indexing Fix Plan

## Problem Statement
AWS deployment shows search page layout issues, missing thumbnails, broken full-text search, and 404 record pages. Local dev does not show these issues. We need to identify config/build differences, then apply minimal fixes and verify in AWS.

## Goals
1. Search results layout matches local (no left whitespace).
2. Thumbnails render for uploaded books.
3. HOCR full-text indexing works (search results include matches).
4. Record detail page loads (metadata + Mirador).

## Non-Goals
- No UI redesign.
- No new features beyond restoring expected behavior.

## Risks / Unknowns
- Deployed image may not include compiled assets or overrides.
- AWS config may override SITE_UI_URL, IIIF search base URLs, or HOCR mount paths.
- Search service may not be reachable over HTTPS from the UI.

## Work Plan (verify each step)

### T1. Confirm deployed config vs local
**Why:** Most failures look like runtime config drift (SITE_UI_URL, HOCR paths, IIIF search URL, static assets).

**Tasks:**
- Check ECS task definition env vars for:
  - SITE_UI_URL, SITE_API_URL
  - HOCR_MOUNT_BASE / HOCR_MOUNT_PATH
  - IIIF_SEARCH_SERVICE_BASE_URL / RDM_IIIF_SEARCH_ENABLED
- Check ALB/Nginx routing and record page host.

**Verification:**
- `curl -k https://alb-invenio.turath-project.com/api/records/r8r3j-kfn71`
- Inspect `links.self_html` and `links.files` in the response.

### T2. Fix search layout whitespace ✅ FIXED (2026-02-06)
**Root cause:** CSS was always built into webpack, but the custom templates (with `turath-search-*` classes) weren't loading because blueprint templates have lower priority than core InvenioRDM templates in Flask's Jinja2 loader.

**Fix:** Added `COPY ./site/turath_inveniordm/templates/ ${INVENIO_INSTANCE_PATH}/templates/` to the Dockerfile. Instance path templates have highest Jinja2 priority, so custom templates now override defaults.

**Verified:** `curl -k -sS https://alb-invenio.turath-project.com/search | grep -c 'turath-search'` returns > 0.

### T3. Restore thumbnails in search results
**Why:** UI looks for `thumbnail.jpg|png|jpeg` in record files.

**Tasks:**
- Ensure upload script adds a thumbnail file (from `chronicals/processed_books_final/000_تاريخ_نجد`).
- Confirm AWS record files include `thumbnail.*`.

**Verification:**
- `curl -k https://alb-invenio.turath-project.com/api/records/r8r3j-kfn71 | jq .files.entries | keys`
- Validate that `thumbnail.*` exists and `/content` URL returns 200.

### T4. Fix HOCR indexing (full-text search)
**Why:** HOCR sync uses `HOCR_MOUNT_BASE`, but extraction uses `HOCR_MOUNT_PATH`.

**Tasks:**
- Align HOCR path configuration (use one env var).
- Ensure search service + CSP allow HTTPS requests.
- Re-index the record after fix.

**Verification:**
- Search for a word present in HOCR and confirm highlight.
- Check logs for successful indexing.

### T5. Fix record page 404 ✅ FIXED (2026-02-03)
**Root cause:** The route existed but the UI crashed loading custom fields. `VocabularyCF(...).options(...)` raised `sqlalchemy.exc.NoResultFound` because `VocabularyType` rows were missing from the database.

**Fix:** Ran `invenio rdm-records fixtures` inside the `web-ui` container to load `app_data/vocabularies.yaml` and create the missing vocabulary type entries.

**Verified:** `curl -k -I https://alb-invenio.turath-project.com/records/r8r3j-kfn71` returns 200.

## Status
- T1: Partially done (config verified through debugging sessions)
- T2: ✅ Fixed (2026-02-06) — Dockerfile template copy fix
- T3: **TODO** — Thumbnails still missing
- T4: **TODO** — HOCR full-text indexing not working
- T5: ✅ Fixed (2026-02-03) — Vocabulary fixtures loaded

Next: T3 or T4.
