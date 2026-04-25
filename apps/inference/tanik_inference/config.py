from typing import List

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    version: str = "0.1.0"
    log_level: str = "INFO"
    cors_allow_origins: List[str] = ["http://localhost:3000"]
    db_url: str = "sqlite:///./tanik.db"
    iris_match_threshold: float = 0.37
    max_upload_bytes: int = 10 * 1024 * 1024

    class Config:
        env_prefix = "TANIK_"
        env_file = ".env"
        case_sensitive = False

    @validator("cors_allow_origins", pre=True)
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


settings = Settings()
