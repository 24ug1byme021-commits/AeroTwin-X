"""
AeroTwin-X backend configuration.

All runtime-tunable values live here, loaded from environment variables
(with sane defaults for local development). Nothing engineering-specific
(physics constants, thresholds) belongs here — see physics/ and health/
for those; this is deployment/runtime config only.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AeroTwin-X"
    environment: str = "development"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Comma-separated origins allowed to call the API (Vite dev server by default).
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # SQLite path for storing telemetry history / simulation runs.
    database_url: str = "sqlite:///./data/synthetic/aerotwinx.db"

    # Telemetry simulation
    telemetry_tick_seconds: float = 1.0
    telemetry_history_max_frames: int = 3600  # 1 hour at 1Hz

    # Optional LLM for the natural-language mission parser.
    # If no key is provided, a deterministic rule-based parser is used instead
    # (see mission/ nl parsing) — the app must work fully offline.
    llm_api_key: str | None = None
    llm_enabled: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
