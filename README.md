# SliceRAG

SliceRAG는 테넌트 식별자(`project_id`) 단위로 논리 격리된 컨텍스트 조회를 제공하는 경량 Project RAG API 서비스입니다. 파이썬(FastAPI) 기반으로 작동하며, 문서의 인제스트, 텍스트 청킹, 임베딩 벡터 생성 및 격리 검색 파이프라인을 지원합니다.

## 시스템 구성 및 인프라

- **멀티테넌시 격리**: 수집된 모든 청크와 문서는 요청된 `project_id` 네임스페이스에 종속되어 상호 격리 검색이 보장됩니다.
- **다중 저장소 엔진**: 정적 분석 및 운영 환경을 위한 PostgreSQL (with `pgvector`) 데이터베이스뿐만 아니라, 로컬 데모 및 테스트를 위해 DB 연결이 없는 인메모리 임베딩 폴백 스토어(`memory`)를 함께 내장하고 있습니다.

## API 명세

- `POST /internal/projects/{project_id}/documents`: 대상 프로젝트 네임스페이스에 문서 텍스트 수집/등록.
- `POST /internal/projects/{project_id}/search`: 해당 프로젝트 범위 내에서 의미론적 RAG 검색 실행.
- `GET  /health`: 서비스 활성 상태 확인.

## 환경 변수 설정

- `AEGIS_MEMORY_STORE`: 사용할 스토어 엔진 유형 (`postgres` 또는 `memory`).
- `AEGIS_MEMORY_DATABASE_URL`: PostgreSQL 데이터베이스 접속 문자열 (`postgres` 모드 전용).
- `AEGIS_MEMORY_EMBEDDING_PROVIDER`: 임베딩 생성 방식 (`hash` 또는 `openai`).
