"""Application configuration settings."""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_NAME: str = "AI Business Intelligence & Financial Analysis Agent"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["*"]

    # Database
    DATABASE_PATH: Path = BASE_DIR / "data" / "business_bi.db"
    DATABASE_URL: str = Field(default=f"sqlite:///{BASE_DIR / 'data' / 'business_bi.db'}")
    DB_ECHO: bool = False
    SQL_MAX_ROWS: int = 1000
    SQL_EXECUTION_TIMEOUT_SECONDS: float = 5.0

    # LLM Settings
    # Provider options: 'gemini', 'openai', 'anthropic', 'mock'
    LLM_PROVIDER: str = "mock"
    LLM_MODEL_NAME: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2048

    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # MCP Server
    MCP_SERVER_NAME: str = "business-intelligence-mcp"
    MCP_HOST: str = "127.0.0.1"
    MCP_PORT: int = 8001

    @property
    def effective_llm_provider(self) -> str:
        """Auto-detect provider if explicit provider is not functional without key."""
        if self.GEMINI_API_KEY or self.GOOGLE_API_KEY:
            if self.LLM_PROVIDER in ["gemini", "google", "auto"]:
                return "gemini"
        if self.OPENAI_API_KEY and self.OPENAI_API_KEY not in ["", "your_openai_api_key_here"]:
            if self.LLM_PROVIDER in ["openai", "auto"]:
                return "openai"
        if self.ANTHROPIC_API_KEY and self.ANTHROPIC_API_KEY not in ["", "your_anthropic_api_key_here"]:
            return "anthropic"
        if self.LLM_PROVIDER != "mock" and not (self.OPENAI_API_KEY or self.GEMINI_API_KEY or self.GOOGLE_API_KEY):
            # Graceful fallback to deterministic mock engine
            return "mock"
        return self.LLM_PROVIDER


settings = Settings()
