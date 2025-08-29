# Makefile Usage Guide

This project includes a small Makefile with convenience targets to manage API tokens via the Invenio shell. Below is a concise guide on what these targets do and how to use them safely.

## Overview
- `make token` — Generates a personal API token for the admin user and writes it to `.env` as `RDM_API_TOKEN` (with a timestamped backup of `.env`).
- `make token-silent` — Same as `token` but avoids the IPython/SystemExit noise by invoking the script in a quieter way.

Both targets run `scripts/create_api_token.py` inside `invenio shell` and include a macOS-friendly fallback for `DYLD_FALLBACK_LIBRARY_PATH` if Cairo dylibs are installed via Homebrew.

## Prerequisites
- A working Python virtual environment for this project (e.g., `.venv`) and the Invenio CLI installed inside it.
  - Example: `source .venv/bin/activate`
- The application must be importable by `invenio shell` or expose a factory `invenio_app.factory.create_app()` so the script can obtain an app context.
- An admin user must already exist (default email used by the script is `admin@turath.com`).
- macOS users with Homebrew-installed Cairo: the Makefile auto-sets `DYLD_FALLBACK_LIBRARY_PATH` to `$(brew --prefix)/lib` when needed.

## Optional environment variables
- `RDM_ADMIN_EMAIL` — Email of the admin user to create the token for (default: `admin@turath.com`).
- `RDM_TOKEN_SCOPES` — OAuth scopes for the token (default: `deposit:write deposit:actions`).

## Usage
1) Activate your virtual environment
```bash
source .venv/bin/activate
```

2) Generate a token and write it to `.env`
```bash
make token
```
What happens:
- Runs `scripts/create_api_token.py` inside `invenio shell`.
- Creates a personal token for the admin user.
- Prints the token to stdout.
- Updates or inserts `RDM_API_TOKEN=<token>` in `.env`.
- Backs up the previous `.env` to `.env.bak-YYYYmmddHHMMSS` if it existed.

3) Quieter variant (suppresses IPython/SystemExit messages)
```bash
make token-silent
```
Same behavior as `make token`, just fewer shell messages.

## Expected output and files changed
- Console output includes the newly created token and a message about updating `.env`.
- A backup file like `.env.bak-20250816175118` may be created next to `.env`.

## Troubleshooting
- "[ERROR] No Flask app context":
  - Ensure you run inside the project with a valid application context.
  - Try: `.venv/bin/invenio shell -c "exec(open('scripts/create_api_token.py').read())"` directly, or expose `invenio_app.factory.create_app()`.

- "User with email ... not found":
  - Create the admin user first (e.g., via your app’s user creation flow or a dedicated script), then re-run `make token`.

- macOS dylib errors (Cairo):
  - The Makefile sets `DYLD_FALLBACK_LIBRARY_PATH` from Homebrew automatically. If you still see dylib load errors, set it manually before running:
    ```bash
    export DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib"
    make token
    ```

## Where the logic lives
- Makefile targets: `Makefile`
- Token creation and `.env` update logic: `scripts/create_api_token.py`
