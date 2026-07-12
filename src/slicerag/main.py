from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
from langsmith import traceable

from slicerag.models import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    SearchRequest,
    SearchResponse,
)
from slicerag.store_factory import create_store

app = FastAPI(
    title="Aegis Memory",
    description="Aegis 내부 Project RAG 서비스",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = create_store()


@app.get("/", response_class=HTMLResponse)
def read_root():
    # scratch/rag_viewer.html 파일 내용을 직접 읽어서 서빙
    html_path = os.path.join(os.path.dirname(__file__), "../../scratch/rag_viewer.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Aegis Memory RAG Explorer</h1>"


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "aegis-memory"}


@app.get("/internal/projects")
async def get_projects() -> dict[str, list[str]]:
    return {"projects": store.get_projects()}


@app.post(
    "/internal/projects/{project_id}/documents",
    response_model=DocumentIngestResponse,
)
@traceable(run_type="chain", name="Ingest Document")
async def ingest_document(
    project_id: str, request: DocumentIngestRequest
) -> DocumentIngestResponse:
    return store.ingest(project_id, request)


@app.post(
    "/internal/projects/{project_id}/search",
    response_model=SearchResponse,
)
@traceable(run_type="chain", name="RAG Search")
async def search_project(project_id: str, request: SearchRequest) -> SearchResponse:
    return store.search(project_id, request.query, request.limit, request.version)


@app.get("/internal/projects/{project_id}/documents/{document_id}")
async def get_document(project_id: str, document_id: str) -> dict[str, str]:
    document = store.get_document(project_id, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    return {
        "project_id": project_id,
        "document_id": document_id,
        "source_id": document.source_id,
        "content_hash": document.content_hash,
    }
