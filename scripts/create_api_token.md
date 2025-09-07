# Create Admin API Token

This guide explains how to run `scripts/create_api_token.py` to generate a personal API token for the admin user and save it to your `.env` as `RDM_API_TOKEN`.

## Prerequisites

- The app is installed and the database is initialized.
- Admin user exists and is active (use `scripts/create_admin.py` first).
- You are inside the project root (where `.venv/` and `.env` live).
- You can run `invenio` from the virtual environment.

## Recommended way (with Flask app context)

Run the script via Flask app context using `invenio shell`:

```bash
# If already inside your Pipenv/venv shell
invenio shell -c "exec(open('scripts/create_api_token.py').read())"

# Or, if you typically run via Pipenv
pipenv run invenio shell -c "exec(open('scripts/create_api_token.py').read())"
```

This ensures a valid Flask app context so the script can access the database and models.

## What the script does

- Creates an OAuth2 Client and a bearer Token for `email=admin@turath.com` (configurable).
- Prints the token to stdout.
- Updates or inserts `RDM_API_TOKEN=<token>` into your `.env`.
  - Creates a backup like `.env.bak-YYYYmmddHHMMSS` if `.env` exists.

## Configuration (optional)

The script reads the following environment variables:

- `RDM_ADMIN_EMAIL` (default: `admin@turath.com`)
- `RDM_TOKEN_SCOPES` (default: `deposit:write deposit:actions`)

Example:

```bash
export RDM_ADMIN_EMAIL="admin@turath.com"
export RDM_TOKEN_SCOPES="deposit:write deposit:actions"
# then run the script as shown above
```

## Example output

```
Token created successfully for admin@turath.com
Token name: API Token 2025-09-01
Scopes: deposit:write deposit:actions
No expiration date

Your API token:
<PASTE_THIS_TOKEN>

Updated .env with new token. Backup saved to .env.bak-20250901125900.
==== Complete! ====
A new API token has been generated and saved to your .env file as RDM_API_TOKEN.
```

## Troubleshooting

- "[ERROR] No Flask app context": You executed the script directly. Re-run using:
  ```bash
  invenio shell -c "exec(open('scripts/create_api_token.py').read())"
  ```
- Tip about `.env` and `python-dotenv`: optional. To silence:
  ```bash
  pipenv run pip install python-dotenv
  ```
- If user not found: run `scripts/create_admin.py` first to create/activate the admin user and assign roles.

## Alternative (only if your app exposes a factory)

If your project exposes `invenio_app.factory.create_app()`, you can run directly:

```bash
.venv/bin/python scripts/create_api_token.py
```

If this fails with app context errors, use the recommended `invenio shell` method above.
