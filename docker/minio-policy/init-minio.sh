#!/bin/sh
set -eu

ROOT_USER="$(cat /run/secrets/minio_root_user)"
ROOT_PASSWORD="$(cat /run/secrets/minio_root_password)"
BACKEND_ACCESS_KEY="$(cat /run/secrets/minio_backend_access_key)"
BACKEND_SECRET_KEY="$(cat /run/secrets/minio_backend_secret_key)"
AI_ACCESS_KEY="$(cat /run/secrets/minio_ai_access_key)"
AI_SECRET_KEY="$(cat /run/secrets/minio_ai_secret_key)"

until mc alias set local http://minio:9000 "$ROOT_USER" "$ROOT_PASSWORD"; do
  sleep 2
done

mc mb --ignore-existing local/documents
mc anonymous set none local/documents
mc mb --ignore-existing local/extraction
mc anonymous set none local/extraction

mc admin policy create local documents-backend-policy /tmp/documents-backend-policy.json || true
mc admin policy create local documents-ai-reader-policy /tmp/documents-ai-reader-policy.json || true
mc admin user add local "$BACKEND_ACCESS_KEY" "$BACKEND_SECRET_KEY" || true
mc admin user add local "$AI_ACCESS_KEY" "$AI_SECRET_KEY" || true
mc admin policy attach local documents-backend-policy --user "$BACKEND_ACCESS_KEY"
mc admin policy attach local documents-ai-reader-policy --user "$AI_ACCESS_KEY"
