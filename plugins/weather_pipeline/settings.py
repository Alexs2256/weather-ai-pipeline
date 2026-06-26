from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
print(f"Looking for .env at: {BASE_DIR / '.env'}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    db_host: str
    db_name: str
    db_user: str
    db_password: str
    db_port: int = 5432
    gemini_key: str
    api_key: str

settings = Settings()