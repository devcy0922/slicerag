from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SLICERAG_")

    store: str = "memory"
    database_url: str = ""
    embedding_dimensions: int = 256
    embedding_provider: str = "hash"
    embedding_model: str = "text-embedding-3-small"
    embedding_gateway_url: str = ""
    embedding_api_key: str = ""
    internal_token: str = ""


settings = Settings()
