# Reproduce the SC0002 analysis

This guide separates **archived verification** from **full rerun**.

## 0. Environment

Validated local environment: Windows PowerShell + Python 3.13.

Create environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3.13 -m pip install -r requirements.txt
py -3.13 -m playwright install chromium
```

For all offline archived checks:

```powershell
py -3.13 -m pip install -r requirements-verify.txt
py -3.13 src\verify\verify_all.py
```

This verifies hashes, AOI, V4 CSVs, raw Step 3A/3A.1/3B.3 GEE exports, GeoTIFFs, the Step 3B.3/3B.4 offline rebuild chain, and exact control-selection invariance.

---

## 1. Rebuild the government-data AOI

Download official solar-land files:

```powershell
py -3.13 src\aoi\download_moeaea_solar_land.py `
  --outdir .\data\work\solar_official
```

Extract SC0002 parcel rows:

```powershell
py -3.13 src\aoi\01_extract_sc0002_official_parcels.py `
  --solar-source .\data\work\solar_official `
  --out .\data\work\SC0002_Official_Parcels.csv
```

Test NLSC on three rows:

```powershell
py -3.13 src\aoi\02_locate_build_sc0002_aoi.py `
  --parcels-csv .\data\work\SC0002_Official_Parcels.csv `
  --outdir .\data\work\SC0002_AOI_test `
  --limit 3 `
  --headed `
  --debug-screenshots
```

Then full AOI build:

```powershell
py -3.13 src\aoi\02_locate_build_sc0002_aoi.py `
  --parcels-csv .\data\work\SC0002_Official_Parcels.csv `
  --outdir .\data\work\SC0002_AOI
```

Use `--insecure-nlsc` only if local TLS/certificate interception prevents normal access.

Reference run:

```text
Input 107
Located 106
Unresolved 1
Clusters 3
Chosen cluster 93 points
Planar area 63.304526 ha
```

If current government/NLSC data have changed, do not force the current run to match historical row counts. For exact spectral reproduction, use:

`data/aoi/SC0002_Envelope_USED_BY_GEE_V4.geojson`

---

## 2. Sentinel-2 V4 spectral analysis

Open and run these scripts in the Earth Engine Code Editor:

```text
src/gee/01_SC0002_NDVI_NDMI_analysis.js
src/gee/02_SC0002_NDVI_NDMI_sensitivity_analysis.js
```

The exact archived V4 AOI geometry is embedded directly in every public GEE script. No private asset ID or repository-specific GCP project ID is required. Earth Engine itself still requires the reviewer to use an Earth-Engine-enabled account/project in the Code Editor.

Reference outputs are in:

```text
data/reference/step2/
```

Quick expected values:

```text
2022 baseline vegetation  58.239810 ha
2026 standard loss        16.795013 ha
2026 fraction             28.8377%
```

---

## 3. Step 3A robustness

Run:

```text
src/gee/03_SC0002_STEP3A_Robustness.js
```

It evaluates:

- 2020 / 2021 / 2022 baseline-year sensitivity;
- NDVI-only / NDMI-only / combined ablation;
- pre-development nulls;
- event window around 2023-05-05.

Then run:

```text
src/gee/04_SC0002_STEP3A1_Temporal_Break.js
```

for monthly / bimonthly same-season temporal-break diagnostics.

The 2026-10-02 rerun outputs are archived under `data/reference/step3a/` and `data/reference/step3a1/`. `src/verify/verify_raw_exports.py` checks their row counts, fixed-grid raster, and key reference values. A fresh GEE rerun can be compared directly against these archived raw exports.

---

## 4. Step 3B.1 control candidates

Run:

```text
src/gee/05_SC0002_STEP3B1_Control_Candidate_Generator.js
```

The ranking must use pre-treatment data only.

Reference Top-20 file:

```text
data/reference/step3b1/SC0002_STEP3B1_Top20_Control_Candidates.csv
```

---

### Offline Step 3B.1 archive check

Without rerunning Earth Engine, verify the archived candidate chain:

```powershell
py -3.13 src\verify\verify_step3b1_archive.py
```

Expected chain:

```text
432 candidates → 60 hard-pass → exact Top20
```

The corresponding 20 RGB review contact sheets are already archived under:

```text
data/reference/step3b2/review_contact_sheets/
```

Validate them with:

```powershell
py -3.13 src\verify\verify_step3b2_review_archive.py
```

## 5. Step 3B.2 government + visual screening

Download the official data again if not already present.

Extract Kaohsiung records:

```powershell
py -3.13 src\screening\01_extract_kaohsiung_official_solar.py `
  --solar-source .\data\work\solar_official `
  --out .\data\work\Kaohsiung_Official_Solar_Parcels_108_113.csv
```

Reference historical extraction:

```text
323 Kaohsiung parcel rows
大樹區 / 三和段 = 107
```

Locate official records:

```powershell
py -3.13 src\screening\02_locate_official_solar_points_nlsc.py `
  --parcels-csv .\data\work\Kaohsiung_Official_Solar_Parcels_108_113.csv `
  --outdir .\data\work\solar_locator `
  --resume
```

Reference run:

```text
323 input
313 located
10 unresolved
96.9040% coverage
```

Important: this archived official-data scope ends at ROC 113 (2024). A control first entering official solar records in 2025–2026 is outside this government archive window and must be caught, if visible, by later imagery review.

Screen Top-20:

```powershell
py -3.13 src\screening\03_check_candidate_solar_overlap.py `
  --candidates .\data\reference\step3b2\SC0002_STEP3B2_Top20_Control_Candidates_WGS84.geojson `
  --official-parcels-csv .\data\work\Kaohsiung_Official_Solar_Parcels_108_113.csv `
  --located-csv .\data\work\solar_locator\Kaohsiung_Official_Solar_NLSC_All.csv `
  --outdir .\data\work\government_screen
```

For visual treatment-status screening, run:

```text
src/gee/06_SC0002_STEP3B2_Review_Image_Exporter.js
```

Then make contact sheets:

```powershell
py -3.13 src\screening\make_review_contact_sheets.py `
  --input-dir .\review_tif `
  --outdir .\review_png
```

Reference screening outcome:

```text
PASS 18/20
EXCLUDE C221, C171
```

Frozen controls:

```text
C162, C172, C176, C222, C129
```

Exact rule:

```text
screen_pass = YES
→ ascending pre-treatment match_score
→ greedy center separation >= 2000 m
→ maximum 5 controls
```

C185 passed screening and ranked second by match score, but its center is <2 km from C162, so the pre-specified spatial-de-duplication rule skips it.

Run `src/verify/verify_control_selection.py` to reproduce this selection and the post-treatment-screening invariance sensitivity.

Do not use 2023–2026 NDVI/NDMI outcome values to alter this control set.

---

## 6. Step 3B.3 outcomes

Run:

```text
src/gee/07_SC0002_STEP3B3_Control_Outcome.js
```

Expected tasks:

```text
1 outcome CSV
1 site geometry GeoJSON
6 loss-mask TIFFs
```

Then summarize:

```powershell
py -3.13 src\analysis\summarize_step3b3.py `
  --input .\gee_exports\SC0002_STEP3B3_Site_Outcome_2022_2026.csv `
  --outdir .\data\work\step3b3_summary
```

The raw 30-row site-outcome CSV, six loss-mask TIFFs, and six-site geometry from the 2026-10-02 rerun are archived in `data/reference/step3b3/`. The original GEE geometry export mixed WGS84 and EPSG:32651 coordinates and is preserved as `_GEE_RAW_MIXED_CRS.geojson`; the canonical `SC0002_STEP3B3_Site_Geometries.geojson` is RFC 7946 WGS84, and public GEE script 07 now exports WGS84 directly. The local analysis scripts can therefore be rerun offline. `src/verify/verify_analysis_rebuild.py` confirms that the archived Step 3B.3 and Step 3B.4 CSVs rebuild from this raw table.

Reference raw and derived outputs are in:

```text
data/reference/step3b3/
```

---

## 7. Step 3B.4 sensitivity

Use the full Step 3B.3 site-outcome CSV:

```powershell
py -3.13 src\analysis\run_step3b4_sensitivity.py `
  --input .\gee_exports\SC0002_STEP3B3_Site_Outcome_2022_2026.csv `
  --outdir .\data\work\step3b4
```

Reference outputs:

```text
data/reference/step3b4/
```

All predefined robustness checks should pass.

---

## 8. Historical imagery

Open Google Earth / Google Earth Pro and independently review the SC0002 AOI at:

```text
2022-02-02
2023-05-05
2024-02-17
2025-03-08
2026-02-12
```

Expected interpretation:

```text
vegetation
→ clearing / grading
→ solar construction
→ mature PV arrays
→ mature PV persists
```

The third-party images are not included in this repository.

---

## 9. Final validation

Run:

```powershell
py -3.13 src\verify\verify_all.py
```

Then compare your regenerated outputs with `data/reference/`.

Small differences can occur if live external datasets are reprocessed or updated. Any material difference should be investigated rather than silently normalized.
