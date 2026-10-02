# Verification guide

The repository supports two distinct forms of reproducibility.

## 1. Offline archive verification

No Google Earth Engine account is required.

### Windows

```powershell
.\verify.ps1
```

### macOS / Linux

```bash
./verify.sh
```

Equivalent manual command:

```bash
python -m pip install -r requirements-verify.txt
python src/verify/verify_all.py
```

## What is verified

| Stage | Archived evidence | Verifier |
|---|---|---|
| Integrity | `SHA256SUMS.txt` | `verify_sha256.py` |
| AOI | exact V4 GeoJSON | `verify_aoi.py` |
| Step 2 | annual/sensitivity CSVs + TIFFs | `verify_archived_results.py`, `verify_rasters.py` |
| Step 3A | raw robustness exports | `verify_raw_exports.py` |
| Step 3A.1 | raw temporal-break exports | `verify_raw_exports.py` |
| Step 3B.1 | 432 all + 60 hard-pass + Top20 | `verify_step3b1_archive.py` |
| Step 3B.2 | 20 contact sheets + metadata + decisions | `verify_step3b2_review_archive.py` |
| Final control selection | exact greedy >=2 km / max 5 rule | `verify_control_selection.py` |
| Step 3B.3 | raw 30-row outcome + 6 TIFFs + geometry | `verify_raw_exports.py` |
| Step 3B.3 derived | treatment/control tables | `verify_analysis_rebuild.py` |
| Step 3B.4 | aggregation + LOO sensitivity | `verify_analysis_rebuild.py`, `verify_reference_results.py` |

The master verifier runs all of the above:

```text
src/verify/verify_all.py
```

## Expected master result

```text
ALL PASS — repository archive, AOI, raw GEE exports, full control-candidate chain, RGB review archive, derived analyses, rasters, results, hashes, and control-selection invariance verified.
```

## 2. Full rerun

A full rerun requires access to live external services. Follow:

```text
docs/REPRODUCE.md
```

Important: live government/NLSC data and Earth Engine collections may evolve. Exact historical reproduction is therefore anchored by the archived AOI and raw/reference outputs.
