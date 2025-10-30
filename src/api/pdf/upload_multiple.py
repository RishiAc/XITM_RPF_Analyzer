import requests
from pathlib import Path

API_URL = "http://localhost:8080/chunk/upload-pdf"

# not finished ts does NOT work

def upload_pdf_with_variations(
    file_path: str,
    base_doc_id: str,
    chunk_sizes=None,
    overlaps=None
):
    """
    Uploads the same PDF to /chunk/upload-pdf for multiple
    (chunk_size, overlap) combinations.

    Parameters:
        file_path (str): Path to the PDF to upload
        base_doc_id (str): Base document name to use in uploads
        chunk_sizes (list[int]): List of chunk sizes to test
        overlaps (list[int]): List of chunk overlaps to test
    """

    # Default test configs
    if chunk_sizes is None:
        chunk_sizes = [256, 512, 1024]
    if overlaps is None:
        overlaps = [50, 100]

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    results = {}

    for size in chunk_sizes:
        for overlap in overlaps:
            print(f"\n🔹 Uploading with chunk_size={size}, overlap={overlap}...")

            # Give each config a unique doc_id
            doc_id = f"{base_doc_id}_s{size}_o{overlap}"

            # NOTE: since your API doesn’t accept chunkSize/overlap directly,
            # we’ll include them as query params (FastAPI can read them if added later)
            params = {
                "chunkSize": size,
                "chunkOverlap": overlap
            }

            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "application/pdf")}
                data = {"doc_id": doc_id}

                response = requests.post(API_URL, files=files, data=data, params=params)

            if response.status_code == 200:
                print(f"✅ Success for {doc_id}")
                results[doc_id] = response.json()
            else:
                print(f"❌ Failed for {doc_id} ({response.status_code})")
                print(response.text)
                results[doc_id] = {"error": response.text}

    return results


if __name__ == "__main__":
    results = upload_pdf_with_variations(
        file_path=r"C:\Users\mcyoo\Desktop\XITM\XITM_RPF_Analyzer\docs\rfps\2-RFP 2000004198.pdf",
        base_doc_id="Fairfax_RFP_Test",
        chunk_sizes=[256, 512, 1024],
        overlaps=[50, 75, 100]
    )

    print("\nAll results received:")
    for doc_id, result in results.items():
        print(f"{doc_id}: {'OK' if 'error' not in result else 'FAILED'}")
