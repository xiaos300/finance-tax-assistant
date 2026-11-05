"""Explicit serial test schema reset; no default application connection fallback."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.cli import main
if __name__=='__main__':
    sys.argv=['reset_test_data','reset-test','--test']
    raise SystemExit(main())
