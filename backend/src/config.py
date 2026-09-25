"""Config centralizada. Diseñada para cuidar presupuesto de APIs ($20 inicial)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "FactoryMark API"
    debug: bool = False

    # APIs externas (cargar via .env, nunca commitear)
    google_places_api_key: str = ""
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # Neon Auth (login solo con Google, verificado por JWKS en src/auth.py)
    neon_auth_base_url: str = ""
    neon_auth_jwks_url: str = ""  # override opcional; por defecto base + /.well-known/jwks.json
    # Solo desarrollo local sin Neon: saltea la verificación (nunca en prod)
    auth_disabled: bool = False

    # Límites para no quemar cuota de Google Places
    max_competitors: int = 10
    max_reviews_per_place: int = 20
    places_cache_ttl_hours: int = 168  # 7 días: reutilizar todo lo posible
    places_language: str = "es"


settings = Settings()
