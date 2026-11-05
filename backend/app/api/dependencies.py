from fastapi import Request,Header,Depends
from app.core.config import configuration,database_settings
from app.core.identity import authenticate
from app.infrastructure.database.targets import test_settings
from app.infrastructure.database.engine import connection_factory
from app.infrastructure.database.unit_of_work import read_transactions
from app.modules.ledger.service import LedgerService
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer=HTTPBearer(auto_error=False)


def user_id(credentials:HTTPAuthorizationCredentials | None=Depends(bearer)):
    return authenticate('Bearer '+credentials.credentials if credentials and credentials.scheme.lower()=='bearer' else None)


def ledger_service(request:Request):
    if not hasattr(request.app.state,'ledger_service'):
        testing=configuration().get('app_env')=='test'
        settings=test_settings()[0] if testing else database_settings()
        engine,sessions=connection_factory(settings,testing=testing)
        # No persistent shared Session; engine creation is lazy and has no DB side effect.
        request.app.state.database_engine=engine
        request.app.state.ledger_service=LedgerService(read_transactions(sessions))
    return request.app.state.ledger_service
