#!/usr/bin/env python3
from pathlib import Path
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "SHA256SUMS.txt"


def main():
    failures = []
    checked = 0
    listed = set()
    for raw in MANIFEST.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            expected, rel = raw.split("  ", 1)
        except ValueError:
            failures.append(f"malformed manifest line: {raw}")
            continue
        listed.add(rel)
        p = ROOT / rel
        if not p.is_file():
            failures.append(f"missing: {rel}")
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        checked += 1
        if got != expected:
            failures.append(f"hash mismatch: {rel}: {got} != {expected}")
    def ignored_runtime_path(path):
        rel = path.relative_to(ROOT)
        parts = rel.parts
        if any(part in {'.git', '.venv', 'venv', '__pycache__'} for part in parts):
            return True
        if rel.as_posix().startswith(('data/work/', 'data/downloads/', 'data/solar_official/', 'data/solar_locator/', 'gee_exports/', 'review_tif/', 'review_png/')):
            return True
        if path.name in {'.DS_Store', 'Thumbs.db'}:
            return True
        if path.suffix.lower() in {'.pyc', '.pyo', '.pyd'}:
            return True
        return False

    actual = {
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob('*')
        if p.is_file()
        and p.name != 'SHA256SUMS.txt'
        and not ignored_runtime_path(p)
    }
    missing_from_manifest = sorted(actual - listed)
    stale_manifest_entries = sorted(listed - actual)
    for rel in missing_from_manifest:
        failures.append(f"unlisted file: {rel}")
    for rel in stale_manifest_entries:
        failures.append(f"manifest entry without file: {rel}")

    if failures:
        print("FAIL — SHA256 manifest")
        for x in failures:
            print(" -", x)
        raise SystemExit(1)
    print(f"PASS — SHA256SUMS.txt verified and complete ({checked} files).")

if __name__ == "__main__":
    main()
