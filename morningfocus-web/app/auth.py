"""Auth dependency — verifies Supabase JWT on every protected API call."""

from __future__ import annotations

import os
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# auto_error=False so we can handle missing tokens ourselves in local mode
_bearer = HTTPBearer(auto_error=False)

# Returned as the current user when Supabase is not configured (local mode)
_LOCAL_USER = {"id": "local", "email": "local@localhost"}


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency.  Add  `_: dict = Depends(require_auth)`  to any route
    you want to protect.  Raises 401 if the token is missing or invalid.

    When SUPABASE_URL / SUPABASE_ANON_KEY are not set the app runs in
    local (no-auth) mode and every request is treated as the local user.
    """
    supabase_url = os.environ.get("SUPABASE_URL", "")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")

    # ── Local mode (no Supabase configured) ────────────────────────────────
    if not supabase_url or not anon_key:
        return _LOCAL_USER

    # ── Supabase mode ───────────────────────────────────────────────────────
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    resp = httpx.get(
        f"{supabase_url}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {credentials.credentials}",
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
