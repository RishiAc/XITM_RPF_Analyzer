import vector_api

ingest_body = vector_api.IngestBody(doc_id="TestDoc1", chunks=["Proposal due 9/12/2026", "work requires 100 people", "This RFP is offered by company"])

print(vector_api.ingest_chunks(ingest_body))

search_body = vector_api.SearchBody(doc_id="TestDoc1", query="Important contract information", top_k=3)

print(vector_api.search(search_body))
