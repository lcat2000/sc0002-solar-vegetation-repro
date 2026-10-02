#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import math
import subprocess
import sys
import tempfile
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/reference/step3b3/SC0002_STEP3B3_Site_Outcome_2022_2026.csv'


def fail(msg):
    raise AssertionError(msg)


def compare_csv(a, b, tol=1e-9):
    da = pd.read_csv(a)
    db = pd.read_csv(b)
    if list(da.columns) != list(db.columns) or len(da) != len(db):
        fail(f'structure mismatch: {a.name}')
    for col in da.columns:
        sa, sb = da[col], db[col]
        na = pd.to_numeric(sa, errors='coerce')
        nb = pd.to_numeric(sb, errors='coerce')
        numeric = na.notna() & nb.notna()
        if numeric.any():
            diff = (na[numeric].astype(float) - nb[numeric].astype(float)).abs().max()
            if float(diff) > tol:
                fail(f'numeric mismatch {a.name}:{col}: max diff {diff}')
        non = ~numeric
        if non.any():
            xa = sa[non].fillna('').astype(str).tolist()
            xb = sb[non].fillna('').astype(str).tolist()
            if xa != xb:
                fail(f'text mismatch {a.name}:{col}')


def compare_bytes(a, b):
    a = Path(a)
    b = Path(b)
    if a.read_bytes() != b.read_bytes():
        fail(f'byte mismatch: {a.name}')


def compare_text(a, b):
    ta = Path(a).read_text(encoding='utf-8')
    tb = Path(b).read_text(encoding='utf-8')
    if ta != tb:
        fail(f'text mismatch: {Path(a).name}')


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    out3 = td / 'step3b3'
    out4 = td / 'step3b4'
    subprocess.run([
        sys.executable, str(ROOT / 'src/analysis/summarize_step3b3.py'),
        '--input', str(RAW), '--outdir', str(out3)
    ], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    subprocess.run([
        sys.executable, str(ROOT / 'src/analysis/run_step3b4_sensitivity.py'),
        '--input', str(RAW), '--outdir', str(out4)
    ], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)

    for p in out3.glob('*.csv'):
        archived = ROOT / 'data/reference/step3b3' / p.name
        compare_csv(p, archived)
        compare_bytes(p, archived)
    for p in out4.glob('*.csv'):
        archived = ROOT / 'data/reference/step3b4' / p.name
        compare_csv(p, archived)
        compare_bytes(p, archived)

    s3 = out3 / 'SC0002_STEP3B3_Summary.txt'
    a3 = ROOT / 'data/reference/step3b3/SC0002_STEP3B3_Summary.txt'
    s4 = out4 / 'SC0002_STEP3B4_Summary.txt'
    a4 = ROOT / 'data/reference/step3b4/SC0002_STEP3B4_Summary.txt'
    compare_text(s3, a3)
    compare_text(s4, a4)
    compare_bytes(s3, a3)
    compare_bytes(s4, a4)

print('PASS — Step 3B.3 and Step 3B.4 archived CSV and Summary.txt outputs rebuild byte-identically from the archived raw 30-row GEE outcome table.')
