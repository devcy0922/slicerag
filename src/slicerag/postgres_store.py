import hashlib
import json
import os
from typing import Any

from slicerag.chunking import chunk_text
from slicerag.embedding import get_embedding_provider
from slicerag.ids import stable_id
from slicerag.models import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    SearchChunk,
    SearchResponse,
    SearchSource,
)
from slicerag.store import StoredDocument


def run_migrations(database_url: str) -> None:
    import psycopg

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    migrations_dir = os.path.join(base_dir, "migrations")
    if not os.path.exists(migrations_dir):
        return

    sql_files = sorted(
        [f for f in os.listdir(migrations_dir) if f.endswith(".sql")]
    )

    with psycopg.connect(database_url) as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
            for sql_file in sql_files:
                file_path = os.path.join(migrations_dir, sql_file)
                with open(file_path, "r", encoding="utf-8") as f:
                    sql = f.read()
                cursor.execute(sql)


class PostgresMemoryStore:
    def __init__(
        self,
        database_url: str,
        embedding_provider = None,
    ) -> None:
        if not database_url:
            raise ValueError("SLICERAG_DATABASE_URL is required for postgres store")
        self.database_url = database_url
        self.embedding_provider = embedding_provider or get_embedding_provider()
        run_migrations(self.database_url)

    def ingest(self, project_id: str, request: DocumentIngestRequest) -> DocumentIngestResponse:
        import psycopg

        source_id = stable_id("src", project_id, request.source.uri)
        content_hash = hashlib.sha256(request.content.encode("utf-8")).hexdigest()
        document_id = stable_id("doc", project_id, request.source.uri, content_hash)
        chunks = chunk_text(request.content)
        version = request.source.version or "1.0.0"

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO memory_projects (project_id, display_name)
                    VALUES (%s, %s)
                    ON CONFLICT (project_id) DO NOTHING
                    """,
                    (project_id, project_id),
                )
                cursor.execute(
                    """
                    INSERT INTO memory_sources
                      (source_id, project_id, source_type, uri, title, version, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (source_id) DO UPDATE SET
                      source_type = EXCLUDED.source_type,
                      uri = EXCLUDED.uri,
                      title = EXCLUDED.title,
                      version = EXCLUDED.version,
                      metadata = EXCLUDED.metadata
                    """,
                    (
                        source_id,
                        project_id,
                        request.source.type,
                        request.source.uri,
                        request.source.title,
                        request.source.version,
                        json.dumps(request.metadata, ensure_ascii=False),
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO memory_documents
                      (document_id, project_id, source_id, content_hash, version, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (project_id, content_hash) DO UPDATE SET
                      source_id = EXCLUDED.source_id,
                      version = EXCLUDED.version,
                      metadata = EXCLUDED.metadata
                    """,
                    (
                        document_id,
                        project_id,
                        source_id,
                        content_hash,
                        version,
                        json.dumps(request.metadata, ensure_ascii=False),
                    ),
                )
                cursor.execute(
                    "DELETE FROM memory_chunks WHERE document_id = %s",
                    (document_id,),
                )
                for chunk in chunks:
                    chunk_id = stable_id("chunk", document_id, str(chunk.index), chunk.text)
                    cursor.execute(
                        """
                        INSERT INTO memory_chunks
                          (chunk_id, project_id, document_id, source_id, chunk_index, text, embedding, version)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s)
                        """,
                        (
                            chunk_id,
                            project_id,
                            document_id,
                            source_id,
                            chunk.index,
                            chunk.text,
                            _vector_literal(self.embedding_provider.embed(chunk.text)),
                            version,
                        ),
                    )

        return DocumentIngestResponse(
            project_id=project_id,
            document_id=document_id,
            chunk_count=len(chunks),
            status="accepted",
        )

    def search(self, project_id: str, query: str, limit: int, version: str | None = None) -> SearchResponse:
        import psycopg

        query_embedding = self.embedding_provider.embed(query)
        search_id = stable_id("search", project_id, query, version or "")

        with psycopg.connect(self.database_url) as conn:
            rows: list[dict[str, Any]]
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO memory_projects (project_id, display_name)
                    VALUES (%s, %s)
                    ON CONFLICT (project_id) DO NOTHING
                    """,
                    (project_id, project_id),
                )
                
                version_filter = ""
                query_params = [
                    _vector_literal(query_embedding),
                    project_id,
                ]
                
                if version:
                    version_filter = "AND c.version = %s"
                    query_params.append(version)
                    
                query_params.extend([
                    _vector_literal(query_embedding),
                    limit
                ])

                sql = f"""
                    SELECT
                      c.chunk_id,
                      c.document_id,
                      c.source_id,
                      c.text,
                      1 - (c.embedding <=> %s::vector) AS score,
                      s.source_type,
                      s.uri,
                      s.title,
                      s.version
                    FROM memory_chunks c
                    JOIN memory_sources s ON s.source_id = c.source_id
                    WHERE c.project_id = %s {version_filter}
                    ORDER BY c.embedding <=> %s::vector
                    LIMIT %s
                """
                cursor.execute(sql, tuple(query_params))
                rows = list(cursor.fetchall())

                selected = [row for row in rows if float(row["score"]) > 0]
                source_ids = sorted({str(row["source_id"]) for row in selected})
                cursor.execute(
                    """
                    INSERT INTO memory_search_logs
                      (search_id, project_id, query, memory_hit, source_ids)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (search_id) DO UPDATE SET
                      memory_hit = EXCLUDED.memory_hit,
                      source_ids = EXCLUDED.source_ids,
                      created_at = now()
                    """,
                    (search_id, project_id, query, bool(selected), source_ids),
                )

        sources_by_id = {
            str(row["source_id"]): SearchSource(
                source_id=str(row["source_id"]),
                type=str(row["source_type"]),
                uri=str(row["uri"]),
                title=row["title"],
                version=row["version"],
            )
            for row in selected
        }

        return SearchResponse(
            project_id=project_id,
            query=query,
            memory_hit=bool(selected),
            chunks=[
                SearchChunk(
                    chunk_id=str(row["chunk_id"]),
                    document_id=str(row["document_id"]),
                    score=round(float(row["score"]), 6),
                    text=str(row["text"]),
                    source_id=str(row["source_id"]),
                )
                for row in selected
            ],
            sources=list(sources_by_id.values()),
        )

    def get_document(self, project_id: str, document_id: str) -> StoredDocument | None:
        import psycopg

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT document_id, project_id, source_id, content_hash, metadata, created_at
                    FROM memory_documents
                    WHERE project_id = %s AND document_id = %s
                    """,
                    (project_id, document_id),
                )
                row = cursor.fetchone()

        if row is None:
            return None
        return StoredDocument(
            document_id=str(row["document_id"]),
            project_id=str(row["project_id"]),
            source_id=str(row["source_id"]),
            content_hash=str(row["content_hash"]),
            metadata=dict(row["metadata"]),
            created_at=row["created_at"],
        )

def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.9f}" for value in values) + "]"
