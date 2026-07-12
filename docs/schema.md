# Aegis Memory 데이터 모델

MVP 기본 저장소는 PostgreSQL + pgvector다.

실행 가능한 초기 migration은 `migrations/001_init_pgvector.sql`에 둔다.

서비스에서 PostgreSQL 저장소를 사용하려면 `SLICERAG_STORE=postgres`와 `SLICERAG_DATABASE_URL`을 설정한다.

검색 대상 문서가 없는 새 `project_id`도 검색 로그를 남길 수 있도록, PostgreSQL store는 search 시작 시 `memory_projects`에 project row를 idempotent하게 보장한다.

## 테이블

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE memory_projects (
  project_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE memory_sources (
  source_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES memory_projects(project_id),
  source_type TEXT NOT NULL,
  uri TEXT NOT NULL,
  title TEXT,
  version TEXT,
  collected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE memory_documents (
  document_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES memory_projects(project_id),
  source_id TEXT NOT NULL REFERENCES memory_sources(source_id),
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'accepted',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (project_id, content_hash)
);

CREATE TABLE memory_chunks (
  chunk_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES memory_projects(project_id),
  document_id TEXT NOT NULL REFERENCES memory_documents(document_id),
  source_id TEXT NOT NULL REFERENCES memory_sources(source_id),
  chunk_index INTEGER NOT NULL,
  text TEXT NOT NULL,
  token_count INTEGER,
  embedding vector(256),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (document_id, chunk_index)
);

CREATE INDEX memory_chunks_project_idx ON memory_chunks(project_id);
CREATE INDEX memory_chunks_embedding_idx ON memory_chunks USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE memory_search_logs (
  search_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES memory_projects(project_id),
  query TEXT NOT NULL,
  memory_hit BOOLEAN NOT NULL,
  source_ids TEXT[] NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
```

## 주의

- `project_id`는 모든 검색과 저장의 필수 스코프다.
- `source_id`와 `document_id`는 audit에서 재참조 가능해야 한다.
- 현재 MVP의 hash embedding은 256차원이다.
- 실제 embedding 모델 확정 후 `vector(256)`은 해당 모델 차원에 맞춰 migration으로 조정한다.
