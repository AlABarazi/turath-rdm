#!/bin/bash
# Resolve the INVENIO_SQLALCHEMY_DATABASE_URI dynamically from
# AWS Secrets Manager so the container always uses the current
# RDS password — even after automatic rotations.
#
# Required env vars (set in ECS task definition):
#   RDS_SECRET_ARN  – ARN of the RDS-managed Secrets Manager secret
#   RDS_DB_HOST     – RDS endpoint (without port)
#   RDS_DB_USER     – database user  (default: inveniordm_user)
#   RDS_DB_NAME     – database name  (default: inveniordm_db)
#   RDS_DB_PORT     – database port  (default: 5432)
#
# After resolving, this script exports INVENIO_SQLALCHEMY_DATABASE_URI
# and exec's whatever command was passed as arguments (e.g. uwsgi).

set -e

if [ -z "$RDS_SECRET_ARN" ]; then
  echo "[resolve-db-uri] RDS_SECRET_ARN not set — falling back to existing INVENIO_SQLALCHEMY_DATABASE_URI"
  exec "$@"
fi

DB_HOST="${RDS_DB_HOST:?RDS_DB_HOST is required}"
DB_USER="${RDS_DB_USER:-inveniordm_user}"
DB_NAME="${RDS_DB_NAME:-inveniordm_db}"
DB_PORT="${RDS_DB_PORT:-5432}"

echo "[resolve-db-uri] Fetching RDS password from Secrets Manager..."

ENCODED_PASSWORD=$(python3 -c "
import json, os, urllib.parse, boto3

client = boto3.client(
    'secretsmanager',
    region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
)
resp = client.get_secret_value(SecretId=os.environ['RDS_SECRET_ARN'])
password = json.loads(resp['SecretString'])['password']
print(urllib.parse.quote(password, safe=''))
")

export INVENIO_SQLALCHEMY_DATABASE_URI="postgresql://${DB_USER}:${ENCODED_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?sslmode=require"

echo "[resolve-db-uri] DB URI resolved successfully"

exec "$@"
