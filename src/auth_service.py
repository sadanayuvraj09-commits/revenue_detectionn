"""
Authentication service — real per-user accounts.

Adds:
  - users collection (email, hashed password, user_id)
  - signup / login issuing JWTs
  - get_current_user: FastAPI dependency that resolves the logged-in
    user from the Authorization: Bearer <token> header. Every route
    that should be scoped to "only this person's data" should depend
    on this instead of (or in addition to) verify_api_key.

user_id is a stable string (uuid4 hex) — never the raw email — so it's
safe to store on every downstream document (projects, commits,
timesheets, gaps, alerts, etc.) as the tenancy key.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import Header, HTTPException

from .config import get_settings
from .database import db

settings = get_settings()

ALGORITHM = "HS256"


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _create_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


async def signup(email: str, password: str) -> dict[str, Any]:
    email = email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required")
    if not password or len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = await db["users"].find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="An account with that email already exists")

    user_id = uuid.uuid4().hex
    doc = {
        "user_id": user_id,
        "email": email,
        "password_hash": _hash_password(password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db["users"].insert_one(doc)

    token = _create_token(user_id, email)
    return {"access_token": token, "token_type": "bearer", "user_id": user_id, "email": email}


async def login(email: str, password: str) -> dict[str, Any]:
    email = email.strip().lower()
    user = await db["users"].find_one({"email": email})
    if not user or not _verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _create_token(user["user_id"], user["email"])
    return {"access_token": token, "token_type": "bearer", "user_id": user["user_id"], "email": user["email"]}


async def get_current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """FastAPI dependency: resolves the caller's identity from a Bearer token.

    Raises 401 if the token is missing, malformed, expired, or invalid.
    Use as: current_user: dict = Depends(get_current_user)
    Then scope every DB read/write with {"user_id": current_user["user_id"]}.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header. Expected: Bearer <token>")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired, please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or corrupted token")

    user_id = payload.get("sub")
    email = payload.get("email")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return {"user_id": user_id, "email": email}