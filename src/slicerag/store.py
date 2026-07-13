import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime

from slicerag.chunking import chunk_text
from slicerag.embedding import cosine_similarity, get_embedding_provider
from slicerag.ids import stable_id
from slicerag.models import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    SearchChunk,
    SearchResponse,
    SearchSource,
)


@dataclass
class StoredSource:
    source_id: str
    project_id: str
    type: str
    uri: str
    title: str | None
    version: str | None
    collected_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class StoredDocument:
    document_id: str
    project_id: str
    source_id: str
    content_hash: str
    metadata: dict[str, object]
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class StoredChunk:
    chunk_id: str
    project_id: str
    document_id: str
    source_id: str
    chunk_index: int
    text: str
    embedding: list[float]
    version: str = "1.0.0"


class MemoryStore:
    def __init__(self, embedding_provider = None) -> None:
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.sources: dict[str, StoredSource] = {}
        self.documents: dict[str, StoredDocument] = {}
        self.chunks: dict[str, StoredChunk] = {}

    def ingest(self, project_id: str, request: DocumentIngestRequest) -> DocumentIngestResponse:
        source_id = stable_id("src", project_id, request.source.uri)
        content_hash = hashlib.sha256(request.content.encode("utf-8")).hexdigest()
        document_id = stable_id("doc", project_id, request.source.uri, content_hash)
        version = request.source.version or "1.0.0"

        self.sources[source_id] = StoredSource(
            source_id=source_id,
            project_id=project_id,
            type=request.source.type,
            uri=request.source.uri,
            title=request.source.title,
            version=request.source.version,
        )
        self.documents[document_id] = StoredDocument(
            document_id=document_id,
            project_id=project_id,
            source_id=source_id,
            content_hash=content_hash,
            metadata=dict(request.metadata),
            version=version,
        )

        chunks = chunk_text(request.content)
        for chunk in chunks:
            chunk_id = stable_id("chunk", document_id, str(chunk.index), chunk.text)
            self.chunks[chunk_id] = StoredChunk(
                chunk_id=chunk_id,
                project_id=project_id,
                document_id=document_id,
                source_id=source_id,
                chunk_index=chunk.index,
                text=chunk.text,
                embedding=self.embedding_provider.embed(chunk.text),
                version=version,
            )

        return DocumentIngestResponse(
            project_id=project_id,
            document_id=document_id,
            chunk_count=len(chunks),
            status="accepted",
        )

    def search(self, project_id: str, query: str, limit: int, version: str | None = None) -> SearchResponse:
        query_embedding = self.embedding_provider.embed(query)
        scored_chunks = [
            (cosine_similarity(query_embedding, chunk.embedding), chunk)
            for chunk in self.chunks.values()
            if chunk.project_id == project_id
            and (version is None or chunk.version == version)
        ]
        scored_chunks.sort(key=lambda item: item[0], reverse=True)
        selected = [(score, chunk) for score, chunk in scored_chunks[:limit] if score > 0]

        source_ids = {chunk.source_id for _, chunk in selected}
        sources = [
            SearchSource(
                source_id=source.source_id,
                type=source.type,
                uri=source.uri,
                title=source.title,
                version=source.version,
            )
            for source in self.sources.values()
            if source.source_id in source_ids
        ]

        return SearchResponse(
            project_id=project_id,
            query=query,
            memory_hit=bool(selected),
            chunks=[
                SearchChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    score=round(score, 6),
                    text=chunk.text,
                    source_id=chunk.source_id,
                )
                for score, chunk in selected
            ],
            sources=sources,
        )

    def get_document(self, project_id: str, document_id: str) -> StoredDocument | None:
        document = self.documents.get(document_id)
        if document is None or document.project_id != project_id:
            return None
        return document
