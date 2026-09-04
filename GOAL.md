# GOAL — slicerag

## 1. 프로젝트 비전

Gateway가 확정한 project namespace 안에서만 RAG 문서를 저장·검색하고,
PostgreSQL 장애 시에도 durable storage 계약을 절대 조용히 약화시키지 않는
운영 가능한 내부 메모리 서비스로 유지한다.

## 2. 마일스톤과 목표

- [x] P0: project isolation 및 내부 API 기반 구성
- [x] P1: PostgreSQL/pgvector durable ingest·search·조회
- [x] P2: DB 장애 시 fail-closed(503)와 회귀 테스트
- [ ] P3: PR 검토 및 배포 후 운영 검증

## 3. 현재 변경 목표

- PostgreSQL migration/CRUD 실패 시 in-memory fallback 제거
- durable write가 확인되지 않은 ingest는 `accepted`로 응답하지 않음
- Gateway가 재시도할 수 있도록 `503`과 `Retry-After`를 제공
- isolation 및 장애 경로를 자동 테스트로 보호
