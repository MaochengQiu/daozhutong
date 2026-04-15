from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "wechat-system"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    wechat_token: str = Field(default="replace_with_wechat_token")
    wechat_score_keyword: str = "查成绩"
    score_page_url: str = "http://localhost:8000/static/score.html"

    ai_enabled: bool = True
    ai_api_key: str = "sk-caed026245774ba390d1f738aad2e3c5"
    ai_api_base: str = "https://api.deepseek.com"
    ai_chat_model: str = "deepseek-chat"
    ai_timeout_sec: int = 20

    docs_path: str = str(BASE_DIR / "docs" / "faq.txt")

    database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'app.db').as_posix()}"
    score_rate_limit_per_minute: int = 20


@lru_cache()
def get_settings() -> Settings:
    return Settings()
