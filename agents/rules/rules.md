# AI Agent Core Routing Hub — GoVail Memory

> 작업 시작 전 반드시 이 파일을 먼저 읽고 규칙을 로드한다.

이 파일은 `govail-memory`에서 에이전트가 로드해야 할 로컬 규칙의 인덱스다.

## 항상 로드

1. `agents/project.yaml`
   - 프로젝트 메타데이터, 배포 대상, 검증 도구를 확인한다.
2. `agents/rules/00-L2-common.md`
   - GoVail 공통 보안/문서/작업 규칙을 확인한다.
3. `agents/rules/10-L3-govail-memory.md`
   - Project RAG, ingest, embedding, search API 작업 시 확인한다.

## 핵심 경계

`govail-memory`는 외부 클라이언트 진입점이 아니다.

```text
외부 공개: govail-gateway
내부 호출: govail-memory
모델 호출: govail-gateway 정책 경유
```

Gateway 안에 RAG 저장소, 크롤러, worker, embedding 저장 로직을 넣지 않는다.

