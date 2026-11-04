"""Run D0 acceptance with logs, exit codes and real loopback HTTP evidence."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/development/reports/2026-11-03_D0_baseline"
OUT.mkdir(parents=True, exist_ok=True)
ENV = {k: v for k, v in os.environ.items() if not k.startswith("MODEL_") and k not in {"DATABASE_URL", "MIGRATION_DATABASE_URL", "MAX_INPUT_TOKENS", "MAX_OUTPUT_TOKENS"}}
ENV.update(APP_ENV="development", MODEL_MODE="disabled", PYTHONUTF8="1",
           UV_CACHE_DIR=str(ROOT / ".cache/uv"), npm_config_cache=str(ROOT / ".cache/npm"), NO_COLOR="1")
UV = str(ROOT / ".tools/bin/uv.exe")
NPM = shutil.which("npm.cmd") or "npm"
commands = []


def run(name, args, cwd=ROOT, expected=0, env=None):
    result = subprocess.run(args, cwd=cwd, env=env or ENV, capture_output=True, encoding="utf-8", errors="replace", timeout=180)
    (OUT / f"{name}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    accepted = expected if isinstance(expected, list) else [expected]
    commands.append({"name": name, "command": [str(a) for a in args], "cwd": str(cwd.relative_to(ROOT)),
                     "exit_code": result.returncode, "expected_exit_code": expected, "passed": result.returncode in accepted})
    (OUT / "commands.json").write_text(json.dumps(commands, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{name}: exit={result.returncode} expected={expected}", flush=True)
    return result


def main():
    protected = [p for base in [ROOT / "materials", ROOT / "docs/requirements"] for p in base.rglob("*") if p.is_file()]
    before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    versions = {}
    for name, args in [("python", [sys.executable, "--version"]), ("node", [shutil.which("node"), "--version"]), ("npm", [NPM, "--version"]), ("uv", [UV, "--version"])]:
        versions[name] = run(f"version-{name}", args).stdout.strip()
    run("lock-check", [UV, "lock", "--check"], ROOT / "backend")
    lock_before = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in ["backend/uv.lock", "frontend/package-lock.json"]}
    # Fresh environment path proves reinstall from the lock without deleting existing files.
    fresh_env = {**ENV, "UV_PROJECT_ENVIRONMENT": str(ROOT / ".cache/d0-frozen-venv")}
    run("backend-frozen-clean", [UV, "sync", "--frozen", "--group", "dev", "--group", "prepare"], ROOT / "backend", env=fresh_env)
    run("backend-tests", [UV, "run", "--frozen", "--no-sync", "pytest", "tests/unit", f"--junitxml={OUT / 'pytest.xml'}"], ROOT / "backend", env=fresh_env)
    run("frontend-frozen", [NPM, "ci"], ROOT / "frontend")
    for name, args in [("frontend-typecheck", ["run", "typecheck"]), ("frontend-vitest", ["run", "test", "--", "--run"]), ("frontend-build", ["run", "build"]), ("frontend-audit", ["audit", "--json"])]:
        run(name, [NPM, *args], ROOT / "frontend")
    run("environment", ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/check_environment.ps1"], expected=[0, 2])
    run("maintenance-unimplemented", ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/manage.ps1", "-Action", "Init"], expected=3)
    run("maintenance-missing-config", ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/manage.ps1", "-Action", "InspectConfig"], expected=2)
    fixture_env = {**ENV, "MIGRATION_DATABASE_URL": "postgresql+psycopg://fixture@127.0.0.1/harness_test_d0"}
    run("maintenance-valid-config", ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/manage.ps1", "-Action", "InspectConfig"], env=fixture_env)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    log = (OUT / "uvicorn.log").open("w", encoding="utf-8")
    server = subprocess.Popen([str(ROOT / "backend/.venv/Scripts/python.exe"), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port), "--workers", "1"], cwd=ROOT / "backend", env=ENV, stdout=log, stderr=log)
    http = []
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/health/live", timeout=1):
                    break
            except (OSError, urllib.error.URLError):
                if server.poll() is not None:
                    raise RuntimeError("Backend exited before liveness")
                time.sleep(.1)
        for path, expected in [("live", 200), ("ready", 503)]:
            try:
                response = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/health/{path}", timeout=5)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                payload = json.loads(response.read())
                http.append({"path": f"/api/v1/health/{path}", "status": response.status, "body": payload,
                             "request_id_header": response.headers.get("X-Request-ID")})
                assert response.status == expected
        assert http[0]["body"]["data"]["status"] == "alive"
        assert http[1]["body"]["data"]["status"] == "not_ready"
        (OUT / "health-http.json").write_text(json.dumps(http, indent=2, ensure_ascii=False), encoding="utf-8")
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/openapi.json", timeout=5) as response:
            (OUT / "openapi.json").write_bytes(response.read())
    finally:
        server.terminate()
        server.wait(timeout=10)
        log.close()
    unchanged = all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value for name, value in lock_before.items())
    protected_unchanged = all(hashlib.sha256(p.read_bytes()).hexdigest() == before[str(p.relative_to(ROOT))] for p in protected)
    run("source-scan", [sys.executable, "scripts/verify_baseline.py"])
    summary = {"run_id": "2026-11-03_D0_baseline", "stage": "D0", "requirements_version": "1.3", "contract_version": "1.2",
               "runtime_versions": versions, "fixture_id": "D0-no-business-data", "seed_hash": None,
               "model_mode": "none", "model_profile_id": None,
               "command": "python scripts/verify_d0.py", "exit_code": 0 if all(c["passed"] for c in commands) and unchanged and protected_unchanged else 1,
               "lock_hashes": lock_before, "locks_unchanged_after_frozen_install": unchanged,
               "protected_input_hashes": before, "protected_inputs_unchanged": protected_unchanged,
               "case_results": [], "evidence_paths": ["commands.json", "pytest.xml", "health-http.json", "openapi.json", "source-scan.json"]}
    summary["source_tree_hash"] = json.loads((OUT / "source-scan.json").read_text(encoding="utf-8"))["source_tree_hash"]
    summary["case_results"] = [
        {"case_id": "TC061", "ac_refs": ["AC-036"], "status": "passed" if summary["exit_code"] == 0 else "failed", "scope": "full D0 engineering case; not full deployment AC-036"},
        {"case_id": "TC051", "ac_refs": ["AC-001", "AC-004", "AC-036"], "status": "not_run", "subitems": [
            {"name": "independent database and maintenance configuration, disabled startup, test_stub environment guard", "status": "passed" if next(c for c in commands if c["name"] == "backend-tests")["passed"] else "failed"},
            {"name": "disabled chat returns 503 without a fake turn", "status": "not_run", "reason": "D2 chat/turn lifecycle not implemented in D0"}
        ]}
    ]
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
