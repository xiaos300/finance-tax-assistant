"""D0 configuration inspection only; database mutations are deliberately unavailable."""
import argparse

from pydantic import ValidationError

from app.core.config import database_settings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["inspect-config"])
    parser.add_argument("--maintenance", action="store_true")
    args = parser.parse_args()
    try:
        database_settings(maintenance=args.maintenance)
    except ValidationError:
        print("Database configuration invalid or missing; no connection attempted.")
        return 2
    print("Database configuration valid; no connection attempted; model settings not loaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
