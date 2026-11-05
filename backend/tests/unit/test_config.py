"""TC051 D0 configuration subset / TC061; no database or model network."""
import os
import subprocess
import sys

import pytest
from pydantic import ValidationError

from app.core.config import DatabaseSettings, ModelModeSettings, database_settings, model_settings
from app.infrastructure.database.engine import connection_factory


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch):
    for key in list(os.environ):
        if key.startswith(("MODEL_", "MAX_INPUT", "MAX_OUTPUT")) or key in {"APP_ENV", "DATABASE_URL", "MIGRATION_DATABASE_URL"}:
            monkeypatch.delenv(key)
    monkeypatch.setenv("APP_ENV", "test")


def test_TC051_database_without_model(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://finance_tax_app@127.0.0.1/finance_tax_test")
    settings = database_settings()
    engine, sessions = connection_factory(settings,testing=True)
    assert engine.dialect.driver == "psycopg"
    assert sessions.kw["bind"] is engine
    engine.dispose()
    assert "finance_tax_app@" not in repr(settings)


def test_TC051_maintenance_does_not_import_model(monkeypatch):
    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql+psycopg://finance_tax_migrator@127.0.0.1/finance_tax_dev")
    # Deliberately invalid model configuration cannot block a database command.
    monkeypatch.setenv("MODEL_MODE", "invalid")
    result = subprocess.run([sys.executable, "-m", "app.cli", "inspect-config", "--maintenance"], capture_output=True, text=True,encoding='utf-8')
    assert result.returncode == 0
    assert "model settings not loaded" in result.stdout


def test_TC061_maintenance_never_falls_back(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://fixture@127.0.0.1/harness_test_d0")
    with pytest.raises(ValidationError):
        database_settings(maintenance=True)


@pytest.mark.parametrize("env", ["development", "demo"])
def test_TC051_stub_rejected_outside_test(env):
    with pytest.raises(ValidationError):
        ModelModeSettings(app_env=env, model_mode="test_stub")


def test_TC051_stub_only_test():
    assert ModelModeSettings(app_env="test", model_mode="test_stub").model_mode == "test_stub"


def test_TC061_disabled_ignores_blank_live_fields(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "disabled")
    monkeypatch.setenv("MODEL_CONTEXT_LIMIT", "")
    monkeypatch.setenv("MAX_INPUT_TOKENS", "")
    assert model_settings().model_mode == "disabled"


def test_TC061_live_requires_configuration(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "live")
    with pytest.raises(ValidationError):
        model_settings()


@pytest.mark.parametrize("url", ["sqlite:///local.db", "postgresql://fixture@localhost/test", "invalid", ""])
def test_TC061_only_psycopg_postgres(url):
    with pytest.raises(ValidationError):
        DatabaseSettings(database_url=url)


def test_TC061_secret_validation_error_is_redacted():
    marker = "D0_SYNTHETIC_SECRET"
    with pytest.raises(ValidationError) as caught:
        DatabaseSettings(database_url=f"wrong://fixture:{marker}@localhost/db")
    assert marker not in str(caught.value)
