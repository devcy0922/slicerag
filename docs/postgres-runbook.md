# PostgreSQL + pgvector 운영 검증

이 문서는 `slicerag`를 운영 PostgreSQL + pgvector 저장소로 검증하는 절차다.

## 전제

- PostgreSQL은 격리된 데이터 노드의 `shared-postgres` 컨테이너에서 동작한다.
- `pg_available_extensions`에 `vector`가 있어야 한다.
- 운영 계정/비밀번호는 `.env` 또는 인프라 전용 secret으로 관리하고 문서에 기록하지 않는다.

## DB 초기화

```bash
docker exec -i shared-postgres sh -lc 'psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1' <<'SQL'
SELECT 'CREATE DATABASE slicerag'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'slicerag')\gexec
SQL

docker exec -i shared-postgres sh -lc 'psql -U "$POSTGRES_USER" -d slicerag -v ON_ERROR_STOP=1' \
  < "${PROJECT_DIR}/migrations/001_init_pgvector.sql"
```

## 서비스 실행

```bash
SLICERAG_STORE=postgres \
SLICERAG_DATABASE_URL='postgresql://<user>:<password>@127.0.0.1:5432/slicerag' \
SLICERAG_INTERNAL_TOKEN='<gateway와-공유하는-긴-무작위-토큰>' \
uvicorn slicerag.main:app --host 127.0.0.1 --port 8095
```

## E2E 확인

```bash
curl -sS http://127.0.0.1:8095/health

curl -sS -X POST http://127.0.0.1:8095/internal/projects/aegis-gateway/documents \
  -H 'content-type: application/json' \
  -H 'X-SliceRAG-Internal-Token: <internal-token>' \
  -d '{"source":{"type":"markdown","uri":"repo://aegis-gateway/memory.md"},"content":"Aegis Gateway는 API Key로 project_id를 식별하고 slicerag는 해당 프로젝트 문서만 RAG 검색한다."}'

curl -sS -X POST http://127.0.0.1:8095/internal/projects/aegis-gateway/search \
  -H 'content-type: application/json' \
  -H 'X-SliceRAG-Internal-Token: <internal-token>' \
  -d '{"query":"project_id RAG 검색","limit":3}'

curl -sS -X POST http://127.0.0.1:8095/internal/projects/other-project/search \
  -H 'content-type: application/json' \
  -H 'X-SliceRAG-Internal-Token: <internal-token>' \
  -d '{"query":"project_id RAG 검색","limit":3}'
```

기대 결과:

- `aegis-gateway`는 `memory_hit=true`
- `other-project`는 `memory_hit=false`
- `memory_search_logs`에는 두 검색 이벤트가 저장된다.

## 2026-06-23 프로젝트 서버 검증 결과

```text
pgvector available: vector 0.8.2
memory_projects: 2
memory_sources: 1
memory_documents: 1
memory_chunks: 1
memory_search_logs: 2
aegis-gateway search: memory_hit=true, source_ids=1
other-project search: memory_hit=false
```
