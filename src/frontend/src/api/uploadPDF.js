// src/api/uploadPDF.js
import { client } from "./client.js";

/**
 * Upload a PDF and send it to FastAPI for Supabase + Qdrant processing
 * @param {File} file - PDF file
 */

export async function uploadPDF(file) {
  if (!file) throw new Error("No file provided");

  try {
    const formData = new FormData();
    formData.append("file", file);

    console.log("client.apiBaseUrl", client.apiBaseUrl);

    const response = await fetch(`${client.apiBaseUrl}/chunk/upload-pdf`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Upload failed: ${response.status} ${errText}`);
    }

    // ✅ Parse JSON result from FastAPI (this is your "result" dict)
    const result = await response.json();

    return result;

  } catch (err) {
    console.error("Error uploading PDF:", err);
    throw err;
  }
}
