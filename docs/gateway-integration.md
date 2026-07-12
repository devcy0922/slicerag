# Gateway 연동 계획

## 목표

Gateway는 API Key 인증 이후 `project_id`를 알고 있다. 이 값을 이용해 Memory에 검색을 요청하고, 반환된 chunks를 LLM context에 첨부한다.

## Gateway 변경 범위

Gateway는 다음만 수행한다.

1. API Key에서 `project_id` 확인
2. 사용자 질문에서 검색 query 생성
3. `slicerag` 내부 API 호출
4. 검색 결과를 system/context message에 첨부
5. audit log에 memory metadata 기록

Gateway는 다음을 수행하지 않는다.

- chunking
- embedding 생성
- vector DB 접근
- 웹 검색
- learned_notes 저장

## Audit metadata 초안

```json
{
  "project_id": "aegis-gateway",
  "memory": {
    "enabled": true,
    "memory_hit": true,
    "source_ids": ["src_demo"],
    "chunk_ids": ["chunk_demo"]
  }
}
```

## 장애 처리

MVP에서 Memory 장애는 기본적으로 soft fail이다.

```text
memory unavailable
→ Gateway audit에 memory_error 기록
→ 기존 LLM 요청은 정책 허용 범위 안에서 계속 처리
```

단, 프로젝트 정책에 `memory_required=true`가 도입되면 이후 단계에서 hard fail로 바꿀 수 있다.

