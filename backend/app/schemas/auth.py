"""
Authentication Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict

from app.models.user import UserRole
from app.core.security import validate_password_strength


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(
        min_length=8,
        max_length=128,
        description="User password (8-128 chars, uppercase, lowercase, digit, special char required)"
    )
    role: UserRole = Field(description="User role (master or slave)")
    organization_name: str = Field(
        min_length=2,
        max_length=255,
        description="Organization name (creates new org, errors if name exists)"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

    @field_validator("organization_name")
    @classmethod
    def validate_org_name(cls, v: str) -> str:
        """Validate and normalize organization name."""
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "role": "slave",
                "organization_name": "Acme Corp"
            }
        }
    )


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }
    )


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str = Field(description="JWT access token (30 min expiry)")
    refresh_token: str = Field(description="JWT refresh token (7 days expiry)")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Access token expiration time in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }
    )


class RefreshRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str = Field(description="JWT refresh token")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )


class RefreshResponse(BaseModel):
    """Refresh token response (new access token only)."""

    access_token: str = Field(description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Access token expiration time in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }
    )
