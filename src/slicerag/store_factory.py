from slicerag.config import settings
from slicerag.postgres_store import PostgresMemoryStore
from slicerag.store import MemoryStore
from slicerag.store_protocol import MemoryStoreProtocol


def create_store() -> MemoryStoreProtocol:
    if settings.store == "postgres":
        return PostgresMemoryStore(settings.database_url)
    if settings.store == "memory":
        return MemoryStore()
    raise ValueError(f"unsupported SLICERAG_STORE={settings.store}. Mock memory store is disabled.")

