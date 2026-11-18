from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./crm.db"
    secret_key: str = "change-me"
    # Okta OIDC
    okta_issuer: str = ""  # e.g. https://your-org.okta.com/oauth2/default
    okta_client_id: str = ""
    okta_client_secret: str = ""
    base_url: str = "http://localhost:8000"
    # Local development only: enables /api/auth/dev-login
    dev_auth: bool = False
    # No login at all: every request acts as a local admin. Turn off once Okta is configured.
    auth_disabled: bool = False
    static_dir: str = "static"

    @field_validator("database_url")
    @classmethod
    def _driver(cls, v: str) -> str:
        # Hosts hand out postgres:// or postgresql://; SQLAlchemy needs the psycopg driver named.
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix):]
        return v

    def validate_for_startup(self) -> None:
        """Fail fast on an unsafe configuration instead of serving an open app."""
        if self.auth_disabled or self.dev_auth:
            return
        missing = [n for n in ("okta_issuer", "okta_client_id", "okta_client_secret") if not getattr(self, n)]
        if missing:
            raise RuntimeError(f"Okta is not configured (missing {', '.join(m.upper() for m in missing)}). "
                               "Set them, or set AUTH_DISABLED=true for a private/local run.")
        if self.secret_key == "change-me":
            raise RuntimeError("SECRET_KEY must be set to a long random value.")


settings = Settings()
