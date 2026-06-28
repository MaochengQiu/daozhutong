from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "wechat-system"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    wechat_token: str = Field(default="replace_with_wechat_token")
    wechat_score_keyword: str = "查成绩"
    score_page_url: str = "http://localhost:8000/static/score.html?v=20260628-idcard4"

    ai_enabled: bool = True
    ai_api_key: str = ""
    ai_api_base: str = "https://api.deepseek.com"
    ai_chat_model: str = "deepseek-chat"
    ai_timeout_sec: int = 20

    tencent_secret_id: str = ""
    tencent_secret_key: str = ""
    tencent_region: str = "ap-guangzhou"
    tencent_embedding_endpoint: str = "hunyuan.tencentcloudapi.com"

    docs_path: str = str(BASE_DIR / "docs" / "faq.txt")

    qa_vector_enabled: bool = True
    qa_chunk_size: int = 500
    qa_chunk_overlap: int = 100
    qa_retrieval_top_k: int = 5

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "wechat_qa_docs"

    database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'app.db').as_posix()}"
    score_rate_limit_per_minute: int = 20


@lru_cache()
def get_settings() -> Settings:
    return Settings()
