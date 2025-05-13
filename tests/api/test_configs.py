import pytest
from fastapi.testclient import TestClient
from netraven.api.main import app

client = TestClient(app)

def test_search_configs_empty(monkeypatch):
    # Patch DB to return empty for FTS
    class DummyResult:
        def fetchall(self):
            return []
    def dummy_execute(sql, params):
        return DummyResult()
    monkeypatch.setattr("netraven.api.routers.configs.get_db", lambda: None)
    monkeypatch.setattr("sqlalchemy.orm.Session.execute", dummy_execute)
    response = client.get("/api/configs/search?q=test")
    assert response.status_code == 200
    assert response.json() == []
