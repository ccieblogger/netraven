Run tests inside docker:
docker exec -it netraven-api-dev bash -c "cd /app && PYTHONPATH=/app poetry run pytest tests/api/"

get all api endpoints.
curl -s http://localhost:8000/openapi.json | jq '.paths | keys'

Get user access token:
curl -s -X POST http://localhost:8000/auth/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&password=admin123'


 # Get the token and store in $TOKEN
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&password=admin123' | jq -r .access_token)

# Use the token to query the endpoint
curl -s http://localhost:8000/jobs/status \
  -H "Authorization: Bearer $TOKEN" | jq . 

# Use the token to query job-logs endpoint
curl -X GET "http://localhost:8000/job-logs/" \
  -H "Authorization: Bearer $TOKEN" | jq . 