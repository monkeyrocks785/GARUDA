from fastapi.testclient import TestClient

from database.connection import Base, engine
from main import app

Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "uptime" in data
    assert "environment" in data
    assert "timestamp" in data


def test_detailed_health_endpoint():
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "timestamp" in data


def test_docs_endpoint():
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_endpoint():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data
