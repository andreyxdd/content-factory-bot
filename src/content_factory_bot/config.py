from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(default="", alias="BOT_TOKEN")
    database_url: str = Field(
        default="postgresql+asyncpg://cfbot:cfbot@localhost:5432/content_factory",
        alias="DATABASE_URL",
    )
    allowlist_telegram_ids: str = Field(default="", alias="ALLOWLIST_TELEGRAM_IDS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    public_base_url: str = Field(default="", alias="PUBLIC_BASE_URL")
    oauth_state_secret: str = Field(default="", alias="OAUTH_STATE_SECRET")
    meta_app_id: str = Field(default="", alias="META_APP_ID")
    meta_app_secret: str = Field(default="", alias="META_APP_SECRET")
    linkedin_client_id: str = Field(default="", alias="LINKEDIN_CLIENT_ID")
    linkedin_client_secret: str = Field(default="", alias="LINKEDIN_CLIENT_SECRET")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    llm_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="LLM_BASE_URL",
    )
    llm_model_research: str = Field(default="perplexity/sonar-pro", alias="LLM_MODEL_RESEARCH")
    llm_model_research_fallback: str = Field(
        default="perplexity/sonar", alias="LLM_MODEL_RESEARCH_FALLBACK"
    )
    llm_model_draft: str = Field(default="anthropic/claude-sonnet-4", alias="LLM_MODEL_DRAFT")
    llm_model_draft_fallback: str = Field(default="openai/gpt-4o", alias="LLM_MODEL_DRAFT_FALLBACK")
    llm_model_image: str = Field(
        default="black-forest-labs/flux-1.1-pro", alias="LLM_MODEL_IMAGE"
    )
    llm_model_image_fallback: str = Field(default="openai/dall-e-3", alias="LLM_MODEL_IMAGE_FALLBACK")
    llm_model_fast: str = Field(default="openai/gpt-4o-mini", alias="LLM_MODEL_FAST")
    llm_model_fast_fallback: str = Field(
        default="google/gemini-2.5-flash", alias="LLM_MODEL_FAST_FALLBACK"
    )
    llm_model_review: str = Field(default="openai/gpt-4o", alias="LLM_MODEL_REVIEW")
    llm_model_review_fallback: str = Field(
        default="anthropic/claude-sonnet-4", alias="LLM_MODEL_REVIEW_FALLBACK"
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    use_worker: bool = Field(default=False, alias="USE_WORKER")
    auto_create_tables: bool = Field(default=False, alias="AUTO_CREATE_TABLES")
    credentials_encryption_key: str = Field(
        default="", alias="CREDENTIALS_ENCRYPTION_KEY"
    )
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    def parsed_allowlist(self) -> frozenset[int]:
        if not self.allowlist_telegram_ids.strip():
            return frozenset()
        return frozenset(
            int(part.strip())
            for part in self.allowlist_telegram_ids.split(",")
            if part.strip()
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
