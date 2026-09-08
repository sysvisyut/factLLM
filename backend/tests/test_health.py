from fastapi.testclient import TestClient
from app.models import Document, Fact, Relationship, EvidenceAtom


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert "version" in data
    assert "database" in data
    assert "llm_provider" in data


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "FACTMESH"
    assert "docs_url" in data


def test_database_tables_exist(db_session):
    # Verify that we can query all primary models without errors
    assert db_session.query(Document).count() == 0
    assert db_session.query(EvidenceAtom).count() == 0
    assert db_session.query(Fact).count() == 0
    assert db_session.query(Relationship).count() == 0
