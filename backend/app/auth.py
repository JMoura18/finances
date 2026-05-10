from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from app.config import get_settings


@dataclass(frozen=True)
class CurrentUser:
    id: uuid.UUID
    email: str
    firebase_uid: str
    is_dev: bool = False


# Stable dev user. Matches the seed script.
DEV_USER = CurrentUser(
    id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    email="dev@cofre.local",
    firebase_uid="dev-uid",
    is_dev=True,
)


def _verify_firebase_token(token: str) -> CurrentUser:
    """Verify a Firebase ID token. Returns a CurrentUser or raises 401."""
    try:
        from firebase_admin import auth as fb_auth
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="firebase-admin not installed",
        ) from e

    try:
        decoded = fb_auth.verify_id_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid firebase token: {e}",
        ) from e

    return CurrentUser(
        id=uuid.UUID(decoded.get("cofre_user_id", str(DEV_USER.id))),
        email=decoded.get("email", ""),
        firebase_uid=decoded["uid"],
    )


async def current_user(
    authorization: str | None = Header(default=None),
) -> CurrentUser:
    """FastAPI dependency.

    Behavior:
      - If Authorization: Bearer <token> is present and Firebase is configured,
        verify the token.
      - If env is dev and no token / no Firebase config, return DEV_USER.
      - Otherwise raise 401.
    """
    settings = get_settings()
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    firebase_configured = bool(settings.firebase_credentials_path)

    if not token:
        if settings.environment == "dev":
            return DEV_USER
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )

    if not firebase_configured:
        if settings.environment == "dev":
            return DEV_USER
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="firebase not configured",
        )

    return _verify_firebase_token(token)


CurrentUserDep = Depends(current_user)
