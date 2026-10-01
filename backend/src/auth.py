"""Autenticación con Neon Auth (login solo con Google).

El frontend (Next.js + Neon Auth SDK) obtiene un JWT corto (EdDSA, 15 min)
con `authClient.token()` y lo envía como `Authorization: Bearer <jwt>`.
Acá solo verificamos firma + issuer + expiración contra el JWKS público.
Los usuarios viven en el schema `neon_auth` de Neon Postgres: no hay
tabla propia en esta fase.
"""

import base64
import logging
from dataclasses import dataclass
from typing import Annotated
from urllib.parse import urlparse

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import settings

logger = logging.getLogger("auth")

bearer_scheme = HTTPBearer(auto_error=False)

_jwks_clients: dict[str, jwt.PyJWKClient] = {}


def _token_summary(token: str) -> dict:
    """TEMPORAL debug: forma del token sin exponer el secreto (opción A)."""
    return {
        "len": len(token),
        "segments": token.count(".") + 1 if token else 0,
        "prefix10": token[:10] if token else "",
        "is_jwt_shape": token.count(".") == 2 and len(token) > 100,
    }


def _unverified_claims(token: str) -> dict:
    """TEMPORAL debug: claims sin verificar firma (iss/sub/exp/alg). Nunca valida."""
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return {
            "iss": decoded.get("iss"),
            "aud": decoded.get("aud"),
            "sub_present": bool(decoded.get("sub")),
            "exp": decoded.get("exp"),
            "iat": decoded.get("iat"),
        }
    except Exception as exc:  # noqa: BLE001 - solo para debug
        return {"decode_error": type(exc).__name__}


def _unverified_header(token: str) -> dict:
    """TEMPORAL debug: alg/kid del header sin verificar."""
    try:
        return {
            k: jwt.get_unverified_header(token).get(k)
            for k in ("alg", "kid", "typ")
        }
    except Exception as exc:  # noqa: BLE001 - solo para debug
        return {"header_error": type(exc).__name__}


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


def _origin(url: str) -> str:
    """Origen scheme://netloc. Neon emite iss/aud como origen aunque el base tenga path."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _expected_issuers() -> set[str]:
    """Issuers aceptados: base completa y origen. Cubre /neondb/auth con iss=origen."""
    base = settings.neon_auth_base_url.rstrip("/")
    if not base:
        return set()
    return {base, _origin(base)}


def _get_jwks_client() -> jwt.PyJWKClient:
    url = get_jwks_url()
    client = _jwks_clients.get(url)
    if client is None:
        client = jwt.PyJWKClient(url, cache_keys=True)
        _jwks_clients[url] = client
    return client


_jwks_json_cache: dict[str, dict] = {}


def _fetch_jwks_json(url: str) -> dict:
    """Fallback sync para OKP/Ed25519 cuando PyJWKClient no mastica la key."""
    cached = _jwks_json_cache.get(url)
    if cached is not None:
        return cached
    resp = httpx.get(url, timeout=10.0)
    resp.raise_for_status()
    data = resp.json()
    _jwks_json_cache[url] = data
    return data


def _ed25519_key_from_jwks(token: str, jwks: dict):
    """Resuelve la pública Ed25519 por kid (como el middleware que sí andaba)."""
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    for jwk in jwks.get("keys", []):
        if jwk.get("kid") == kid:
            x_value = jwk["x"]
            padding = "=" * ((4 - len(x_value) % 4) % 4)
            raw = base64.urlsafe_b64decode(x_value + padding)
            return Ed25519PublicKey.from_public_bytes(raw)
    raise ValueError("No signing key found for token kid")


def _decode_verified(token: str, key) -> dict:
    """Verifica firma + exp. iss/aud se validan manual contra el set permitido."""
    return jwt.decode(
        token,
        key,
        algorithms=["EdDSA"],
        options={"require": ["exp", "iss", "sub"], "verify_aud": False, "verify_iss": False},
    )


def verify_neon_jwt(token: str) -> CurrentUser:
    """Verifica firma EdDSA, issuer y expiración. Lanza 401/503 si falla."""
    # TEMPORAL debug opción A: qué llega como token (nunca el token completo).
    logger.debug(
        "[auth] verify start jwks_url=%s expected=%s token=%s claims=%s header=%s",
        get_jwks_url() if settings.neon_auth_base_url else "<sin-base-url>",
        sorted(_expected_issuers()),
        _token_summary(token),
        _unverified_claims(token),
        _unverified_header(token),
    )
    if not settings.neon_auth_base_url:
        logger.debug("[auth] 503 sin base_url")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth no configurada: falta NEON_AUTH_BASE_URL",
        )
    try:
        try:
            signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
            payload = _decode_verified(token, signing_key.key)
        except jwt.ExpiredSignatureError:
            raise
        except Exception as first_exc:
            # Sin forma JWT no hay nada que buscar en red (tests sin red + opacos).
            if token.count(".") != 2:
                raise jwt.InvalidTokenError("Token sin forma JWT") from first_exc
            logger.debug(
                "[auth] PyJWKClient falló (%s), reintento manual Ed25519",
                type(first_exc).__name__,
            )
            jwks = _fetch_jwks_json(get_jwks_url())
            payload = _decode_verified(token, _ed25519_key_from_jwks(token, jwks))
    except jwt.ExpiredSignatureError:
        logger.debug(
            "[auth] 401 expirado claims=%s", _unverified_claims(token)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada, volvé a ingresar",
        ) from None
    except (jwt.InvalidTokenError, ValueError, KeyError, httpx.HTTPError, OSError) as exc:
        logger.debug(
            "[auth] 401 inválido exc=%s token=%s claims=%s",
            type(exc).__name__,
            _token_summary(token),
            _unverified_claims(token),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        ) from None
    issuer = str(payload.get("iss", "")).rstrip("/")
    allowed = _expected_issuers()
    if issuer not in allowed:
        logger.debug("[auth] 401 otro emisor iss=%s allowed=%s", issuer, sorted(allowed))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de otro emisor",
        )
    aud = payload.get("aud")
    if aud is not None:
        auds = [aud] if isinstance(aud, str) else list(aud)
        if not any(str(a).rstrip("/") in allowed for a in auds):
            logger.debug("[auth] 401 audiencia inválida aud=%s allowed=%s", auds, sorted(allowed))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de otro emisor",
            )
    sub = payload.get("sub")
    if not sub:
        logger.debug("[auth] 401 sin sub")
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
        logger.debug("[auth] 401 sin credentials scheme=%s", getattr(credentials, "scheme", None))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token de autenticación",
        )
    token = credentials.credentials
    logger.debug(
        "[auth] bearer scheme=%s token=%s",
        credentials.scheme,
        _token_summary(token),
    )
    return verify_neon_jwt(token)
