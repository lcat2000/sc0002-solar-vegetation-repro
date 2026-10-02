#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = [
    "src/verify/verify_sha256.py",
    "src/verify/verify_reference_results.py",
    "src/verify/verify_raw_exports.py",
    "src/verify/verify_analysis_rebuild.py",
    "src/verify/verify_aoi.py",
    "src/verify/verify_archived_results.py",
    "src/verify/verify_rasters.py",
    "src/verify/verify_step3b1_archive.py",
    "src/verify/verify_step3b2_review_archive.py",
    "src/verify/verify_control_selection.py",
]

for rel in SCRIPTS:
    print("\n===", rel, "===", flush=True)
    r = subprocess.run([sys.executable, str(ROOT/rel)], cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit(r.returncode)
print("\nALL PASS — repository archive, AOI, raw GEE exports, full control-candidate chain, RGB review archive, derived analyses, rasters, results, hashes, and control-selection invariance verified.")
