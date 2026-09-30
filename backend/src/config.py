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

    # Neon Postgres (negocio del dueño, ver backend/schema.sql)
    database_url: str = ""

    # Límites para no quemar cuota de Google Places
    max_competitors: int = 10
    max_reviews_per_place: int = 20
    places_cache_ttl_hours: int = 168  # 7 días: reutilizar todo lo posible
    places_language: str = "es"
    # Radio de búsqueda por proximidad (modo local), en metros
    search_radius_m: int = 1000

    # Tavily (señales web; primario en modo online/mixto, opcional en local)
    tavily_api_key: str = ""
    tavily_enabled: bool = False  # enrichment extra en modo local
    tavily_max_queries: int = 3
    tavily_max_results: int = 5
    tavily_cache_ttl_hours: int = 168

    # Instagram-Login v1 (conectar + leer perfil; publicar = milestone post-App-Review)
    instagram_client_id: str = ""
    instagram_client_secret: str = ""
    instagram_redirect_uri: str = ""
    token_encryption_key: str = ""  # Fernet; persistencia cifrada con tabla de negocios


settings = Settings()
