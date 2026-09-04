# Gateway 연동 계획

## 목표

Gateway는 API Key 인증 이후 `project_id`를 알고 있다. 이 값을 이용해 Memory에 검색을 요청하고, 반환된 chunks를 LLM context에 첨부한다.

## Gateway 변경 범위

Gateway는 다음만 수행한다.

1. API Key에서 `project_id` 확인
2. 사용자 질문에서 검색 query 생성
3. `project_id`와 내부 서비스 토큰을 포함해 `slicerag` 내부 API 호출
4. 검색 결과를 system/context message에 첨부
5. audit log에 memory metadata 기록

Gateway는 다음을 수행하지 않는다.

- chunking
- embedding 생성
- vector DB 접근
- 웹 검색
- learned_notes 저장

SliceRAG는 외부 API Key나 사용자 권한을 해석하지 않는다. Gateway가 외부 인증과 프로젝트 스코프를 확정하고, SliceRAG는 `X-SliceRAG-Internal-Token`으로 호출 주체가 Gateway인지 확인한다.

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

PostgreSQL 저장소를 사용하는 환경에서 DB migration 또는 operation이 실패하면
SliceRAG는 메모리로 자동 전환하지 않고 `503 Service Unavailable`을 반환한다.
따라서 `accepted` 응답은 항상 durable write가 완료된 경우에만 의미한다.

Gateway는 `503`을 `memory_error`로 audit하고, `Retry-After` 헤더를 존중해 재시도하거나
정책에 따라 상위 요청을 중단해야 한다. 인메모리 저장소는 명시적으로
`SLICERAG_STORE=memory`를 선택한 로컬 테스트 전용 구성이다.
