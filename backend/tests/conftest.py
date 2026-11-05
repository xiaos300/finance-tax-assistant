"""Real PostgreSQL fixtures only. Missing connection means blocked, never fallback."""
import pytest
from app.core.config import configuration
from app.infrastructure.database.targets import test_settings,TargetError
from app.infrastructure.database.engine import connection_factory
from app.infrastructure.database.maintenance import reset_test,migrate,grant_runtime
from app.infrastructure.database.seed import seed
from app.infrastructure.database.unit_of_work import read_transactions
from app.modules.ledger.service import LedgerService


@pytest.fixture
def pg():
    v=configuration()
    if not v.get('test_database_url') or not v.get('test_migration_database_url'):
        pytest.skip('blocked: explicit PostgreSQL test credentials unavailable')
    try:a,m=test_settings(v)
    except TargetError:pytest.fail('Test protection rejected the configured target; no fallback',pytrace=False)
    app,sessions=connection_factory(a,testing=True)
    maintenance,_=connection_factory(m,maintenance=True,testing=True)
    try:
        # Both authenticated identities must succeed before any schema mutation.
        with app.connect():pass
        with maintenance.connect():pass
    except Exception:
        app.dispose();maintenance.dispose()
        pytest.fail('PostgreSQL authentication/target guard failed; no reset executed',pytrace=False)
    try:
        reset_test(maintenance)
        migrate(maintenance)
        with maintenance.begin() as c:seed(c)
        with maintenance.begin() as c:grant_runtime(c)
        yield app,maintenance,LedgerService(read_transactions(sessions))
    finally:
        app.dispose();maintenance.dispose()
