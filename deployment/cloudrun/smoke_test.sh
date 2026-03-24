#!/usr/bin/env bash
set -euo pipefail

# Usage:
# API_URL=https://your-cloud-run-service-url \
# FRONTEND_URL=https://your-frontend.vercel.app \
# ./deployment/cloudrun/smoke_test.sh

API_URL="${API_URL:?API_URL is required}"
FRONTEND_URL="${FRONTEND_URL:?FRONTEND_URL is required}"

echo "==> Health check"
curl -fsS "${API_URL}/health" | sed 's/.*/health: &/'

echo "==> Vector health check"
curl -fsS "${API_URL}/vector/health" | sed 's/.*/vector_health: &/'

echo "==> CORS preflight check (Knowledge Base endpoint)"
curl -fsS -o /dev/null -D - \
  -X OPTIONS "${API_URL}/knowledge_base/get_all_query_rows" \
  -H "Origin: ${FRONTEND_URL}" \
  -H "Access-Control-Request-Method: GET" \
  | rg -i "access-control-allow-origin|access-control-allow-methods|HTTP/"

echo "==> Smoke test completed"
echo "Manual checks still required for login/signup, upload, analysis, and gdrive sync."
