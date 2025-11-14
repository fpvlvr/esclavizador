"""
Application configuration settings.
Uses Pydantic Settings for environment variable management.
"""

from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Esclavizador", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="Allowed hosts"
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # Database
    database_url: str = Field(
        default="postgres://esclavizador:dev_password@localhost:5432/esclavizador",
        description="PostgreSQL database URL (use postgres:// scheme for Tortoise ORM)"
    )

    # JWT Configuration
    secret_key: str = Field(
        ...,  # Required field
        min_length=32,
        description="Secret key for JWT token generation (min 32 chars)"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle JSON string or comma-separated values
            if v.startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: str | List[str]) -> List[str]:
        """Parse allowed hosts from string or list."""
        if isinstance(v, str):
            if v.startswith("["):
                import json
                return json.loads(v)
            return [host.strip() for host in v.split(",")]
        return v

    @property
    def tortoise_orm_config(self) -> dict:
        """
        Generate Tortoise ORM configuration.

        Returns:
            dict: Tortoise ORM configuration dictionary
        """
        return {
            "connections": {
                "default": self.database_url
            },
            "apps": {
                "models": {
                    "models": [
                        "app.models.organization",
                        "app.models.user",
                        "app.models.project",
                        "app.models.task",
                        "app.models.time_entry",
                        "app.models.tag",
                        "aerich.models",
                    ],
                    "default_connection": "default",
                }
            },
            "use_tz": True,
            "timezone": "UTC",
        }


# Global settings instance
settings = Settings()
