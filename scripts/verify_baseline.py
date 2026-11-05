"""TC061 source/build secret scan and reproducible source/context inventories.

Not a release packager. Findings print locations and rule names only.
"""
import hashlib
import json
from pathlib import Path
import re
import argparse

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".tools", ".cache", ".venv", "node_modules", "__pycache__", ".pytest_cache", "var"}
PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "provider_key": re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    "credential_url": re.compile(r"postgres(?:ql)?(?:\+psycopg)?://[^\s/:]+:[^\s@]+@"),
    "bearer": re.compile(r"Bearer\s+[A-Za-z0-9_-]{24,}"),
}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,default=ROOT/'docs/development/reports/2026-11-03_D0_baseline')
    args=parser.parse_args()
    findings = []
    manifest = {}
    scanned = 0
    for base in [ROOT / "backend", ROOT / "frontend", ROOT / "scripts", ROOT/'data/seed', ROOT/'deploy', ROOT]:
        candidates = base.glob("*") if base == ROOT else base.rglob("*")
        for path in sorted(candidates):
            relative = path.relative_to(ROOT)
            if not path.is_file() or any(p in EXCLUDED for p in relative.parts) or path.suffix == ".pyc" or (path.name.startswith('.env') and path.name != '.env.example'):
                continue
            if "dist" not in relative.parts:
                manifest[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
            if path.suffix not in {".py", ".ts", ".vue", ".js", ".mjs", ".json", ".toml", ".html", ".css", ".ps1", ".md", ".lock",'.sql','.sh'} and path.name not in {".env.example", ".gitignore", ".dockerignore"}:
                continue
            scanned += 1
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for rule, pattern in PATTERNS.items():
                    if pattern.search(line):
                        findings.append({"file": relative.as_posix(), "line": line_no, "rule": rule})
    for name in [".env.example", ".gitignore", ".dockerignore", "README.md"]:
        path = ROOT / name
        manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    # Guard actual ignore boundaries. An added rule failure makes acceptance fail.
    required = {
        ".gitignore": [".env", ".tools/", ".cache/", ".venv/", "node_modules/", "dist/", "var/"],
        ".dockerignore": [".env", ".tools", ".cache", "**/.venv", "**/node_modules", "var", "materials"],
    }
    boundaries = all(all(rule in (ROOT / name).read_text().splitlines() for rule in rules) for name, rules in required.items())
    # Prove scanner detects a synthetic credential without persisting that credential.
    canary_detected = bool(PATTERNS["provider_key"].search("sk-" + "D0Canary" * 5))
    result = {"source_tree_hash": hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
              "files": manifest, "scanned_files_including_dist": scanned,
              "findings": findings, "ignore_boundaries_passed": boundaries, "canary_detected": canary_detected}
    target = args.output_dir
    target.mkdir(parents=True, exist_ok=True)
    (target / "source-scan.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "files"}, ensure_ascii=False))
    return 0 if not findings and boundaries and canary_detected else 1


if __name__ == "__main__":
    raise SystemExit(main())
