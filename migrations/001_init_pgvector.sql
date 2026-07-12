CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS memory_projects (
  project_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS memory_sources (
  source_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES memory_projects(project_id),
  source_type TEXT NOT NULL,
  uri TEXT NOT NULL,
  title TEXT,
  version TEXT,
  collected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS memory_documents (
  document_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES memory_projects(project_id),
  source_id TEXT NOT NULL REFERENCES memory_sources(source_id),
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'accepted',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (project_id, content_hash)
);

CREATE TABLE IF NOT EXISTS memory_chunks (
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

CREATE INDEX IF NOT EXISTS memory_chunks_project_idx
  ON memory_chunks(project_id);

CREATE INDEX IF NOT EXISTS memory_chunks_embedding_idx
  ON memory_chunks USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS memory_search_logs (
  search_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES memory_projects(project_id),
  query TEXT NOT NULL,
  memory_hit BOOLEAN NOT NULL,
  source_ids TEXT[] NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
