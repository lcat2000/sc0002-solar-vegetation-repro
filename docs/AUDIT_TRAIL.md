# Audit trail

This file maps each analytical claim to the archived material needed to inspect it.

## AOI

```text
data/aoi/SC0002_Envelope_USED_BY_GEE_V4.geojson
src/aoi/
```

Reference reconstruction:

```text
107 official records
106 located
1 unresolved
3 connected clusters
93 points selected
convex hull + 50 m buffer
```

## Step 2 — primary spectral result

```text
data/reference/step2/
src/gee/01_SC0002_NDVI_NDMI_analysis.js
src/gee/02_SC0002_NDVI_NDMI_sensitivity_analysis.js
```

Primary archived result:

```text
2022 baseline spectral vegetation = 58.239810 ha
2022→2026 standard loss           = 16.795013 ha
fraction                          = 28.8377%
```

## Step 3A — robustness

```text
data/reference/step3a/
src/gee/03_SC0002_STEP3A_Robustness.js
```

Includes baseline-year sensitivity, index ablation, pre-development nulls, and event-window output.

## Step 3A.1 — temporal break

```text
data/reference/step3a1/
src/gee/04_SC0002_STEP3A1_Temporal_Break.js
```

Includes monthly and same-season bimonthly comparisons.

## Step 3B.1 — candidate generation

```text
data/reference/step3b1/
src/gee/05_SC0002_STEP3B1_Control_Candidate_Generator.js
src/verify/verify_step3b1_archive.py
```

Offline chain:

```text
432 all candidates
→ 60 hard-pass
→ exact Top20 ranking
```

## Step 3B.2 — control screening

```text
data/reference/step3b2/
data/reference/step3b2/review_contact_sheets/
src/gee/06_SC0002_STEP3B2_Review_Image_Exporter.js
src/verify/verify_step3b2_review_archive.py
src/verify/verify_control_selection.py
```

The archive contains 20 Top20 contact sheets, annual RGB metadata, screening decisions, and the final selection audit.

## Step 3B.3 — outcomes

```text
data/reference/step3b3/
src/gee/07_SC0002_STEP3B3_Control_Outcome.js
src/analysis/summarize_step3b3.py
```

Raw table:

```text
6 sites × 5 years = 30 rows
```

Final controls:

```text
C162, C172, C176, C222, C129
```

## Step 3B.4 — sensitivity

```text
data/reference/step3b4/
src/analysis/run_step3b4_sensitivity.py
```

Covers mean, median, trimmed mean, highest-loss control, LOO, influence, and valid-data guardrails.

## Historical imagery

```text
data/evidence/google_earth/historical_image_review.csv
```

Third-party imagery is not redistributed; dates and interpretation records are archived for independent re-review.

## Step 3B.3 geometry CRS audit

The original 2026-10-02 GEE `Site_Geometries` export mixed the WGS84 SC0002 polygon with EPSG:32651 control polygons. It is preserved verbatim as `data/reference/step3b3/SC0002_STEP3B3_Site_Geometries_GEE_RAW_MIXED_CRS.geojson`. The canonical `SC0002_STEP3B3_Site_Geometries.geojson` transforms all six sites to RFC 7946 WGS84. `verify_raw_exports.py` checks coordinate ranges and control centers, and GEE script 07 now applies `.transform('EPSG:4326', 1)` before export. This correction affects only the GIS review file, not any analysis geometry or numerical result.
