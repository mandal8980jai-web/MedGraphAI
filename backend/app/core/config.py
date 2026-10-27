from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-3.5-flash-lite"
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./medigraph.db"
    UPLOAD_DIR: str = "../storage/uploads"
    REPORT_DIR: str = "../storage/reports"
    MAX_UPLOAD_MB: int = 15
    RETENTION_DAYS: int = 7
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    CORS_ORIGIN_REGEX: str = r"https://.*\.vercel\.app"
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origins(self) -> list[str]:
        origins = set()
        raw = self.FRONTEND_ORIGIN.strip() if self.FRONTEND_ORIGIN else ""
        if raw:
            for item in raw.split(","):
                cleaned = item.strip().rstrip("/")
                if cleaned:
                    origins.add(cleaned)
        # Always allow standard local dev origins
        origins.add("http://localhost:5173")
        origins.add("http://127.0.0.1:5173")
        origins.add("http://localhost:3000")
        origins.add("http://127.0.0.1:3000")
        return list(origins)

    @property
    def is_llm_key_configured(self) -> bool:
        if not self.LLM_API_KEY:
            return False
        key = self.LLM_API_KEY.strip()
        placeholders = {
            "put_your_gemini_key_here",
            "your_gemini_key_here",
            "put_your_provider_key_here",
            "your-provider-key-here",
            "placeholder",
            "none"
        }
        if key.lower() in placeholders or len(key) < 8:
            return False
        return True

    @property
    def sqlite_db_path(self) -> Path:
        db_url = self.DATABASE_URL
        if db_url.startswith("sqlite:///"):
            raw_path = db_url.replace("sqlite:///", "")
            path = Path(raw_path)
            if not path.is_absolute():
                backend_dir = Path(__file__).resolve().parent.parent.parent
                return (backend_dir / path).resolve()
            return path.resolve()
        return (Path(__file__).resolve().parent.parent.parent / "medigraph.db").resolve()

    @property
    def upload_path(self) -> Path:
        backend_dir = Path(__file__).resolve().parent.parent.parent
        p = Path(self.UPLOAD_DIR)
        if not p.is_absolute():
            return (backend_dir / p).resolve()
        return p.resolve()

    @property
    def report_path(self) -> Path:
        backend_dir = Path(__file__).resolve().parent.parent.parent
        p = Path(self.REPORT_DIR)
        if not p.is_absolute():
            return (backend_dir / p).resolve()
        return p.resolve()


settings = Settings()
