from typing import Any, List

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    version: str = "0.1.0"
    log_level: str = "INFO"
    cors_allow_origins: List[str] = ["http://localhost:3000"]
    db_url: str = "sqlite:///./tanik.db"
    iris_match_threshold: float = 0.37
    fingerprint_match_threshold: float = 40.0
    max_upload_bytes: int = 10 * 1024 * 1024

    class Config:
        env_prefix = "TANIK_"
        env_file = ".env"
        case_sensitive = False

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            # Pydantic v1 BaseSettings tries `json.loads` on complex-typed env
            # vars before any validator runs. CORS_ALLOW_ORIGINS is documented
            # as comma-separated, not JSON, so short-circuit it and let the
            # validator below split. All other fields go through the default
            # parser (which is the right behavior for ints, floats, and
            # plain strings).
            if field_name == "cors_allow_origins":
                return raw_val
            return cls.json_loads(raw_val)

    @validator("cors_allow_origins", pre=True)
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


settings = Settings()
