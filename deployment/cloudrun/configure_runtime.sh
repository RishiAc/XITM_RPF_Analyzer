#!/usr/bin/env bash
set -euo pipefail

# Usage:
# PROJECT_ID=your-gcp-project \
# REGION=us-central1 \
# SERVICE_NAME=xitm-rfp-api \
# FRONTEND_URL=https://your-frontend.vercel.app \
# API_BASE_URL=https://your-cloud-run-url \
# CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://your-custom-domain \
# ./deployment/cloudrun/configure_runtime.sh

PROJECT_ID="${PROJECT_ID:?PROJECT_ID is required}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-xitm-rfp-api}"

echo "==> Updating non-secret env vars"
gcloud run services update "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --set-env-vars "API_BASE_URL=${API_BASE_URL:?API_BASE_URL is required}" \
  --set-env-vars "FRONTEND_URL=${FRONTEND_URL:?FRONTEND_URL is required}" \
  --set-env-vars "CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS:?CORS_ALLOWED_ORIGINS is required}" \
  --set-env-vars "QDRANT_COLLECTION=${QDRANT_COLLECTION:-rfp_chunks}" \
  --set-env-vars "EMBED_MODEL=${EMBED_MODEL:-sentence-transformers/all-MiniLM-L6-v2}"

echo "==> Updating secret references from Secret Manager"
gcloud run services update "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --set-secrets "QDRANT_URL=QDRANT_URL:latest" \
  --set-secrets "QDRANT_API_KEY=QDRANT_API_KEY:latest" \
  --set-secrets "SUPABASE_URL=SUPABASE_URL:latest" \
  --set-secrets "SUPABASE_SERVICE_ROLE_KEY=SUPABASE_SERVICE_ROLE_KEY:latest" \
  --set-secrets "OPENAI_API_KEY=OPENAI_API_KEY:latest" \
  --set-secrets "GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest" \
  --set-secrets "GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest" \
  --set-secrets "LLAMA_PARSE_KEY=LLAMA_PARSE_KEY:latest"

echo "==> Runtime configuration complete"
echo "Tip: create/update secrets with:"
echo "  printf '%s' 'value' | gcloud secrets versions add SECRET_NAME --data-file=- --project ${PROJECT_ID}"
