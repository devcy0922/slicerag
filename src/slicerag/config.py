from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AEGIS_MEMORY_")

    store: str = "memory"
    database_url: str = ""
    embedding_dimensions: int = 256
    embedding_provider: str = "hash"
    embedding_model: str = "text-embedding-3-small"
    openai_api_key: str = "dummy"
    openai_base_url: str = ""


settings = Settings()

