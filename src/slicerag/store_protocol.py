from typing import Protocol

from slicerag.models import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    SearchResponse,
)
from slicerag.store import StoredDocument


class MemoryStoreProtocol(Protocol):
    def ingest(
        self, project_id: str, request: DocumentIngestRequest
    ) -> DocumentIngestResponse:
        ...

    def search(self, project_id: str, query: str, limit: int) -> SearchResponse:
        ...

    def get_document(self, project_id: str, document_id: str) -> StoredDocument | None:
        ...

