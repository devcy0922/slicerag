import pytest
from fastapi.testclient import TestClient

from slicerag import main
from slicerag.config import settings
from slicerag.store import MemoryStore

INTERNAL_TOKEN = "test-internal-token"
HEADERS = {"X-SliceRAG-Internal-Token": INTERNAL_TOKEN}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(settings, "internal_token", INTERNAL_TOKEN)
    monkeypatch.setattr(main, "store", MemoryStore())
    return TestClient(main.app)


def ingest_document(client: TestClient, project_id: str) -> str:
    response = client.post(
        f"/internal/projects/{project_id}/documents",
        headers=HEADERS,
        json={
            "source": {
                "type": "markdown",
                "uri": f"repo://{project_id}/architecture.md",
                "title": "격리 테스트 문서",
            },
            "content": "SliceRAG는 프로젝트별 문서를 격리하여 검색합니다.",
        },
    )
    assert response.status_code == 200
    return response.json()["document_id"]


def test_internal_api_rejects_missing_or_invalid_token(client: TestClient) -> None:
    payload = {"query": "격리", "limit": 3}

    missing = client.post("/internal/projects/alpha/search", json=payload)
    invalid = client.post(
        "/internal/projects/alpha/search",
        headers={"X-SliceRAG-Internal-Token": "invalid-token"},
        json=payload,
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401


def test_project_scope_prevents_cross_project_reads(client: TestClient) -> None:
    document_id = ingest_document(client, "alpha")

    alpha_search = client.post(
        "/internal/projects/alpha/search",
        headers=HEADERS,
        json={"query": "프로젝트별 문서 격리", "limit": 3},
    )
    beta_search = client.post(
        "/internal/projects/beta/search",
        headers=HEADERS,
        json={"query": "프로젝트별 문서 격리", "limit": 3},
    )
    cross_project_document = client.get(
        f"/internal/projects/beta/documents/{document_id}",
        headers=HEADERS,
    )

    assert alpha_search.status_code == 200
    assert alpha_search.json()["memory_hit"] is True
    assert beta_search.status_code == 200
    assert beta_search.json()["memory_hit"] is False
    assert beta_search.json()["chunks"] == []
    assert cross_project_document.status_code == 404


def test_reserved_or_invalid_project_id_is_rejected(client: TestClient) -> None:
    reserved = client.post(
        "/internal/projects/all/search",
        headers=HEADERS,
        json={"query": "격리", "limit": 3},
    )
    invalid = client.post(
        "/internal/projects/UpperCase/search",
        headers=HEADERS,
        json={"query": "격리", "limit": 3},
    )

    assert reserved.status_code == 422
    assert invalid.status_code == 422


def test_project_enumeration_and_browser_ui_are_not_exposed(client: TestClient) -> None:
    projects = client.get("/internal/projects", headers=HEADERS)
    root = client.get("/")

    assert projects.status_code == 404
    assert root.status_code == 404
