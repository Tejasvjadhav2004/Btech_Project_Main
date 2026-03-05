from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # ── PostgreSQL ────────────────────────────────────────────────────────────
    # NEVER hardcode credentials here. Set these in your .env file.
    DATABASE_URL: str = ""

    # ── LangChain / OpenAI ────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL:   str = "gpt-3.5-turbo"

    # ── API Security ──────────────────────────────────────────────────────────
    # Comma-separated list of valid API keys for accessing this service.
    # You generate these keys and give one to each team member.
    # Example in .env:  APP_API_KEYS=key-alice-abc123,key-bob-xyz789
    APP_API_KEYS: str = ""

    @property
    def allowed_api_keys(self) -> List[str]:
        """Returns list of valid API keys from the comma-separated env variable."""
        return [k.strip() for k in self.APP_API_KEYS.split(",") if k.strip()]

    class Config:
        env_file = ".env"

settings = Settings()
