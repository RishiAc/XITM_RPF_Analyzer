# Cloud Run + Vercel Deployment Guide

This guide deploys:

- Backend (`FastAPI`) on **Google Cloud Run**
- Frontend (`React`) on **Vercel**
- External services: **Supabase**, **Qdrant**, **OpenAI**, **Google Drive OAuth**

## 1) Prerequisites

- GCP project with billing enabled
- `gcloud` CLI configured and authenticated
- Docker installed locally
- Vercel project connected to this repo
- New Supabase project
- New Qdrant cluster
- Google OAuth app credentials

## 2) Configure backend code runtime behavior

Backend now supports production CORS env variables:

- `CORS_ALLOWED_ORIGINS` (comma-separated list)
- `CORS_ALLOWED_ORIGIN_REGEX` (optional)

Health route:

- `GET /health`

## 3) Deploy backend container to Cloud Run

From repo root:

```bash
chmod +x deployment/cloudrun/deploy_backend.sh
PROJECT_ID=your-gcp-project \
REGION=us-central1 \
SERVICE_NAME=xitm-rfp-api \
REPOSITORY=xitm-artifacts \
IMAGE_NAME=xitm-rfp-api \
FRONTEND_URL=https://your-frontend.vercel.app \
./deployment/cloudrun/deploy_backend.sh
```

After deployment, capture the Cloud Run URL (for example `https://xitm-rfp-api-xyz.a.run.app`).

## 4) Create and wire GCP secrets

Create/update all required secrets:

```bash
printf '%s' 'your-value' | gcloud secrets create QDRANT_URL --data-file=- --replication-policy=automatic
printf '%s' 'your-value' | gcloud secrets create QDRANT_API_KEY --data-file=- --replication-policy=automatic
printf '%s' 'your-value' | gcloud secrets create SUPABASE_URL --data-file=- --replication-policy=automatic
printf '%s' 'your-value' | gcloud secrets create SUPABASE_SERVICE_ROLE_KEY --data-file=- --replication-policy=automatic
printf '%s' 'your-value' | gcloud secrets create OPENAI_API_KEY --data-file=- --replication-policy=automatic
printf '%s' 'your-value' | gcloud secrets create GOOGLE_CLIENT_ID --data-file=- --replication-policy=automatic
printf '%s' 'your-value' | gcloud secrets create GOOGLE_CLIENT_SECRET --data-file=- --replication-policy=automatic
printf '%s' 'your-value' | gcloud secrets create LLAMA_PARSE_KEY --data-file=- --replication-policy=automatic
```

If a secret already exists, use:

```bash
printf '%s' 'new-value' | gcloud secrets versions add SECRET_NAME --data-file=-
```

Grant Cloud Run runtime service account access to secrets:

```bash
PROJECT_NUMBER="$(gcloud projects describe your-gcp-project --format='value(projectNumber)')"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for SECRET in QDRANT_URL QDRANT_API_KEY SUPABASE_URL SUPABASE_SERVICE_ROLE_KEY OPENAI_API_KEY GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET LLAMA_PARSE_KEY; do
  gcloud secrets add-iam-policy-binding "$SECRET" \
    --member="serviceAccount:${RUNTIME_SA}" \
    --role="roles/secretmanager.secretAccessor"
done
```

Apply runtime env + secret references:

```bash
chmod +x deployment/cloudrun/configure_runtime.sh
PROJECT_ID=your-gcp-project \
REGION=us-central1 \
SERVICE_NAME=xitm-rfp-api \
API_BASE_URL=https://your-cloud-run-service-url \
FRONTEND_URL=https://your-frontend.vercel.app \
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://your-custom-domain \
./deployment/cloudrun/configure_runtime.sh
```

## 5) Configure Supabase

1. Create a new Supabase project.
2. Apply SQL migrations from `supabase/migrations`.
3. In Supabase Auth settings:
   - **Site URL**: `https://your-frontend.vercel.app`
   - **Redirect URLs**: include `https://your-frontend.vercel.app/login`
4. Collect:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY` (backend secret)
   - `SUPABASE_ANON_KEY` (frontend env var)

## 6) Configure Qdrant

1. Create a new Qdrant cluster and API key.
2. Set `QDRANT_URL` and `QDRANT_API_KEY` in GCP secrets.
3. Keep `QDRANT_COLLECTION=rfp_chunks` unless you want a custom collection name.

## 7) Configure Google OAuth for Drive sync

In Google Cloud Console OAuth credentials:

- Authorized redirect URI:
  - `https://your-cloud-run-service-url/gdrive/callback`
- Authorized origins (if used by your flow):
  - `https://your-frontend.vercel.app`

Cloud Run runtime vars used by this flow:

- `API_BASE_URL=https://your-cloud-run-service-url`
- `FRONTEND_URL=https://your-frontend.vercel.app`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`

## 8) Deploy frontend on Vercel

Set project root to:

- `src/frontend`

Set Vercel environment variables (Production + Preview as needed):

- `REACT_APP_API_URL=https://your-cloud-run-service-url`
- `REACT_APP_SUPABASE_URL=...`
- `REACT_APP_SUPABASE_ANON_KEY=...`
- `REACT_APP_ALLOWED_DOMAIN=yourcompany.com` (or use explicit approved list)
- `REACT_APP_APPROVED_EMAILS=user1@yourcompany.com,user2@yourcompany.com`
- `REACT_APP_ADMIN_EMAILS=admin1@yourcompany.com`
- `REACT_APP_OTP_EXPIRY_MIN=5`

SPA routing fallback is handled by `src/frontend/vercel.json`.

## 9) Validation checklist

Run these checks after both deployments:

1. Backend health:
   - `GET https://your-cloud-run-service-url/health` returns `{ "ok": true }`
2. Auth:
   - Signup only allowed emails
   - Login redirects to protected routes
3. Upload:
   - Upload a PDF and confirm chunk ingestion succeeds
4. Chat:
   - Query an RFP and verify answer + sources
5. Analysis:
   - Run analysis and verify phase scores populate
6. Knowledge Base:
   - CRUD query rows and see updates reflected
7. Google Drive:
   - Connect account, sync folder URL/ID, verify completion
8. Data:
   - Supabase writes present in expected tables
   - Qdrant vectors present and searchable

## 10) Security checklist (go-live)

- Store all secrets in GCP Secret Manager (never commit secrets)
- Rotate any keys previously exposed in terminal history/logs
- Keep CORS restricted to exact production domains
- Keep Cloud Run HTTPS only (default)
- Review Cloud Run IAM (`--allow-unauthenticated` only if intended)
- Enable Cloud Logging alerts for 4xx/5xx spikes
- Set budget alerts in GCP and usage alerts for OpenAI/Qdrant
