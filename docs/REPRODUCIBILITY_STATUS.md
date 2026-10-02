# Reproducibility status matrix

| Component | Offline archived verification | Full rerun path | Status |
|---|---|---|---|
| AOI geometry | Yes (`verify_aoi.py`) | Government data + NLSC | Archived |
| Step 2 V4 spectral results | Yes | GEE script 01/02 | Archived |
| Step 2 GeoTIFF QA | Yes | GEE exports | Archived |
| Step 3A robustness | Yes (`verify_raw_exports.py`) | GEE script 03 | Raw outputs archived |
| Step 3A.1 temporal break | Yes (`verify_raw_exports.py`) | GEE script 04 | Raw outputs archived |
| Step 3B.1 candidate chain | Yes (`verify_step3b1_archive.py`): 432 all + 60 hard-pass + Top20 | GEE script 05 | Fully archived offline |
| Step 3B.2 RGB review + screening/final controls | Yes (`verify_step3b2_review_archive.py`): 20 contact sheets + 140-row metadata + decisions | GEE RGB + NLSC screen | Fully archived offline |
| Post-treatment-screen sensitivity | Yes (`verify_control_selection.py`) | Local Python | Archived |
| Step 3B.3 raw outcomes | Yes (`verify_raw_exports.py`) | GEE script 07 | 30-row CSV + 6 TIFFs + canonical WGS84 geometry archived; original mixed-CRS geometry preserved for provenance |
| Step 3B.3 derived comparison | Yes | `summarize_step3b3.py` | Rebuildable offline from raw CSV |
| Step 3B.4 sensitivity outputs | Yes | `run_step3b4_sensitivity.py` | Rebuildable offline from raw CSV |
| Raw-to-derived analysis chain | Yes (`verify_analysis_rebuild.py`) | Local Python | Verified |
| File hashes | Yes (`verify_sha256.py`) | Local Python | Archived |

The previously documented raw-output gaps were closed by a fresh GEE rerun on **2026-10-02** using the public self-contained scripts and the embedded archived V4 AOI. See `data/reference/RAW_RERUN_PROVENANCE.md`.
