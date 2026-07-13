from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path
from langsmith import traceable

from slicerag.auth import require_internal_access
from slicerag.models import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    SearchRequest,
    SearchResponse,
)
from slicerag.store_factory import create_store

app = FastAPI(
    title="SliceRAG",
    description="Gateway가 호출하는 내부 Project RAG 서비스",
    version="0.1.0",
)
store = create_store()
internal_router = APIRouter(
    prefix="/internal",
    dependencies=[Depends(require_internal_access)],
)
ProjectPathId = Annotated[
    str,
    Path(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9_-]*$",
        description="Gateway가 인증 결과에서 결정한 프로젝트 식별자",
    ),
]


def require_project_scope(project_id: ProjectPathId) -> str:
    if project_id == "all":
        raise HTTPException(
            status_code=422,
            detail="예약된 프로젝트 식별자는 사용할 수 없습니다.",
        )
    return project_id


ProjectId = Annotated[str, Depends(require_project_scope)]


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "slicerag"}


@internal_router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentIngestResponse,
)
@traceable(run_type="chain", name="Ingest Document")
async def ingest_document(
    project_id: ProjectId, request: DocumentIngestRequest
) -> DocumentIngestResponse:
    return store.ingest(project_id, request)


@internal_router.post(
    "/projects/{project_id}/search",
    response_model=SearchResponse,
)
@traceable(run_type="chain", name="RAG Search")
async def search_project(
    project_id: ProjectId, request: SearchRequest
) -> SearchResponse:
    return store.search(project_id, request.query, request.limit, request.version)


@internal_router.get("/projects/{project_id}/documents/{document_id}")
async def get_document(project_id: ProjectId, document_id: str) -> dict[str, str]:
    document = store.get_document(project_id, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    return {
        "project_id": project_id,
        "document_id": document_id,
        "source_id": document.source_id,
        "content_hash": document.content_hash,
    }


app.include_router(internal_router)
