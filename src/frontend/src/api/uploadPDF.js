/**
 * Upload a PDF and send it to FastAPI for Supabase + Qdrant processing
 * @param {File} file - PDF file
 */
import { client } from "./client.js";

export async function uploadPDF(file) {
  if (!file) throw new Error("No file provided");
  const url = "http://localhost:8080/chunk/upload-pdf"; // <-- ensure 8080
  const fd = new FormData();
  fd.append("file", file);

  try {
<<<<<<< HEAD:src/frontend/src/api/uploadPDF.js
    const formData = new FormData();
    formData.append("file", file);

    console.log("client.stagingBackendUrl", client.stagingBackendUrl);

    const response = await fetch(`http://localhost:8080/chunk/upload-pdf`, {
=======
    const res = await fetch(url, {
>>>>>>> 7eef9fe9320946e31e7c569b68eb48cee06258b9:src/frontend/src/SupaBase/uploadPDF.js
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
