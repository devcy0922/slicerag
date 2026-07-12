from typing import Any, Literal

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    type: str = Field(..., description="문서 출처 종류")
    uri: str = Field(..., description="출처 URI 또는 repo 경로")
    title: str | None = None
    version: str | None = None


class DocumentIngestRequest(BaseModel):
    source: SourceRef
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentIngestResponse(BaseModel):
    project_id: str
    document_id: str
    chunk_count: int
    status: Literal["accepted"]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=100)
    version: str | None = Field(default=None, description="격리 검색할 문서 버전 정보")


class SearchChunk(BaseModel):
    chunk_id: str
    document_id: str
    score: float
    text: str
    source_id: str


class SearchSource(BaseModel):
    source_id: str
    type: str
    uri: str
    title: str | None = None
    version: str | None = None


class SearchResponse(BaseModel):
    project_id: str
    query: str
    memory_hit: bool
    chunks: list[SearchChunk]
    sources: list[SearchSource]

