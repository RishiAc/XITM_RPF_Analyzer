
### Put these in your .env located at the root of your repo: ###

QDRANT_API_KEY=
QDRANT_URL=https://b0a197c1-9124-4747-815f-8731febbdecd.us-east-1-1.aws.cloud.qdrant.io
QDRANT_COLLECTION=testCluster
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2


### Build the docker image ###

docker build -t xitm-rfp-api:dev -f deployment/docker/dockerfile .


### Run the API ###
docker run -d --name rfp-api \
  -p 8080:8080 \
  --env-file .env \
  xitm-rfp-api:dev
docker logs -f rfp-api

### You should only have one container running with the same name, otherwize you'll run into errors

### Try running this in your terminal after running the API. should return ok 
curl -s http://localhost:8080/health








# XITM RFP Analyzer API

This service ingests RFP documents, creates embeddings, stores them in **Qdrant Cloud**, and allows semantic search.  
It is containerized with Docker so teammates only need **Docker Desktop (Mac/Windows)** or **Docker Engine (Linux)**.

---

## ⚙️ Requirements
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 
- A `.env` file with your Qdrant credentials (see below)

---

## 🔑 Environment Variables

Create a file named `.env` in the project root:

```ini
QDRANT_API_KEY= *will send this over text*
QDRANT_URL=https://b0a197c1-9124-4747-815f-8731febbdecd.us-east-1-1.aws.cloud.qdrant.io
QDRANT_COLLECTION=testCluster
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

You will get `QDRANT_URL` and `QDRANT_API_KEY` from Qdrant Cloud.

---

## 🐳 Build & Run with Docker

1. **Clone the repo**  
    cd into the repo
   cd XITM_RFP_Analyzer

2. **Build the Docker image** (first time only):  
   docker build -t xitm-rfp-api:dev -f deployment/docker/Dockerfile .

3. **Run the container with your `.env` file**:  

   docker run --rm -p 8080:8080 --env-file .env xitm-rfp-api:dev


4. The API will now be live at:  
   - Health check: http://localhost:8080/health  

---

## 🧪 Testing the API

### Ingest sample chunks

Copy paste this into another terminal after running the API and docker
```bash
curl -X POST http://localhost:8080/vector/ingest-chunks   -H "Content-Type: application/json"   -d '{
    "doc_id": "RFP-DEMO-001",
    "chunks": [
      {
        "chunk_num": 3,
        "text": "All proposals must be submitted via SAM.gov by 2:00 PM ET."
      },

      {
        "chunk_num": 2, "text": "Technical volume is limited to 25 pages, Times New Roman 12pt."
      },

      {
        "chunk_num": 1, "text": "This procurement is a WOSB set-aside under NAICS 541512."
      }
    ]
  }'

```

Expected response:
```json
{"ok": true, "doc_id": "RFP-DEMO-001", "ingested": 3}
```

### Run a semantic search
```bash
curl -X POST http://localhost:8080/vector/search \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "RFP-DEMO-001",
    "query": "page limits and font requirements",
    "top_k": 3
  }'
```

Expected response (example):
```json
{
  "results": [
    {
      "score": 0.92,
      "text": "Technical volume is limited to 25 pages, Times New Roman 12pt."
    }
  ]
}
```

---

## 🖥️ Windows Users

- **PowerShell**: try the `curl` commands above — works in most modern setups.  
- **Git Bash**: `curl` is bundled with Git for Windows.  
- **Postman/Insomnia**: paste the request body and URL instead of curl.  
- Or use the built-in Swagger docs at http://localhost:8080/docs.

---

## 📂 Project Structure
```
deployment/docker/Dockerfile   # Container build instructions
src/api/app.py                 # FastAPI app (endpoints for ingest & search)
.env.example                   # Example env file
```

---

## 🔄 Common Docker Commands

- List containers:  
  ```bash
  docker ps
  ```
- View logs of running API:  
  ```bash
  docker logs -f <container_id>
  ```
- Stop the API (CTRL+C if running in foreground):  
  ```bash
  docker stop <container_id>
  ```

---

## 📝 Notes
- Everyone uses the **same Qdrant cluster** in the cloud.  
- `doc_id` keeps data separated inside one collection.  
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (dim=384).  
- Collection is auto-created if missing.
