# SC0002 Solar Development / Spectral Vegetation Change

**Reproducible case study · Kaohsiung, Taiwan · Sentinel-2 + government parcel records + matched controls**

[繁體中文 README](README.zh-TW.md) · [Verification guide](docs/VERIFY.md) · [Method](docs/METHOD.md) · [Full reproduction](docs/REPRODUCE.md) · [Limitations](docs/LIMITATIONS.md)

This repository contains the complete public audit trail for the **SC0002** case study. It is designed so that a reviewer can either:

1. **verify the archived analysis offline**, without Google Earth Engine credentials; or
2. **rerun the analytical workflow**, including the Google Earth Engine steps.

The repository intentionally uses the terms **spectral vegetation loss / decline**, not *tree loss*, and does not present the matched-control contrast as a causal treatment-effect estimate.

---

## Research question

> Does SC0002 show a large post-2022 spectral vegetation decline that is spatially and temporally consistent with documented clearing and subsequent solar construction, and is that decline substantially larger than in pre-treatment-matched controls?

## Main archived result

Sentinel-2 SR Harmonized, March–July annual P70 NDVI/NDMI composites, fixed UTM Zone 51N grid:

```text
2022 baseline spectral vegetation    58.239810 ha
2022→2026 standard spectral loss     16.795013 ha
fraction of 2022 baseline             28.8377%
```

Final controls were frozen before 2023–2026 NDVI/NDMI outcomes were calculated:

```text
C162, C172, C176, C222, C129
```

| Year | SC0002 | Control mean | Highest control | SC0002 − control mean |
|---|---:|---:|---:|---:|
| 2023 | 25.67% | 0.73% | 1.52% | +24.93 pp |
| 2024 | 18.96% | 0.52% | 1.45% | +18.44 pp |
| 2025 | 36.99% | 0.71% | 1.18% | +36.28 pp |
| 2026 | 28.84% | 1.30% | 2.25% | +27.54 pp |

Sensitivity checks pass for control mean, median, trimmed mean, highest-loss control, leave-one-control-out analysis, and valid-data coverage.

**Interpretation note.** The 2022→2026 combined rule is numerically close to NDVI-only (`28.84%` vs `29.33%`), while NDMI-only is more variable and shows a `43.02%` pre-development 2020→2021 null. NDMI is therefore treated as an additional conservative condition, not as independent confirmation. Monthly comparisons are also highly unstable in low-observation months, so the study does not claim an exact clearing onset date. See [Limitations](docs/LIMITATIONS.md) and [Expected results](docs/EXPECTED_RESULTS.md).

---

# Quick verification — no Earth Engine required

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3.13 -m pip install -r requirements-verify.txt
py -3.13 src\verify\verify_all.py
```

Or run the convenience wrapper:

```powershell
.\verify.ps1
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-verify.txt
python3 src/verify/verify_all.py
```

Or:

```bash
./verify.sh
```

Expected final line:

```text
ALL PASS — repository archive, AOI, raw GEE exports, full control-candidate chain, RGB review archive, derived analyses, rasters, results, hashes, and control-selection invariance verified.
```

The verifier checks the complete archived chain, including:

- SHA-256 hashes;
- AOI geometry and properties;
- Step 2 V4 spectral results and raster QA;
- raw Step 3A and Step 3A.1 GEE exports;
- Step 3B.1 **432 candidates → 60 hard-pass → exact Top20**;
- 20 Step 3B.2 RGB review contact sheets + annual metadata;
- final control-selection rule and screening-invariance check;
- raw Step 3B.3 **30-row site-outcome table**, six-site geometry, and six loss rasters;
- offline rebuild of Step 3B.3 and Step 3B.4 derived tables;
- Step 3B.4 leave-one-control-out / conservative-control / coverage checks.

See [docs/VERIFY.md](docs/VERIFY.md) for the audit matrix.

---

# Analysis definition

## Sentinel-2

```text
Collection:       COPERNICUS/S2_SR_HARMONIZED
Annual window:    March 1 – July 31
Annual statistic: per-pixel P70
CRS:              EPSG:32651
Pixel grid:       10 m
Transform:        [10, 0, 0, 0, -10, 0]
```

SCL classes excluded:

```text
0, 1, 3, 7, 8, 9, 10, 11
```

Indices:

```text
NDVI = (B8 - B4) / (B8 + B4)
NDMI = (B8 - B11) / (B8 + B11)
```

2022 baseline spectral vegetation:

```text
NDVI_P70 >= 0.55
AND
NDMI_P70 >= 0.10
```

Standard loss rule:

```text
2022 baseline vegetation
AND (NDVI_2022 - NDVI_target) >= 0.20
AND (NDMI_2022 - NDMI_target) >= 0.10
```

Formal areas are computed with `ee.Image.pixelArea()` inside the AOI. Raster pixel-count area is retained as QA only.

---

# Evidence chain

## 1. Government-record AOI reconstruction

Source dataset:

**取得電業設置發電設備工作許可證太陽光電案場土地地號**, Taiwan Energy Administration, `set_id=344`.

Archived study scope: ROC 108–113 (2019–2024).

Validated SC0002 reconstruction:

```text
official input records       107
located                      106
unresolved                     1
connected clusters             3
chosen cluster points         93
EPSG:3826 planar area    63.304526 ha
Earth Engine geodesic    63.456375 ha
```

The exact V4 AOI is archived at:

```text
data/aoi/SC0002_Envelope_USED_BY_GEE_V4.geojson
```

This archived geometry is embedded in the public GEE scripts, so no private GCP project or Earth Engine asset is required.

## 2. Historical imagery

Independent review dates are recorded in:

```text
data/evidence/google_earth/historical_image_review.csv
```

Validated sequence:

```text
2022-02-02  vegetation-dominated
2023-05-05  major clearing / grading visible
2024-02-17  solar construction visible
2025-03-08  large regular PV arrays visible
2026-02-12  mature PV development persists
```

Google Earth screenshots are **not redistributed**. Reviewers should inspect the same AOI and dates independently. The 2023-05-05 image shows that clearing had occurred **by** that date; it is not treated as the exact onset date.

## 3. Spectral robustness

Archived Step 3A / Step 3A.1 raw GEE exports cover:

- baseline-year sensitivity (2020 / 2021 / 2022);
- NDVI-only / NDMI-only / combined ablation;
- pre-development null comparisons;
- event-window analysis;
- monthly and same-season bimonthly temporal-break analysis.

See [docs/EXPECTED_RESULTS.md](docs/EXPECTED_RESULTS.md).

## 4. Matched-control audit trail

The complete Step 3B.1 candidate archive is stored in:

```text
data/reference/step3b1/
```

Offline chain:

```text
432 all candidates
→ 60 hard-pass candidates
→ Top20 by ascending pre-treatment match_score
```

The pre-treatment `match_score` uses exactly **nine variables**:

- 2020, 2021, 2022 P70 NDVI/NDMI (6 terms);
- 2022 baseline vegetation fraction (1 term);
- SRTM elevation and slope (2 terms).

Valid observations are a **hard screen** (`>=10` in each of 2020–2022), not a score term. Geographic distance defines the deterministic **2–12 km candidate-search ring**, also not a score term. No 2023–2026 NDVI/NDMI outcomes are used for ranking.

Step 3B.2 archives:

```text
20 Top20 RGB contact sheets
140 control-year metadata rows = 20 controls × 7 years
screening decisions
final-control status
```

The visual screen excludes obvious treatment contamination or major unrelated post-2022 development. Because that screen uses post-treatment true-color imagery, [LIMITATIONS.md](docs/LIMITATIONS.md) discusses its potential directional bias. Importantly, the repository verifies that forcing C221, C171, both, or all Top20 candidates to pass leaves the final five controls unchanged under the pre-specified spatial-selection rule.

Final selection rule:

```text
screen_pass = YES
→ ascending pre-treatment match_score
→ greedy center separation >= 2 km
→ maximum 5 controls
```

Final controls:

```text
C162, C172, C176, C222, C129
```

---

# Repository map

```text
.
├── README.md
├── README.zh-TW.md
├── LICENSE
├── CHANGELOG.md
├── SHA256SUMS.txt
├── verify.ps1
├── verify.sh
├── requirements.txt
├── requirements-verify.txt
├── vercel.json
├── site/
│   └── index.html
├── .github/
│   └── workflows/verify-reference.yml
├── docs/
│   ├── VERIFY.md
│   ├── AUDIT_TRAIL.md
│   ├── METHOD.md
│   ├── REPRODUCE.md
│   ├── EXPECTED_RESULTS.md
│   ├── REPRODUCIBILITY_STATUS.md
│   ├── RELEASE_CHECKLIST.md
│   ├── PUBLISH_TO_GITHUB.md
│   └── LIMITATIONS.md
├── src/
│   ├── aoi/
│   ├── gee/
│   ├── screening/
│   ├── analysis/
│   └── verify/
└── data/
    ├── aoi/
    ├── evidence/google_earth/
    └── reference/
        ├── step2/
        ├── step3a/
        ├── step3a1/
        ├── step3b1/
        ├── step3b2/
        ├── step3b3/
        └── step3b4/
```

---

# Full reproduction

For a full rerun, including AOI reconstruction and Earth Engine analyses, follow:

**[docs/REPRODUCE.md](docs/REPRODUCE.md)**

External services used:

- Google Earth Engine Sentinel-2 SR Harmonized: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
- NLSC map / cadastral locator: https://maps.nlsc.gov.tw/
- Taiwan Energy Administration open-data download endpoint (`set_id=344`): https://www.moeaea.gov.tw/ECW/populace/opendata/wHandOpenData_File.ashx?set_id=344

External records and interfaces can change. The repository therefore archives the exact AOI and reference outputs used for the study.

---

# Interpretation boundary

Supported statement:

> SC0002 exhibits a large and persistent post-2022 spectral vegetation decline that is spatially and temporally consistent with independently reviewed clearing and subsequent solar construction. The decline is substantially larger than in five pre-treatment-matched, outcome-blindly ranked controls and remains robust under the archived sensitivity checks.

Not established by this repository alone:

- direct measurement of tree-species or tree-canopy loss;
- a legally surveyed construction footprint;
- attribution of every changed pixel to PV modules;
- a causal treatment-effect estimate;
- project-level legal or causal responsibility.

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

---

# Suggested GitHub metadata

**Repository name**

```text
sc0002-solar-vegetation-repro
```

**Description**

```text
Reproducible Sentinel-2 case study of post-development spectral vegetation change at SC0002, Kaohsiung, with archived government-data AOI, matched controls, raw GEE exports, RGB review evidence, and offline verification.
```

**Suggested topics**

```text
remote-sensing sentinel-2 google-earth-engine ndvi ndmi solar-pv
reproducible-research environmental-monitoring taiwan geospatial
```

## License

Repository code is released under the MIT License. External government data, cadastral services, Sentinel data, and third-party historical imagery remain subject to their own terms and licenses.
