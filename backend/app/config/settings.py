from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    app_name: str = Field(default="AI Interview Analysis API")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    
    # Database - Supabase PostgreSQL (required)
    database_url: str = Field(..., description="Supabase PostgreSQL connection string")
    
    # Supabase Auth (for OAuth and user management)
    supabase_url: str = Field(default="https://example.supabase.co")
    supabase_anon_key: str = Field(default="your-anon-key")
    supabase_service_role_key: Optional[str] = Field(default=None)
    
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])
    
    log_level: str = Field(default="INFO")
    
    # Google OAuth
    google_client_id: Optional[str] = Field(default=None)
    google_client_secret: Optional[str] = Field(default=None)
    google_redirect_uri: str = Field(default="http://localhost:8000/api/v1/auth/callback/google")

    # jwt
    jwt_secret: str = Field(default="your-secret-key", description="Secret key for JWT tokens")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


if __name__ == "__main__":
    s = get_settings()
    print("--- Loaded Settings ---")
    print("Database URL:", s.database_url)
    print("Supabase URL:", s.supabase_url)
    print("Supabase Anon Key:", s.supabase_anon_key)
    print("Supabase Service Role Key:", s.supabase_service_role_key)
    print("Google Client ID:", s.google_client_id)
    print("Google Client Secret:", s.google_client_secret)
    print("JWT Secret:", s.jwt_secret)
    print("-----------------------")