"""Lazy synchronous connection factory; no connection, DDL or seed on import."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import DatabaseSettings, configuration
from app.infrastructure.database.targets import parse_target, verify_authenticated, TargetError


def connection_factory(settings: DatabaseSettings, *, maintenance=False, testing=False):
    values=configuration()
    if testing and (values.get('app_env')!='test' or values.get('pytest_xdist_worker')):
        raise TargetError('Serial APP_ENV=test is required for test connections.')
    if not testing and values.get('app_env')=='test':
        raise TargetError('APP_ENV=test requires an explicit test connection factory.')
    url, target = parse_target(settings.database_url.get_secret_value(), maintenance=maintenance, testing=testing)
    engine = create_engine(
        url,
        pool_size=settings.db_pool_size, max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_seconds, pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"connect_timeout": settings.db_connect_timeout_seconds, "hostaddr": target.host,
                      "options": f"-c search_path=harness,pg_catalog -c timezone=UTC -c lock_timeout={settings.db_lock_timeout_ms} -c statement_timeout={settings.db_statement_timeout_ms}"},
    )
    @event.listens_for(engine, 'checkout')
    def verify_connection(dbapi_connection, connection_record, connection_proxy):
        with dbapi_connection.cursor() as cursor:
            verify_authenticated(cursor, target)
        dbapi_connection.rollback()
    return engine, sessionmaker(bind=engine, expire_on_commit=False)
