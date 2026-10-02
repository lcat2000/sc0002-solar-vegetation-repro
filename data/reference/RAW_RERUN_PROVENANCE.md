# Raw GEE rerun provenance

Date: **2026-10-02**

Purpose: close the raw-output archive gaps previously documented for Step 3A, Step 3A.1, and Step 3B.3.

The rerun used the public self-contained Earth Engine scripts in this repository. The exact archived V4 AOI is embedded in those scripts; no private GCP project ID or private Earth Engine asset was used.

Scripts:

```text
src/gee/03_SC0002_STEP3A_Robustness.js
src/gee/04_SC0002_STEP3A1_Temporal_Break.js
src/gee/07_SC0002_STEP3B3_Control_Outcome.js
```

Archived outputs:

```text
data/reference/step3a/
  4 CSV raw tables
  1 three-band ablation-mask GeoTIFF

data/reference/step3a1/
  5 CSV raw tables

data/reference/step3b3/
  SC0002_STEP3B3_Site_Outcome_2022_2026.csv   (30 rows = 6 sites × 5 years)
  SC0002_STEP3B3_Site_Geometries.geojson      (6 sites, canonical RFC 7946 WGS84)
  SC0002_STEP3B3_Site_Geometries_GEE_RAW_MIXED_CRS.geojson
      (preserved original 2026-10-02 GEE export; SC0002 WGS84 + controls EPSG:32651)
  6 loss-mask GeoTIFFs
  derived Step 3B.3 CSV/TXT summaries regenerated from the raw table
```

The Step 3B.4 CSV/TXT outputs were also regenerated locally from the newly archived Step 3B.3 raw 30-row table.

Validation:

```text
src/verify/verify_raw_exports.py
src/verify/verify_analysis_rebuild.py
```

The raw rerun reproduces the previously reported rounded findings. Tiny sub-nanoscopic differences (typically around 1e-10 to 1e-9 in floating-point area/fraction fields) can occur in Earth Engine `pixelArea()` reductions; they do not change any reported rounded percentage, ranking, PASS/FAIL result, or interpretation.

The original transport ZIP is not part of the repository. Every archived rerun output that is part of the scientific record is individually covered by `SHA256SUMS.txt`.

Geometry correction note: the 2026-10-02 GEE GeoJSON export mixed the WGS84 treatment geometry with EPSG:32651 control geometries. The exact original is retained under the `_GEE_RAW_MIXED_CRS` filename. The canonical `SC0002_STEP3B3_Site_Geometries.geojson` transforms the five controls to WGS84 without changing analysis geometries or numerical outcomes. Public GEE script 07 now transforms all site geometries to WGS84 before future GeoJSON exports.
