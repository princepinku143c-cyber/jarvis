from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JARVIS_", env_file=".env", extra="ignore")

    model_provider: str = "openrouter"
    model: str = "anthropic/claude-sonnet-4"
    fallback_model: str | None = "anthropic/claude-sonnet-4"
    openrouter_api_key: str | None = None
    database_url: str = "sqlite:///./storage/jarvis.db"
    browser_headless: bool = True
    browser_executable_path: str | None = None
    require_confirmation: bool = True
    allowed_tools: str = "web,browser,memory,scheduler"
    log_level: str = "INFO"

    @property
    def allowed_tool_set(self) -> set[str]:
        return {x.strip() for x in self.allowed_tools.split(",") if x.strip()}


settings = Settings()
