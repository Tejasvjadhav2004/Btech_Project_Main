"""
API Key Security
-----------------
FastAPI dependency that validates the X-API-Key header on every protected request.

How it works:
 1. You generate API keys (random strings) and store them in APP_API_KEYS in .env
 2. Each team member gets ONE key from you
 3. They must pass it as:   X-API-Key: <their-key>  in every request
 4. If the key is missing or wrong → 403 Forbidden
 5. To revoke access: remove their key from APP_API_KEYS in .env and restart server

Security is DISABLED if APP_API_KEYS is empty in .env (open access — for local dev).
"""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    """
    FastAPI dependency — attach to any router or individual route.

    Usage in routes:
        from api.security import verify_api_key
        router = APIRouter(dependencies=[Depends(verify_api_key)])
    """
    allowed = settings.allowed_api_keys

    # If no keys configured, allow open access (local development)
    if not allowed:
        return "open-access"

    if not api_key or api_key not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key. Contact the project admin for access.",
        )
    return api_key
