const BASE_URL = process.env.REACT_APP_STAGING_BACKEND_URL || "http://localhost:8080";

export async function getAuthUrl() {
    const res = await fetch(`${BASE_URL}/gdrive/auth-url`);
    if (!res.ok) throw new Error("Failed to get auth URL");
    const data = await res.json();
    return data.auth_url;
}

export async function getStatus() {
    const res = await fetch(`${BASE_URL}/gdrive/status`);
    if (!res.ok) return false;
    const data = await res.json();
    return !!data.connected;
}

export async function syncFolder(folderId) {
    const res = await fetch(`${BASE_URL}/gdrive/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_id: folderId }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Sync failed");
    }
    return res.json();
}
