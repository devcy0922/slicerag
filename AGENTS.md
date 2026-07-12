# GoVail Memory — AI Agent Guide

작업 시작 전에는 반드시 `agents/rules/rules.md`를 먼저 읽고 프로젝트 규칙을 로드한다.

이 저장소는 GoVail 플랫폼의 내부 Project RAG 컴포넌트다. 외부 클라이언트의 진입점이 아니며, `govail-gateway`가 인증과 프로젝트 스코프를 확인한 뒤 내부 서비스로 호출한다.

## 책임 경계

```text
Client / IDE / CLI
→ govail-gateway
→ Auth / Project Scope / Policy / Audit
→ govail-memory
→ Project RAG context
→ govail-gateway
→ LiteLLM
→ vLLM / MLX
```

`govail-memory`는 다음 책임만 가진다.

- 프로젝트별 문서 네임스페이스 관리
- 문서 ingest
- chunk 및 embedding 저장
- 프로젝트 스코프 기반 RAG 검색
- 검색 근거와 source 반환

MVP에서는 다음 기능을 구현하지 않는다.

- 웹 검색
- learned_notes 승격
- 난이도/태스크 분류
- 멀티에이전트 실행
- 자동 코드 실행
- 외부 공개 API

## 개발 원칙

- 모든 공개 문서와 코드 주석은 한국어로 작성한다.
- 외부 요청 인증은 `govail-gateway` 책임이다.
- `govail-memory`는 내부 네트워크에서만 접근 가능한 서비스로 배포한다.
- 직접 vLLM 또는 LiteLLM을 공개 계약으로 호출하지 않는다. 모델 호출은 Gateway 정책 경유를 기본 원칙으로 한다.
- raw 문서와 실제 고객 소스코드는 커밋하지 않는다.

