"""
Google Drive API integration for company knowledge base sync.
OAuth flow, list folder files, download PDF/DOCX, parse, chunk, ingest to Qdrant.
"""
import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from pydantic import BaseModel

from .pdf.parser import parse, chunks_to_json
from .vector_api import IngestBody, ingest_chunks, compute_evidence_for_all_queries

router = APIRouter(prefix="/gdrive", tags=["gdrive"])

# OAuth scopes for Drive read access
SCOPES = ["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/drive.metadata.readonly"]

# In-memory token storage (plan: "stores refresh_token in memory/env")
_gdrive_credentials: Optional[Credentials] = None

# Store Flow by state for PKCE - code_verifier must match between auth-url and callback
_pending_flows: dict[str, Flow] = {}

# Supported MIME types for parsing
PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
GOOGLE_DOCS_MIME = "application/vnd.google-apps.document"


def _get_flow() -> Flow:
    """Build OAuth flow from env client_id/client_secret."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment",
        )
    base_url = os.getenv("API_BASE_URL", "http://localhost:8080")
    redirect_uri = f"{base_url.rstrip('/')}/gdrive/callback"
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    return Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=redirect_uri)


def _get_credentials() -> Credentials:
    """Return stored credentials or raise if not connected."""
    from google.auth.transport.requests import Request

    global _gdrive_credentials
    if _gdrive_credentials is None:
        raise HTTPException(status_code=401, detail="Google Drive not connected. Call /gdrive/auth-url first.")
    if _gdrive_credentials.expired and _gdrive_credentials.refresh_token:
        _gdrive_credentials.refresh(Request())
    return _gdrive_credentials


class SyncBody(BaseModel):
    folder_id: str


@router.get("/auth-url")
def get_auth_url():
    """
    Returns the Google OAuth URL for the user to authorize.
    Frontend should open this URL in a popup or redirect the user.
    Stores Flow by state so callback can exchange code with same code_verifier (PKCE).
    """
    try:
        flow = _get_flow()
        auth_url, state = flow.authorization_url(prompt="consent", access_type="offline")
        _pending_flows[state] = flow
        return {"auth_url": auth_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build auth URL: {e}")


@router.get("/callback")
def oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """
    OAuth callback. Exchanges code for tokens and stores refresh_token.
    Uses the Flow stored at auth-url (by state) so code_verifier matches for PKCE.
    """
    global _gdrive_credentials
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' in callback")
    if not state or state not in _pending_flows:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state. Please try connecting again.",
        )

    try:
        flow = _pending_flows.pop(state)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        _gdrive_credentials = credentials
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url.rstrip('/')}/knowledge", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code: {e}")


@router.get("/status")
def gdrive_status():
    """Check if Google Drive is connected."""
    try:
        _get_credentials()
        return {"connected": True}
    except HTTPException:
        return {"connected": False}


def _list_files_in_folder(service, folder_id: str):
    """List PDF and DOCX (and Google Docs) in folder. Recurse into subfolders optional - plan says folder."""
    query = f"'{folder_id}' in parents"
    # Include PDF, DOCX, Google Docs
    mime_query = "(mimeType='application/pdf' or mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document' or mimeType='application/vnd.google-apps.document')"
    full_query = f"{query} and {mime_query}"
    results = []
    page_token = None
    while True:
        resp = service.files().list(
            q=full_query,
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token,
        ).execute()
        results.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return results


def _download_file(service, file_id: str, mime_type: str, name: str, temp_dir: Path) -> Optional[Path]:
    """Download file to temp path. Returns path or None on failure."""
    try:
        if mime_type == GOOGLE_DOCS_MIME:
            # Export Google Docs as PDF
            content = service.files().export(fileId=file_id, mimeType=PDF_MIME).execute()
            ext = ".pdf"
        elif mime_type in (PDF_MIME, DOCX_MIME):
            content = service.files().get_media(fileId=file_id).execute()
            ext = ".pdf" if mime_type == PDF_MIME else ".docx"
        else:
            return None

        # Use sanitized filename
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
        if not safe_name:
            safe_name = file_id
        path = temp_dir / f"{safe_name}{ext}"
        path.write_bytes(content)
        return path
    except Exception:
        return None


@router.post("/sync")
def sync_folder(body: SyncBody):
    """
    1. List files in folder
    2. Download each PDF/DOCX
    3. Parse + chunk using parser.py logic
    4. Ingest to Qdrant with doc_type="company"
    5. Run compute_evidence() for ALL queries
    Returns: { files_processed: N, chunks_created: M }
    """
    creds = _get_credentials()
    service = build("drive", "v3", credentials=creds)

    files = _list_files_in_folder(service, body.folder_id)
    files_processed = 0
    chunks_created = 0
    processed_names: list[str] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        for f in files:
            fid = f["id"]
            name = f.get("name", "unknown")
            mime = f.get("mimeType", "")
            local_path = _download_file(service, fid, mime, name, temp_path)
            if local_path is None:
                continue
            try:
                nodes = parse(str(local_path))
                doc_id = f"gdrive:{fid}"
                json_chunks = chunks_to_json(doc_id, nodes)["chunks"]
                if not json_chunks:
                    continue
                ingest_body = IngestBody(doc_id=doc_id, chunks=json_chunks, doc_type="company")
                result = ingest_chunks(ingest_body)
                files_processed += 1
                chunks_created += result.get("ingested", len(json_chunks))
                processed_names.append(name)
            except Exception:
                continue

    # Recompute evidence for all queries
    compute_evidence_for_all_queries()

    return {
        "files_processed": files_processed,
        "chunks_created": chunks_created,
        "files": processed_names,
    }
