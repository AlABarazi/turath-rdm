# Dockerfile that builds a fully functional image of your app.
#
# This image installs all Python dependencies for your application. It's based
# on Almalinux (https://github.com/inveniosoftware/docker-invenio)
# and includes Pip, Pipenv, Node.js, NPM and some few standard libraries
# Invenio usually needs.
#
# Note: It is important to keep the commands in this file in sync with your
# bootstrap script located in ./scripts/bootstrap.

FROM registry.cern.ch/inveniosoftware/almalinux:1

COPY site ./site
COPY Pipfile Pipfile.lock ./
RUN pipenv lock --clear && pipenv install --system

# Patch invenio_communities migration to align group_id type with accounts_role.id (string)
# This avoids a FK type mismatch during Alembic migrations when using accounts 6.x.
RUN python - <<'PY'
import io
import sys
from pathlib import Path

p = Path('/usr/local/lib/python3.9/site-packages/invenio_communities/alembic/fbe746957cfc_create_member_tables.py')
src = p.read_text(encoding='utf-8')
patched = src

# Change communities_members.group_id from Integer to String
patched = patched.replace(
    'sa.Column("group_id", sa.Integer(), nullable=True)',
    'sa.Column("group_id", sa.String(), nullable=True)'
)

# Change communities_archivedinvitations.group_id from Integer to String
patched = patched.replace(
    'sa.Column("group_id", sa.Integer(), nullable=True),',
    'sa.Column("group_id", sa.String(), nullable=True),'
)

if patched != src:
    p.write_text(patched, encoding='utf-8')
    print(f"Patched {p}")
else:
    print(f"No changes applied to {p} (already patched or unexpected format)")
PY

# Patch follow-up migration to avoid duplicate FK creation when constraints already exist
RUN python - <<'PY'
from pathlib import Path

pf = Path('/usr/local/lib/python3.9/site-packages/invenio_communities/alembic/02cd82910727_update_role_id_type_upgrade.py')
src = pf.read_text(encoding='utf-8')

# Replace op.create_foreign_key blocks with conditional DO blocks executed via op.execute
replacement_arch = (
    'op.execute(\n'
    "    \"\"\"\n"
    "    DO $$\n"
    "    BEGIN\n"
    "      IF NOT EXISTS (\n"
    "        SELECT 1 FROM pg_constraint c\n"
    "        JOIN pg_class t ON c.conrelid = t.oid\n"
    "        WHERE c.conname = 'fk_communities_archivedinvitations_group_id_accounts_role'\n"
    "      ) THEN\n"
    "        ALTER TABLE communities_archivedinvitations\n"
    "        ADD CONSTRAINT fk_communities_archivedinvitations_group_id_accounts_role\n"
    "        FOREIGN KEY (group_id) REFERENCES accounts_role(id) ON DELETE RESTRICT;\n"
    "      END IF;\n"
    "    END\n"
    "    $$;\n"
    "    \"\"\"\n"
    ')\n'
)

replacement_members = (
    'op.execute(\n'
    "    \"\"\"\n"
    "    DO $$\n"
    "    BEGIN\n"
    "      IF NOT EXISTS (\n"
    "        SELECT 1 FROM pg_constraint c\n"
    "        JOIN pg_class t ON c.conrelid = t.oid\n"
    "        WHERE c.conname = 'fk_communities_members_group_id_accounts_role'\n"
    "      ) THEN\n"
    "        ALTER TABLE communities_members\n"
    "        ADD CONSTRAINT fk_communities_members_group_id_accounts_role\n"
    "        FOREIGN KEY (group_id) REFERENCES accounts_role(id) ON DELETE RESTRICT;\n"
    "      END IF;\n"
    "    END\n"
    "    $$;\n"
    "    \"\"\"\n"
    ')\n'
)

patched = src
patched = patched.replace(
    "op.create_foreign_key(\n        op.f(\"fk_communities_archivedinvitations_group_id_accounts_role\"),\n        \"communities_archivedinvitations\",\n        \"accounts_role\",\n        [\"group_id\"],\n        [\"id\"],\n        ondelete=\"RESTRICT\",\n    )\n",
    replacement_arch,
)
patched = patched.replace(
    "op.create_foreign_key(\n        op.f(\"fk_communities_members_group_id_accounts_role\"),\n        \"communities_members\",\n        \"accounts_role\",\n        [\"group_id\"],\n        [\"id\"],\n        ondelete=\"RESTRICT\",\n    )\n",
    replacement_members,
)

if patched != src:
    pf.write_text(patched, encoding='utf-8')
    print(f"Patched {pf}")
else:
    print(f"No changes applied to {pf} (already patched or unexpected format)")
PY

COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations/ ${INVENIO_INSTANCE_PATH}/translations/
COPY ./ .

RUN cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose  && \
    invenio webpack buildall

ENTRYPOINT [ "bash", "-c"]