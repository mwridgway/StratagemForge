from __future__ import annotations

import io

from fastapi.testclient import TestClient

from stratagemforge.api import deps
from stratagemforge.core.app import create_app
from stratagemforge.core.config import Settings


def create_test_client(tmp_path) -> TestClient:
    data_dir = tmp_path / "data"
    settings = Settings(data_dir=data_dir, database_url=f"sqlite:///{tmp_path}/test.db")
    settings.ensure_directories()
    deps.configure(settings)
    app = create_app(settings)
    return TestClient(app)


def test_full_upload_and_analysis_flow(tmp_path):
    with create_test_client(tmp_path) as client:
        health = client.get("/health")
        assert health.status_code == 200

        upload_response = client.post(
            "/api/demos/upload",
            files={"demo": ("test.dem", io.BytesIO(b"demo data"), "application/octet-stream")},
        )
        assert upload_response.status_code == 201
        payload = upload_response.json()
        demo_id = payload["id"]
        assert payload["status"] == "processed"

        list_response = client.get("/api/demos")
        assert list_response.status_code == 200
        listing = list_response.json()
        assert listing["count"] == 1
        assert listing["demos"][0]["id"] == demo_id

        analysis_response = client.post("/api/analysis", json={"demo_id": demo_id})
        assert analysis_response.status_code == 200
        analysis = analysis_response.json()
        assert analysis["results"]["row_count"] == 1

        users_response = client.get("/api/users")
        assert users_response.status_code == 200
        users = users_response.json()
        assert len(users) >= 1
