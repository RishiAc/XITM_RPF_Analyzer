import vectorApi

ingest_body = vectorApi.IngestBody(doc_id="TestDoc1", chunks=["Proposal due 9/12/2026", "work requires 100 people", "This RFP is offered by company"])

print(vectorApi.ingest_chunks(ingest_body))

search_body = vectorApi.SearchBody(doc_id="TestDoc1", query="Important contract information", top_k=3)

print(vectorApi.search(search_body))
