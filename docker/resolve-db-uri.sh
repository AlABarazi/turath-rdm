#!/bin/bash
# Resolve the INVENIO_SQLALCHEMY_DATABASE_URI dynamically
# using RDS_DB_PASSWORD environment variable (manual password management)
# or falling back to RDS_SECRET_ARN (AWS-managed rotation - legacy).
#
# Required env vars (set in ECS task definition):
#   RDS_DB_PASSWORD – Database password (manual management)
#   OR
#   RDS_SECRET_ARN  – ARN of Secrets Manager secret (legacy)
#   
#   RDS_DB_HOST     – RDS endpoint (without port)
#   RDS_DB_USER     – database user  (default: inveniordm_user)
#   RDS_DB_NAME     – database name  (default: inveniordm_db)
#   RDS_DB_PORT     – database port  (default: 5432)

set -e

DB_HOST="${RDS_DB_HOST:?RDS_DB_HOST is required}"
DB_USER="${RDS_DB_USER:-inveniordm_user}"
DB_NAME="${RDS_DB_NAME:-inveniordm_db}"
DB_PORT="${RDS_DB_PORT:-5432}"

# Method 1: Direct password (preferred - manual management)
if [ -n "$RDS_DB_PASSWORD" ]; then
  echo "[resolve-db-uri] Using RDS_DB_PASSWORD (manual password management)"
  ENCODED_PASSWORD=$(python3 -c "
import urllib.parse, os
password = os.environ['RDS_DB_PASSWORD']
print(urllib.parse.quote(password, safe=''))
")

# Method 2: Secrets Manager (legacy - automatic rotation)
elif [ -n "$RDS_SECRET_ARN" ]; then
  echo "[resolve-db-uri] Using RDS_SECRET_ARN (legacy - fetching from Secrets Manager)"
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

# Method 3: Fallback to existing URI
else
  echo "[resolve-db-uri] No RDS_DB_PASSWORD or RDS_SECRET_ARN — falling back to existing INVENIO_SQLALCHEMY_DATABASE_URI"
  exec "$@"
fi

export INVENIO_SQLALCHEMY_DATABASE_URI="postgresql://${DB_USER}:${ENCODED_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?sslmode=require"

echo "[resolve-db-uri] DB URI resolved successfully"

exec "$@"
