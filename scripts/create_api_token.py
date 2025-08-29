#!/usr/bin/env python3
"""
Create a personal API token for the admin user and update RDM_API_TOKEN in .env.

Usage options:
- Preferred (guarantees app context):
  .venv/bin/invenio shell -c "exec(open('scripts/create_api_token.py').read())"

- If your project exposes a factory at invenio_app.factory.create_app(), you can also run:
  .venv/bin/python scripts/create_api_token.py

The script will:
- Create a Client and a bearer Token for email=admin@turath.com
- Print the token to stdout
- Update/insert RDM_API_TOKEN in .env (backing up to .env.bak-YYYYmmddHHMMSS)
"""
import os
import re
import sys
import time
from datetime import datetime

from werkzeug.security import gen_salt

# Lazy imports inside functions to allow running both in and out of app context

def _has_app_context() -> bool:
    try:
        from flask import has_app_context
        return has_app_context()
    except Exception:
        return False


def _ensure_app_context():
    """Ensure we have a Flask app context. Try factory fallback if needed.

    Returns True if an app context is available (or created), else False.
    """
    if _has_app_context():
        return True
    # Try a factory commonly used by InvenioRDM apps
    try:
        from invenio_app.factory import create_app  # type: ignore
        app = create_app()
        app.app_context().push()
        return True
    except Exception:
        return False


EMAIL = os.environ.get("RDM_ADMIN_EMAIL", "admin@turath.com")
SCOPES = os.environ.get("RDM_TOKEN_SCOPES", "deposit:write deposit:actions")
TOKEN_NAME = f"API Token {datetime.now().strftime('%Y-%m-%d')}"


def create_api_token(email: str, scopes: str) -> str | None:
    """Create a personal API token for the given user email.

    Returns the access token string or None on failure.
    """
    from invenio_db import db
    from invenio_accounts.models import User
    from invenio_oauth2server.models import Client, Token

    # Find user
    user = User.query.filter_by(email=email).first()
    if not user:
        print(f"[ERROR] User with email {email} not found. Create the admin user first.")
        return None

    client = Client(
        client_id=gen_salt(40),
        client_secret=gen_salt(60),
        name=TOKEN_NAME,
        description=f"Personal API token for {email}",
        user_id=user.id,
        is_confidential=False,
        is_internal=True,
        _default_scopes=scopes,
    )

    token = Token(
        client_id=client.client_id,
        user_id=user.id,
        token_type="bearer",
        access_token=gen_salt(100),
        refresh_token=None,
        expires=None,
        _scopes=scopes,
        is_personal=True,
        is_internal=False,
    )

    try:
        db.session.add(client)
        db.session.add(token)
        db.session.commit()
    except Exception as e:
        from invenio_db import db as _db
        _db.session.rollback()
        print(f"[ERROR] Failed to create token: {e}")
        return None

    print(f"Token created successfully for {email}")
    print(f"Token name: {TOKEN_NAME}")
    print(f"Scopes: {scopes}")
    print("No expiration date")

    return token.access_token


def _backup_env(env_path: str) -> str | None:
    if not os.path.exists(env_path):
        return None
    ts = time.strftime("%Y%m%d%H%M%S")
    backup_path = f"{env_path}.bak-{ts}"
    try:
        with open(env_path, "rb") as rf, open(backup_path, "wb") as wf:
            wf.write(rf.read())
        return backup_path
    except Exception as e:
        print(f"[WARN] Could not backup {env_path}: {e}")
        return None


def update_env_token(token: str, project_root: str = ".") -> None:
    env_path = os.path.join(project_root, ".env")
    backup = _backup_env(env_path)

    new_line = f"RDM_API_TOKEN={token}\n"

    try:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                content = f.read()
            if "RDM_API_TOKEN=" in content:
                content = re.sub(r"^RDM_API_TOKEN=.*$", new_line.strip(), content, flags=re.M)
            else:
                if not content.endswith("\n"):
                    content += "\n"
                content += new_line
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(new_line)
        msg = "Updated .env with new token."
        if backup:
            msg += f" Backup saved to {backup}."
        print(msg)
    except Exception as e:
        print(f"[ERROR] Failed to update .env: {e}")


def main() -> int:
    # Ensure we are at project root (script is in scripts/). When run via
    # `invenio shell -c "exec(open(...).read())"`, __file__ is not defined;
    # in that case, use the current working directory as project root.
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
    except NameError:
        project_root = os.getcwd()
    os.chdir(project_root)

    if not _ensure_app_context():
        print("[ERROR] No Flask app context. Run via 'invenio shell' or expose a create_app() factory.")
        print("Example: .venv/bin/invenio shell -c \"exec(open('scripts/create_api_token.py').read())\"")
        return 2

    token = create_api_token(EMAIL, SCOPES)
    if not token:
        return 1

    print("\nYour API token:")
    print(token)

    update_env_token(token, project_root)
    print("\n==== Complete! ====")
    print("A new API token has been generated and saved to your .env file as RDM_API_TOKEN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
