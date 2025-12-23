"""Authentication and authorization utilities."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings

security = HTTPBearer(auto_error=False)


async def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """Get current admin user (basic auth for MVP)."""
    settings = get_settings()

    # For MVP: simple token-based auth
    # In production: use proper JWT/OAuth2
    admin_token = getattr(settings, "admin_token", None)

    if not admin_token:
        # If no token configured, allow access (for development)
        return "admin_user"

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication credentials",
        )

    return "admin_user"


def require_admin():
    """Dependency to require admin authentication."""
    return Depends(get_current_admin)

