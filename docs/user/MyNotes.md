Run tests inside docker:
docker exec -it netraven-api-dev bash -c "cd /app && PYTHONPATH=/app poetry run pytest tests/api/"