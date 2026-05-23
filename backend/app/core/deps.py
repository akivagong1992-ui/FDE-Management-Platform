from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/auth/login")


async def get_session(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[AsyncSession, None]:
    yield db


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload


def require_role(*allowed_roles: str):
    async def _checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _checker


def cockpit_guard(request: Request) -> None:
    allowed = {ip.strip() for ip in settings.COCKPIT_ALLOWED_IPS.split(",") if ip.strip()}
    client_ip = request.client.host if request.client else ""
    token = request.headers.get("X-Cockpit-Token") or request.query_params.get("token")

    if client_ip in allowed:
        return
    if token and token == settings.COCKPIT_TOKEN:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cockpit access denied")
