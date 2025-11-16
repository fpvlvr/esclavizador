"""
Security utilities for authentication and authorization.

Includes:
- Password hashing and verification (Argon2id via pwdlib)
- Password strength validation
- JWT token generation and validation
- Token hashing for database storage
"""

import re
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Tuple
import uuid

import jwt
from pwdlib import PasswordHash
from fastapi.security import HTTPBearer

from app.core.config import settings


# Password hashing using Argon2id (OWASP recommended, 2025)
# pwdlib.recommended() uses Argon2id with secure defaults:
# - Memory cost: 65536 KB (64 MB)
# - Time cost: 3 iterations
# - Parallelism: 4 threads
pwd_hash = PasswordHash.recommended()

# HTTP Bearer security scheme for JWT extraction
security = HTTPBearer()


# =============================================================================
# Password Hashing
# =============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using Argon2id.

    Argon2id is the OWASP-recommended algorithm for password hashing (2025).
    It's memory-hard and resistant to GPU/ASIC attacks, unlike bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password (Argon2id format)
    """
    return pwd_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Supports Argon2id hashes. pwdlib automatically handles algorithm
    detection and verification.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_hash.verify(plain_password, hashed_password)


# =============================================================================
# Password Validation
# =============================================================================

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets security requirements.

    Requirements:
    - Minimum 8 characters
    - Maximum 128 characters (reasonable security limit)
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        (is_valid, error_message) - error_message is empty string if valid
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if len(password) > 128:
        return False, "Password must be less than 128 characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
        return False, "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"

    return True, ""


# =============================================================================
# JWT Token Functions
# =============================================================================

def create_access_token(user_id: str, email: str, role: str, org_id: str) -> str:
    """
    Create JWT access token (30 min expiry).

    Claims:
        sub: user_id (UUID string)
        email: user email
        role: user role (boss/worker)
        org_id: organization_id (UUID string)
        exp: expiration timestamp
        iat: issued at timestamp

    Args:
        user_id: User UUID
        email: User email
        role: User role (boss/worker)
        org_id: Organization UUID

    Returns:
        JWT access token string
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "org_id": str(org_id),
        "exp": expire,
        "iat": now,
        "type": "access"
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: str) -> Tuple[str, str]:
    """
    Create JWT refresh token (7 days expiry).

    Claims:
        sub: user_id (UUID string)
        type: "refresh"
        exp: expiration timestamp
        iat: issued at timestamp
        jti: unique token ID (for DB storage)

    Args:
        user_id: User UUID

    Returns:
        (token, jti) - token string and unique identifier for DB storage
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    jti = str(uuid.uuid4())  # Unique token ID

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": now,
        "jti": jti,
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, jti


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        jwt.ExpiredSignatureError: Token expired
        jwt.InvalidTokenError: Token invalid or malformed
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


# =============================================================================
# Token Hashing for Storage
# =============================================================================

def hash_token(token: str) -> str:
    """
    Hash token using SHA-256 for database storage.

    We store hashed tokens instead of plaintext to prevent
    token leakage if the database is compromised.

    Args:
        token: Token string to hash

    Returns:
        SHA-256 hash (64 hex characters)
    """
    return hashlib.sha256(token.encode()).hexdigest()
