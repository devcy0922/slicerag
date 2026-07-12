# 10-L3-govail-memory — Project RAG 도메인 규칙

## 프로젝트 정체성

`govail-memory`는 GoVail 플랫폼의 내부 Project RAG 서비스다.

이 서비스는 API Key 인증을 직접 수행하지 않는다. `govail-gateway`가 인증과 `project_id` 식별을 완료한 뒤 내부 API로 호출한다.

## MVP 범위

포함한다.

- `project_id` 기반 namespace
- 문서 ingest
- chunk 저장
- embedding 저장
- RAG search
- sources 반환
- 검색 이벤트 메타데이터 기록

제외한다.

- 웹 검색
- learned_notes
- 난이도/태스크 분류
- 멀티에이전트
- 자동 코드 실행
- 외부 공개 API

## API 경계

모든 API는 내부 경로를 사용한다.

```text
POST /internal/projects/{project_id}/documents
POST /internal/projects/{project_id}/search
GET  /internal/projects/{project_id}/documents/{document_id}
GET  /health
```

외부 클라이언트는 이 API를 직접 호출하지 않는다.

## 저장소 선택

MVP 기본 DB는 macmini의 PostgreSQL + pgvector를 우선한다. Gateway의 project/token 관리가 PostgreSQL과 이미 맞물려 있으므로 운영 일관성을 우선한다.

