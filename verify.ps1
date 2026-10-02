$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    py -3.13 -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install -r requirements-verify.txt
& .\.venv\Scripts\python.exe src\verify\verify_all.py
