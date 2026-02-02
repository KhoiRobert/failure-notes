from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List, Any
from dotenv import load_dotenv

# Load environment variables (no-op if .env missing, e.g. in Docker)
load_dotenv()

# Default CORS (used when CORS_ORIGINS env is not set; avoids env parsing issues in Docker)
_DEFAULT_CORS = "http://localhost:3000,http://localhost:3001,http://localhost:8000"

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/failure_notes",
        description="PostgreSQL connection URL",
    )

    # Server
    HOST: str = Field(default="0.0.0.0", description="Bind host")
    PORT: int = Field(default=8000, description="Bind port")
    DEBUG: bool = Field(default=True, description="Debug mode")

    # Admin (comma-separated emails; users with these emails can access admin APIs)
    ADMIN_EMAILS: str = Field(
        default="",
        description="Comma-separated admin emails for admin-only endpoints",
    )

    @property
    def admin_emails_set(self) -> set[str]:
        """Admin emails as a set for fast lookup"""
        if not self.ADMIN_EMAILS:
            return set()
        return {e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()}

    # Security
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production-min-32-chars-long",
        description="Secret key for signing",
    )
    JWT_SECRET_KEY: str = Field(
        default="dev-jwt-secret-key-change-in-production-min-32-chars",
        description="JWT signing key",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_HOURS: int = Field(default=24, description="Session expiry in hours")

    # CORS - comma-separated list of origins
    CORS_ORIGINS: str = Field(
        default=_DEFAULT_CORS,
        description="Comma-separated allowed origins",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def cors_origins_to_str(cls, v: Any) -> str:
        """Coerce to string so env values (e.g. with commas) always parse."""
        if v is None:
            return _DEFAULT_CORS
        return str(v).strip() or _DEFAULT_CORS

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # AI Service (for future use)
    AI_API_KEY: str = Field(default="", description="AI API key")
    AI_API_URL: str = Field(default="https://api.openai.com/v1", description="AI API base URL")
    AI_MODEL: str = Field(default="gpt-4", description="AI model name")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level")

    # Environment
    ENVIRONMENT: str = Field(default="development", description="development|production")

# Create settings instance
settings = Settings()
