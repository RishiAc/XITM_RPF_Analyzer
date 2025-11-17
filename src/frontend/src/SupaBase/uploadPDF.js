/**
 * Upload a PDF and send it to FastAPI for Supabase + Qdrant processing
 * @param {File} file - PDF file
 */
export async function uploadPDF(file) {
  if (!file) throw new Error("No file provided");
  const url = "http://localhost:8080/chunk/upload-pdf"; // <-- ensure 8080
  const fd = new FormData();
  fd.append("file", file);

  try {
    const res = await fetch(url, {
      method: "POST",
      body: fd, // do NOT set Content-Type
    });

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`Upload failed: ${res.status} ${res.statusText} - ${txt}`);
    }
    return await res.json();
  } catch (err) {
    console.error("uploadPDF error:", err);
    throw err;
  }
}
