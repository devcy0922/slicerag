# GoVail Memory API

모든 API는 내부 서비스 호출용이다. 외부 클라이언트는 직접 호출하지 않는다.

## Health

```http
GET /health
```

응답:

```json
{
  "status": "ok",
  "service": "govail-memory"
}
```

## Document Ingest

```http
POST /internal/projects/{project_id}/documents
```

요청:

```json
{
  "source": {
    "type": "markdown",
    "uri": "repo://govail-gateway/README.md",
    "title": "GoVail Gateway README",
    "version": "main"
  },
  "content": "# 문서 본문",
  "metadata": {
    "repository": "govail-gateway",
    "branch": "main"
  }
}
```

응답:

```json
{
  "project_id": "govail-gateway",
  "document_id": "doc_demo",
  "chunk_count": 4,
  "status": "accepted"
}
```

## Search

```http
POST /internal/projects/{project_id}/search
```

검색은 항상 `{project_id}` 네임스페이스 안에서만 수행된다. 같은 문서가 다른 프로젝트에 없으면 같은 query라도 `memory_hit=false`가 반환되어야 한다.

요청:

```json
{
  "query": "Gateway와 LiteLLM 라우팅 구조는?",
  "limit": 5
}
```

응답:

```json
{
  "project_id": "govail-gateway",
  "query": "Gateway와 LiteLLM 라우팅 구조는?",
  "memory_hit": true,
  "chunks": [
    {
      "chunk_id": "chunk_demo",
      "document_id": "doc_demo",
      "score": 0.83,
      "text": "Gateway는 외부 진입점이며 LiteLLM은 내부 모델 라우터다.",
      "source_id": "src_demo"
    }
  ],
  "sources": [
    {
      "source_id": "src_demo",
      "type": "markdown",
      "uri": "repo://govail-gateway/README.md",
      "title": "GoVail Gateway README",
      "version": "main"
    }
  ]
}
```
