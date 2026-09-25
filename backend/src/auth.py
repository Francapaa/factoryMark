"""Autenticación con Neon Auth (login solo con Google).

El frontend (Next.js + Neon Auth SDK) obtiene un JWT corto (EdDSA, 15 min)
con `authClient.token()` y lo envía como `Authorization: Bearer <jwt>`.
Acá solo verificamos firma + issuer + expiración contra el JWKS público.
Los usuarios viven en el schema `neon_auth` de Neon Postgres: no hay
tabla propia en esta fase.
"""

from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import settings

bearer_scheme = HTTPBearer(auto_error=False)

_jwks_clients: dict[str, jwt.PyJWKClient] = {}


@dataclass
class CurrentUser:
    id: str
    email: str | None = None
    name: str | None = None
    picture: str | None = None


def get_jwks_url() -> str:
    """URL del JWKS. Si no hay override, se deriva del base URL de Neon Auth."""
    if settings.neon_auth_jwks_url:
        return settings.neon_auth_jwks_url
    return f"{settings.neon_auth_base_url.rstrip('/')}/.well-known/jwks.json"


def _get_jwks_client() -> jwt.PyJWKClient:
    url = get_jwks_url()
    client = _jwks_clients.get(url)
    if client is None:
        client = jwt.PyJWKClient(url, cache_keys=True)
        _jwks_clients[url] = client
    return client


def verify_neon_jwt(token: str) -> CurrentUser:
    """Verifica firma EdDSA, issuer y expiración. Lanza 401/503 si falla."""
    if not settings.neon_auth_base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth no configurada: falta NEON_AUTH_BASE_URL",
        )
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["EdDSA"],
            options={"require": ["exp", "iss", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada, volvé a ingresar",
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        ) from None
    issuer = str(payload.get("iss", "")).rstrip("/")
    expected = settings.neon_auth_base_url.rstrip("/")
    if issuer != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de otro emisor",
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin usuario",
        )
    return CurrentUser(
        id=str(sub),
        email=payload.get("email"),
        name=payload.get("name"),
        picture=payload.get("picture"),
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser:
    """Dependencia FastAPI: exige Bearer JWT válido, salvo AUTH_DISABLED=true (solo dev)."""
    if settings.auth_disabled:
        return CurrentUser(
            id="dev-user",
            email="dev@factorymark.local",
            name="Dev",
        )
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token de autenticación",
        )
    return verify_neon_jwt(credentials.credentials)
