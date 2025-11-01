import json
import requests
import difflib
from typing import Dict, Any

API_URL = "http://localhost:8080"
SEARCH_ENDPOINT = f"{API_URL}/vector/search"


def load_test_data(path: str) -> Dict[str, Any]:
    """Load JSON with ideal chunks and queries."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def text_similarity(a: str, b: str) -> float:
    """Simple similarity metric between two chunks (0-1)."""
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def run_search(doc_id: str, query: str, top_k: int = 10):
    payload = {"doc_id": doc_id, "query": query, "top_k": top_k}
    resp = requests.post(SEARCH_ENDPOINT, json=payload)
    if not resp.ok:
        raise RuntimeError(f"Search failed: {resp.status_code} {resp.text}")
    return resp.json()["results"]


def check_accuracy_for_doc(doc_id: str, test_data: Dict[str, Any], top_k: int = 20):
    """
    Run queries from the test data against a single manually uploaded doc_id.
    """
    total_queries = 0
    correct_matches = 0

    chunks = test_data.get("chunks", [])
    if not chunks:
        raise ValueError("No 'chunks' found in test data file.")

    print(f"\n=== Testing document: {doc_id} ===")

    for chunk in chunks:
        ideal_text = chunk["chunk_text"]
        for query in chunk.get("queries", []):
            total_queries += 1
            results = run_search(doc_id, query, top_k=top_k)

            found = False
            matched_chunk = None
            highest_score = 0.0

            # Check each top-K result
            for r in results:
                sim = text_similarity(r["text"], ideal_text)
                if sim > highest_score:
                    highest_score = sim
                    matched_chunk = r["text"]
                if sim > 0.7:
                    found = True 

            # print(f"[{'✅' if found else '❌'}] Query: {query}")
            print(f"Query: {query}")
            if matched_chunk:
                # print(f"   ↳ Best matching chunk (score {highest_score:.2f}): {matched_chunk}")
                print(f"   ↳ Best matching chunk: {matched_chunk}\n")

            correct_matches += int(found)


    accuracy = correct_matches / total_queries if total_queries else 0
    # print(f"\n=== Summary for {doc_id} ===")
    # print(f"Total queries: {total_queries}")
    # print(f"Correct matches: {correct_matches}")
    # print(f"Accuracy: {accuracy:.2%}")


def main():
    # Path to your JSON file containing ideal chunks and queries
    test_file = r"C:\Users\mcyoo\Desktop\XITM\XITM_RPF_Analyzer\src\api\pdf\rpf_ideal_chunks.json"
    test_data = load_test_data(test_file)

    # Ask user to input the doc_id of the PDF they manually uploaded
    doc_id = input("Enter the doc_id of the manually uploaded PDF: ").strip()
    if not doc_id:
        print("Error: doc_id cannot be empty")
        return

    print("🚀 Starting accuracy evaluation...")
    check_accuracy_for_doc(doc_id, test_data)


if __name__ == "__main__":
    main()
