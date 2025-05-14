import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from tests.api.base import BaseAPITest
import time
import netraven.api.main

class TestSystemStatusAPI(BaseAPITest):
    def setup_method(self):
        # Clear the cache before each test
        netraven.api.main._system_status_cache = {"result": None, "timestamp": 0}

    def test_system_status_healthy(self, client, admin_headers):
        with patch("netraven.api.main.check_postgres", return_value="healthy"), \
             patch("netraven.api.main.check_redis", return_value="healthy"), \
             patch("netraven.api.main.check_worker", return_value="healthy"), \
             patch("netraven.api.main.check_scheduler", return_value="healthy"):
            response = client.get("/system/status?refresh=true", headers=admin_headers)
            self.assert_successful_response(response)
            data = response.json()
            # Only require the health keys to be present
            for k in ["api", "postgres", "redis", "worker", "scheduler"]:
                assert k in data
            assert all(data[k] == "healthy" for k in ["api", "postgres", "redis", "worker", "scheduler"])

    @pytest.mark.parametrize("service", ["postgres", "redis", "worker", "scheduler"])
    def test_system_status_unhealthy_service(self, client, admin_headers, service):
        patch_target = f"netraven.api.main.check_{service}"
        with patch(patch_target, return_value="unhealthy"):
            response = client.get("/system/status?refresh=true", headers=admin_headers)
            self.assert_successful_response(response)
            data = response.json()
            assert data[service] == "unhealthy"
            # Other services should still be present
            for k in ["api", "postgres", "redis", "worker", "scheduler"]:
                assert k in data

    def test_system_status_cache_and_refresh(self, client, admin_headers):
        # Patch all checks to return 'healthy' initially
        with patch("netraven.api.main.check_postgres", return_value="healthy"), \
             patch("netraven.api.main.check_redis", return_value="healthy"), \
             patch("netraven.api.main.check_worker", return_value="healthy"), \
             patch("netraven.api.main.check_scheduler", return_value="healthy"):
            response1 = client.get("/system/status?refresh=true", headers=admin_headers)
            self.assert_successful_response(response1)
            data1 = response1.json()
            assert all(v == "healthy" for v in data1.values())

        # Patch postgres to return 'unhealthy', but without refresh, should get cached 'healthy'
        with patch("netraven.api.main.check_postgres", return_value="unhealthy"):
            response2 = client.get("/system/status", headers=admin_headers)
            self.assert_successful_response(response2)
            data2 = response2.json()
            assert data2["postgres"] == "healthy"  # Still cached

            # Now force refresh
            response3 = client.get("/system/status?refresh=true", headers=admin_headers)
            self.assert_successful_response(response3)
            data3 = response3.json()
            assert data3["postgres"] == "unhealthy"  # Fresh result

    def test_system_status_schema(self, client, admin_headers):
        response = client.get("/system/status?refresh=true", headers=admin_headers)
        self.assert_successful_response(response)
        data = response.json()
        # Only require the health keys to be present
        for k in ["api", "postgres", "redis", "worker", "scheduler"]:
            assert k in data