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


settings = Settings()
