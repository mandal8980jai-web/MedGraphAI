from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "llm_key_set" in data
        assert "model" in data


def test_config_defaults():
    from app.core.config import settings
    assert settings.DATABASE_URL.startswith("sqlite")
    assert settings.RETENTION_DAYS == 7
    assert settings.MAX_UPLOAD_MB == 15
