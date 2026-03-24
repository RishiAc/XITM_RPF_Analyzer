#!/usr/bin/env bash
set -euo pipefail

# Usage:
# PROJECT_ID=your-gcp-project \
# REGION=us-central1 \
# SERVICE_NAME=xitm-rfp-api \
# REPOSITORY=xitm-artifacts \
# IMAGE_NAME=xitm-rfp-api \
# FRONTEND_URL=https://your-frontend.vercel.app \
# ./deployment/cloudrun/deploy_backend.sh

PROJECT_ID="${PROJECT_ID:?PROJECT_ID is required}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-xitm-rfp-api}"
REPOSITORY="${REPOSITORY:-xitm-artifacts}"
IMAGE_NAME="${IMAGE_NAME:-xitm-rfp-api}"

IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:$(date +%Y%m%d-%H%M%S)"

echo "==> Enabling required APIs"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  --project "${PROJECT_ID}"

echo "==> Ensuring Artifact Registry repository exists"
gcloud artifacts repositories create "${REPOSITORY}" \
  --repository-format=docker \
  --location="${REGION}" \
  --project="${PROJECT_ID}" \
  || true

echo "==> Configuring Docker auth"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "==> Building and pushing image: ${IMAGE_URI}"
docker build -t "${IMAGE_URI}" -f deployment/docker/dockerfile .
docker push "${IMAGE_URI}"

echo "==> Deploying Cloud Run service: ${SERVICE_NAME}"
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_URI}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --port 8080 \
  --cpu 2 \
  --memory 8Gi \
  --timeout 900 \
  --concurrency 20 \
  --min-instances 0 \
  --set-env-vars "FRONTEND_URL=${FRONTEND_URL:-https://example.vercel.app}" \
  --project "${PROJECT_ID}"

SERVICE_URL="$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format='value(status.url)')"

echo "==> Deployment complete"
echo "Service URL: ${SERVICE_URL}"
echo "Next: set runtime env vars and secrets, then update FRONTEND_URL/API_BASE_URL and CORS envs."
