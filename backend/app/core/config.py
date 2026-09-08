import os
from typing import List, Union, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FACTMESH"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Context-Aware Cross-Document Fact Knowledge Layer"
    
    # Environment & Host
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = ""

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Optional[str]) -> str:
        if not v or v.startswith("sqlite:///./"):
            # Resolve to absolute path at project root
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            db_name = v.replace("sqlite:///./", "") if v else "factmesh.db"
            db_path = os.path.join(root_dir, db_name)
            return f"sqlite:///{db_path}"
        return v
    
    # Queue
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS_QUEUE: bool = False
    
    # Storage
    STORAGE_DIR: str = "./data/storage"
    
    # LLM
    LLM_PROVIDER: str = "offline_heuristic"  # 'offline_heuristic', 'gemini', 'openai'
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://localhost:3000"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
