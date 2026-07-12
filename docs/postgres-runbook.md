# PostgreSQL + pgvector 운영 검증

이 문서는 `govail-memory`를 macmini의 PostgreSQL + pgvector 저장소로 검증하는 절차다.

## 전제

- PostgreSQL은 macmini의 `shared-postgres` 컨테이너에서 동작한다.
- `pg_available_extensions`에 `vector`가 있어야 한다.
- 운영 계정/비밀번호는 `.env` 또는 인프라 전용 secret으로 관리하고 문서에 기록하지 않는다.

## DB 초기화

```bash
docker exec -i shared-postgres sh -lc 'psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1' <<'SQL'
SELECT 'CREATE DATABASE govail_memory'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'govail_memory')\gexec
SQL

docker exec -i shared-postgres sh -lc 'psql -U "$POSTGRES_USER" -d govail_memory -v ON_ERROR_STOP=1' \
  < /srv/govail-memory/migrations/001_init_pgvector.sql
```

## 서비스 실행

```bash
GOVAIL_MEMORY_STORE=postgres \
GOVAIL_MEMORY_DATABASE_URL='postgresql://<user>:<password>@127.0.0.1:5432/govail_memory' \
uvicorn govail_memory.main:app --host 127.0.0.1 --port 8095
```

## E2E 확인

```bash
curl -sS http://127.0.0.1:8095/health

curl -sS -X POST http://127.0.0.1:8095/internal/projects/govail-gateway/documents \
  -H 'content-type: application/json' \
  -d '{"source":{"type":"markdown","uri":"repo://govail-gateway/memory.md"},"content":"GoVail Gateway는 API Key로 project_id를 식별하고 govail-memory는 해당 프로젝트 문서만 RAG 검색한다."}'

curl -sS -X POST http://127.0.0.1:8095/internal/projects/govail-gateway/search \
  -H 'content-type: application/json' \
  -d '{"query":"project_id RAG 검색","limit":3}'

curl -sS -X POST http://127.0.0.1:8095/internal/projects/other-project/search \
  -H 'content-type: application/json' \
  -d '{"query":"project_id RAG 검색","limit":3}'
```

기대 결과:

- `govail-gateway`는 `memory_hit=true`
- `other-project`는 `memory_hit=false`
- `memory_search_logs`에는 두 검색 이벤트가 저장된다.

## 2026-06-23 macmini 검증 결과

```text
pgvector available: vector 0.8.2
memory_projects: 2
memory_sources: 1
memory_documents: 1
memory_chunks: 1
memory_search_logs: 2
govail-gateway search: memory_hit=true, source_ids=1
other-project search: memory_hit=false
```

