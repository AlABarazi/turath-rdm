# Convenience targets for common maintenance commands

# Ensure Homebrew Cairo dylibs are found when running via make (non-interactive shell).
# Try the current env var; if empty, fall back to Homebrew's lib dir automatically.
BREW_PREFIX := $(shell brew --prefix 2>/dev/null)
CAIRO_LIB_DEFAULT := $(BREW_PREFIX)/lib
DYLD_FALLBACK_LIBRARY_PATH ?= $(shell printenv DYLD_FALLBACK_LIBRARY_PATH)
ifeq ($(strip $(DYLD_FALLBACK_LIBRARY_PATH)),)
  ifneq ($(strip $(BREW_PREFIX)),)
    DYLD_FALLBACK_LIBRARY_PATH := $(CAIRO_LIB_DEFAULT)
  endif
endif

# Generate an API token and update RDM_API_TOKEN in .env using invenio shell.
# Usage: make token
.PHONY: token
token:
	DYLD_FALLBACK_LIBRARY_PATH=$(DYLD_FALLBACK_LIBRARY_PATH) \
		invenio shell -c "import runpy, sys; ns = runpy.run_path('scripts/create_api_token.py', run_name='__not_main__'); rc = ns['main'](); sys.exit(rc) if rc else None"

# Same as `make token` but avoids the SystemExit message from IPython by
# running the script via runpy without __main__.
# Usage: make token-silent
.PHONY: token-silent
token-silent:
	DYLD_FALLBACK_LIBRARY_PATH=$(DYLD_FALLBACK_LIBRARY_PATH) \
		invenio shell -c "import runpy; runpy.run_path('scripts/create_api_token.py', run_name='__not_main__')"

# MinIO / Storage helpers
.PHONY: storage-setup
storage-setup:
	DYLD_FALLBACK_LIBRARY_PATH=$(DYLD_FALLBACK_LIBRARY_PATH) \
		python scripts/storage/minio_setup_workflow.py

.PHONY: storage-verify
storage-verify:
	DYLD_FALLBACK_LIBRARY_PATH=$(DYLD_FALLBACK_LIBRARY_PATH) \
		invenio shell -c "exec(open('scripts/verify_storage.py').read())"
