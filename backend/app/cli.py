"""Guarded maintenance CLI. Never print configuration, DBAPI exceptions or secrets."""
import argparse
import json

from pydantic import ValidationError

from app.core.config import database_settings, configuration
from app.infrastructure.database.targets import test_settings, TargetError, parse_target
from app.infrastructure.database.engine import connection_factory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["inspect-config","inspect-admin","bootstrap-test","bootstrap-dev","prepare-existing-test","prepare-existing-dev","migrate","seed","grant-runtime","inspect","reset-test"])
    parser.add_argument("--maintenance", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument('--test-acceptance')
    parser.add_argument('--approval-ref')
    args = parser.parse_args()
    try:
        if args.action in ('prepare-existing-test','prepare-existing-dev'):
            from app.infrastructure.database.preparation import prepare_existing
            result=prepare_existing(configuration(),testing=args.action=='prepare-existing-test',approval_ref=args.approval_ref,acceptance=args.test_acceptance)
            print(json.dumps(result,ensure_ascii=False))
            return 0
        if args.action in ('inspect-admin','bootstrap-test','bootstrap-dev'):
            from app.infrastructure.database.bootstrap import inspect_admin, bootstrap
            result=inspect_admin(configuration()) if args.action=='inspect-admin' else bootstrap(configuration(),development=args.action=='bootstrap-dev',acceptance=args.test_acceptance)
            print(json.dumps(result,ensure_ascii=False))
            return 0
        settings = test_settings()[1] if args.test else database_settings(maintenance=args.maintenance or args.action!='inspect-config')
        if args.action=='inspect-config':
            parse_target(settings.database_url.get_secret_value(),maintenance=args.maintenance,testing=args.test)
            print("Database configuration valid; no connection attempted; model settings not loaded.")
            return 0
        if args.action=='reset-test' and not args.test:raise TargetError('Reset requires explicit test mode')
        from app.infrastructure.database.maintenance import migrate, grant_runtime, inspect_prepared, reset_test
        from app.infrastructure.database.seed import seed
        engine,_=connection_factory(settings,maintenance=True,testing=args.test)
        try:
            if args.action=='migrate':migrate(engine);result='migrated'
            elif args.action=='reset-test':reset_test(engine);result='test_schema_rebuilt'
            else:
                with engine.begin() as connection:
                    if args.action=='seed':result=seed(connection)
                    elif args.action=='grant-runtime':grant_runtime(connection);result='granted'
                    else:result=inspect_prepared(connection)
            print(json.dumps({'action':args.action,'result':result},ensure_ascii=False))
        finally:engine.dispose()
        return 0
    except ValidationError:
        print("Database configuration invalid or missing; no connection attempted.")
        return 2
    except TargetError:
        print('Database target, credentials or authenticated identity rejected; operation stopped.')
        return 2
    except Exception:
        print('Database operation failed; transaction stopped. No credentials or driver details emitted.')
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
