# SliceRAG

SliceRAG is a lightweight Project RAG service providing logical context isolation based on tenant namespaces (`project_id`). It handles document ingestion, semantic chunking, embedding generation, and isolated vector searches.

## Architecture

- **Multi-Tenant Separation**: All ingested documents and chunks are tagged and queried using a target `project_id`.
- **Database Engine Options**: Configurable backends supporting both PostgreSQL (with `pgvector`) and an in-memory fallback store for standalone local evaluation.

## API Endpoints

- `POST /internal/projects/{project_id}/documents`: Ingest document text.
- `POST /internal/projects/{project_id}/search`: Execute RAG vector search scoped to the namespace.
- `GET  /health`: Liveness probe.

## Configuration

Settings are controlled via prefix environment variables:
- `AEGIS_MEMORY_STORE`: Active database store (`postgres` or `memory`).
- `AEGIS_MEMORY_DATABASE_URL`: PostgreSQL connection string (only for `postgres` mode).
- `AEGIS_MEMORY_EMBEDDING_PROVIDER`: Selected embedding method (`hash` or `openai`).
