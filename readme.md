
### Put these in your .env located at the root of your repo: ###

QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.CJ_VLIwqMA6BcpBv66qE3ZQvnIWb61y5DpiLtf_L2B0
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
