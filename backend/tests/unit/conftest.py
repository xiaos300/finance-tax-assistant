"""Unit tests must not consume an operator's real root .env or credentials."""
import os
import pytest
from app.core import config


@pytest.fixture(autouse=True)
def isolated_unit_configuration(monkeypatch):
    monkeypatch.setattr(config,'dotenv_values',lambda path:{})
    keys={'DATABASE_URL','MIGRATION_DATABASE_URL','TEST_DATABASE_URL','TEST_MIGRATION_DATABASE_URL',
          'ADMIN_DATABASE_URL','DEMO_U001_TOKEN','DEMO_U002_TOKEN','APP_ENV'}
    for key in list(os.environ):
        if key.upper() in keys or key.upper().startswith(('MODEL_','MAX_INPUT','MAX_OUTPUT')):
            monkeypatch.delenv(key)
    monkeypatch.setenv('APP_ENV','test')
    monkeypatch.setenv('MODEL_MODE','disabled')
