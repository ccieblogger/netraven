Run tests inside docker:
docker exec -it netraven-api-dev bash -c "cd /app && PYTHONPATH=/app poetry run pytest tests/api/"

get all api endpoints.
curl -s http://localhost:8000/openapi.json | jq '.paths | keys'

Get user access token:
curl -s -X POST http://localhost/api/auth/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&password=admin123'


 # Get the token and store in $TOKEN
TOKEN=$(curl -s -X POST http://localhost/api/auth/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&password=admin123' | jq -r .access_token)

# Use the token to query the endpoint
curl -s http://localhost:8000/jobs/status \
  -H "Authorization: Bearer $TOKEN" | jq . 

# Use the token to query job-logs endpoint
curl -X GET "http://localhost:8000/job-logs/" \
  -H "Authorization: Bearer $TOKEN" | jq . 

# List Jobs in DB
  curl -X GET "http://localhost:8000/jobs/" \
    -H "Authorization: Bearer $TOKEN" | jq .

# Redis Queue status
  curl -X GET "http://localhost:8000/scheduler/queue/status" \
    -H "Authorization: Bearer $TOKEN" | jq .

# Use the token to query log stream
   curl -H "Authorization: Bearer $TOKEN" http://localhost/api/logs/stream
   curl -i -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/logs/stream?job_id=1

# Use the token to get log stream

# Grepping container logs
docker logs netraven-worker-dev 2>&1 | grep UnifiedLogger

# Grepping container logs with tail
docker logs -f netraven-worker-dev 2>&1 | grep UnifiedLogger


# Worker container commands
rq info --url redis://redis:6379/0

docker exec netraven-worker-dev rq info --url redis://redis:6379/0