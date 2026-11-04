"""Explicit root .env loading; database maintenance never constructs model settings."""
import os
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False, hide_input_in_errors=True)


class AppSettings(Settings):
    app_env: Literal["development", "test", "demo"]


class DatabaseSettings(Settings):
    database_url: SecretStr
    db_pool_size: int = Field(default=5, ge=1, le=20)
    db_max_overflow: int = Field(default=0, ge=0, le=20)
    db_pool_timeout_seconds: int = Field(default=5, ge=1, le=60)
    db_connect_timeout_seconds: int = Field(default=5, ge=1, le=60)
    db_lock_timeout_ms: int = Field(default=5000, ge=1, le=60000)
    db_statement_timeout_ms: int = Field(default=15000, ge=1, le=120000)

    @field_validator("database_url")
    @classmethod
    def postgres_only(cls, value: SecretStr) -> SecretStr:
        try:
            url = make_url(value.get_secret_value())
            valid = url.drivername == "postgresql+psycopg" and bool(url.host and url.database and url.username)
        except Exception:
            valid = False
        if not valid:
            raise ValueError("A PostgreSQL psycopg connection target is required")
        return value


class ModelSettings(Settings):
    app_env: Literal["development", "test", "demo"]
    model_mode: Literal["disabled", "live", "test_stub"] = "disabled"
    model_adapter: str
    model_base_url: str
    model_api_key: SecretStr
    model_id: str
    model_context_limit: int = Field(gt=0)
    max_input_tokens: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)

    @model_validator(mode="after")
    def budget_and_endpoint(self):
        if not self.model_base_url.startswith("https://"):
            raise ValueError("Live model endpoint must use HTTPS")
        if not all((self.model_adapter, self.model_id, self.model_api_key.get_secret_value())):
            raise ValueError("Live model configuration is incomplete")
        if self.max_input_tokens + self.max_output_tokens > self.model_context_limit:
            raise ValueError("Model token budget exceeds context limit")
        return self


class ModelModeSettings(Settings):
    app_env: Literal["development", "test", "demo"]
    model_mode: Literal["disabled", "live", "test_stub"] = "disabled"

    @model_validator(mode="after")
    def test_only(self):
        if self.model_mode == "test_stub" and self.app_env != "test":
            raise ValueError("test_stub requires APP_ENV=test")
        return self


def configuration() -> dict[str, str]:
    # Fixed project-root path, independent of the caller's working directory.
    return {k.lower(): v for k, v in {**dotenv_values(ROOT / ".env"), **os.environ}.items() if v is not None}


def database_settings(*, maintenance: bool = False) -> DatabaseSettings:
    values = configuration()
    if maintenance:
        # Never fall back from maintenance to the application role.
        values["database_url"] = values.get("migration_database_url", "")
    return DatabaseSettings(**values)


def model_settings() -> ModelModeSettings | ModelSettings:
    values = configuration()
    values.setdefault("model_mode", "live" if values.get("app_env") == "demo" else "disabled")
    mode = ModelModeSettings(**values)
    return ModelSettings(**values) if mode.model_mode == "live" else mode
