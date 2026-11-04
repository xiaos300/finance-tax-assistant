"""Lazy synchronous connection factory; no connection, DDL or seed on import."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import DatabaseSettings


def connection_factory(settings: DatabaseSettings):
    engine = create_engine(
        settings.database_url.get_secret_value(),
        pool_size=settings.db_pool_size, max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_seconds, pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"connect_timeout": settings.db_connect_timeout_seconds,
                      "options": f"-c search_path=harness,pg_catalog -c timezone=UTC -c lock_timeout={settings.db_lock_timeout_ms} -c statement_timeout={settings.db_statement_timeout_ms}"},
    )
    return engine, sessionmaker(bind=engine, expire_on_commit=False)
