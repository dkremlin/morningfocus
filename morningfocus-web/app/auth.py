"""Auth dependency — verifies Supabase JWT on every protected API call."""

from __future__ import annotations

import os

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer()


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency.  Add  `_: dict = Depends(require_auth)`  to any route
    you want to protect.  Raises 401 if the token is missing or invalid.
    """
    token = credentials.credentials
    supabase_url = os.environ.get("SUPABASE_URL", "")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")

    if not supabase_url or not anon_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth is not configured on this server (missing SUPABASE_URL / SUPABASE_ANON_KEY).",
        )

    resp = httpx.get(
        f"{supabase_url}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": anon_key,
        },
        timeout=5,
    )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return resp.json()  # contains user id, email, etc.
