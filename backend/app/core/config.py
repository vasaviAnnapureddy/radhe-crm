"""Settings: read once from the .env file in the project root."""
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> project root is three folders up from "core"
ROOT_DIR = Path(__file__).resolve().parents[3]
CONFIG_DIR = ROOT_DIR / "config"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = ""
    environment: str = "development"
    log_level: str = "INFO"

    jwt_secret: str = ""
    jwt_expire_minutes: int = 480
    jwt_remember_days: int = 14
    cookie_secure: bool = False
    login_rate_limit_per_minute: int = 5

    admin_email: str = ""
    admin_password: str = ""
    admin_name: str = ""
    # One shared demo password for every employee and customer login. Empty = no portal logins are seeded.
    portal_password: str = ""
    # Easy-to-remember logins for the three story characters. Empty = they keep their generated email.
    portal_customer_email: str = ""  # Karthik Reddy, home owner
    portal_rm_email: str = ""        # Sneha Rao, relationship manager
    portal_sales_email: str = ""     # Arjun Varma, sales manager

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        """Neon gives 'postgresql://...'. SQLAlchemy needs to be told which driver to use."""
        value = value.strip().strip('"').strip("'")
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def load_config(file_name: str) -> dict:
    """Read one YAML file from the config folder, for example load_config("scoring.yaml")."""
    return yaml.safe_load((CONFIG_DIR / file_name).read_text(encoding="utf-8"))
