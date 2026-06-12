from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str
    voyage_api_key: str = ""
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "dsa_mentor_knowledge"
    voyage_model: str = "voyage-3.5-lite"
    groq_models_raw: str = Field(
        default="openai/gpt-oss-120b,openai/gpt-oss-20b,llama-3.3-70b-versatile",
        validation_alias="GROQ_MODELS",
    )
    default_groq_model: str = "openai/gpt-oss-120b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )

    @property
    def groq_models(self) -> tuple[str, ...]:
        return tuple(model.strip() for model in self.groq_models_raw.split(",") if model.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
