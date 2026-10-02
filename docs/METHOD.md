# Method

## 1. Study design

SC0002 is treated as a single-site case study with four independent evidence streams:

1. government solar-land records and cadastral-location reconstruction;
2. historical-image review;
3. Sentinel-2 spectral vegetation change;
4. pre-treatment-matched controls frozen before outcome calculation.

The design is descriptive and quasi-experimental in spirit, but it is **not presented as causal identification**.

The public GEE scripts embed the exact archived V4 AOI geometry directly, so no private Earth Engine asset or GCP project identifier is required.

## 2. AOI reconstruction

Official source: Taiwan Energy Administration dataset `set_id=344`, archived study scope ROC 108–113.

Pipeline:

```text
official parcel rows
→ normalize city / district / section / lot
→ 高雄市 / 大樹區 / 三和段
→ NLSC current parcel locator
→ 300 m transitive point connectivity
→ largest connected cluster
→ convex hull + 50 m buffer
```

Validated reference:

```text
107 input rows
106 located
1 unresolved
3 connected clusters
93 points in selected cluster
63.304526 ha planar area in EPSG:3826
63.456375 ha Earth Engine geodesic area
```

The selected cluster is chosen by largest component first. The reference seed is a tie-break / diagnostic only, not the AOI centroid.

## 3. Fixed raster grid

```text
CRS            EPSG:32651
pixel size     10 m
transform      [10,0,0,0,-10,0]
```

Formal areas are computed from `ee.Image.pixelArea()` within geometry. Raster full-cell counts are QA only.

## 4. Sentinel-2

Collection:

```text
COPERNICUS/S2_SR_HARMONIZED
```

Annual time window: March–July.

SCL excluded:

```text
0 no data
1 saturated/defective
3 cloud shadow
7 low-probability cloud/unclassified
8 medium-probability cloud
9 high-probability cloud
10 cirrus
11 snow/ice
```

Indices:

```text
NDVI = (B8-B4)/(B8+B4)
NDMI = (B8-B11)/(B8+B11)
```

Annual statistic: per-pixel P70.

## 5. Baseline and loss rules

2022 baseline spectral vegetation:

```text
NDVI_P70 >= 0.55
AND
NDMI_P70 >= 0.10
```

Threshold sensitivity:

```text
Loose     NDVI drop >= 0.15, NDMI drop >= 0.08
Standard  NDVI drop >= 0.20, NDMI drop >= 0.10
Strict    NDVI drop >= 0.25, NDMI drop >= 0.12
```

Annual loss is not cumulative. Each target year is compared independently against the same baseline.

## 6. Step 3A robustness

Step 3A evaluates:

- alternative baseline years (2020 / 2021 / 2022);
- NDVI-only vs NDMI-only vs combined rules;
- pre-development null comparisons;
- event-window analysis around 2023-05-05.

Step 3A.1 uses monthly and same-season bimonthly comparisons to reduce seasonal confounding.

Important interpretation:

- divergence is already visible in early 2023;
- 2023-05-05 is evidence that clearing had occurred by then;
- monthly P70 is too unstable to claim an exact clearing date.

## 7. Matched-control generation

Control candidates are generated from a deterministic UTM grid.

The `match_score` is a normalized squared-distance score using exactly **nine pre-treatment variables**:

- P70 NDVI 2020, 2021, 2022 (3 terms);
- P70 NDMI 2020, 2021, 2022 (3 terms);
- 2022 baseline vegetation fraction (1 term);
- SRTM elevation (1 term);
- SRTM slope (1 term).

Two additional design constraints are intentionally **not score terms**:

- 2020–2022 valid observations are a hard screen (`>=10` in each year);
- geographic distance defines the deterministic candidate-search ring (2–12 km from SC0002).

No 2023–2026 NDVI / NDMI outcomes are used for ranking. `verify_step3b1_archive.py` independently recomputes every archived `match_score` and `match_pass` from these pre-treatment inputs.

### Offline candidate audit archive

The repository archives all 432 candidates, the exact 60 `match_pass=1` candidates, and the Top20. The 60-row table is deterministically derived from the archived 432-row GEE export and sorted by ascending `match_score`; the Top20 must equal its first 20 rows.

Hard-screen rules and the scoring formula are documented directly in:

`src/gee/05_SC0002_STEP3B1_Control_Candidate_Generator.js`

## 8. Control treatment-status screening

Top-20 candidates are screened for:

- known official solar-parcel point hit;
- historical pre-2023 comparability;
- post-2022 visible solar or major unrelated development;
- obvious non-comparability;
- imagery sufficiency.

The official solar screen is a **representative parcel-point** screen, not cadastral polygon proof.

The annual RGB review is a 10 m Sentinel-2 treatment-status screen. It can identify major development but can miss small installations. Because post-treatment true-colour features such as clearing can correlate with the spectral outcome, this screening can in principle introduce directional selection bias. In this case, forcing the visually excluded candidates to pass does not change the final five controls; see `src/verify/verify_control_selection.py`.

Final controls are frozen before outcome analysis:

```text
C162
C172
C176
C222
C129
```

## 9. Treatment vs controls

Step 3B.3 applies the same 2022 baseline and annual loss rule to treatment and controls.

Comparisons include:

- control mean;
- control median;
- control range;
- difference in percentage points;
- treatment/control ratio;
- rank among six sites;
- valid-baseline coverage.

## 10. Sensitivity

Step 3B.4 tests:

- mean vs median;
- trimmed mean;
- treatment vs highest-loss individual control;
- leave-one-control-out means;
- per-control influence on aggregate mean;
- valid-data coverage guardrail.

No control replacement is permitted after outcomes are observed.

## 11. Spatial-resolution and mask notes

B11 is natively 20 m, so NDMI does not contain independent 10 m SWIR information even though outputs share a 10 m grid. SCL class 2 is retained in the production mask. These choices are documented as limitations rather than silently treated as 10 m cloud/shadow-free truth.

## 12. Archived raw outputs

Step 3A, Step 3A.1, and Step 3B.3 were rerun on 2026-10-02 using the public self-contained GEE scripts and the embedded archived V4 AOI. Their raw CSV/GeoTIFF outputs are archived under `data/reference/step3a/`, `step3a1/`, and `step3b3/`. The historical Step 3B.3 GEE geometry export is retained separately because it mixed WGS84 and EPSG:32651 coordinates; the canonical six-site GeoJSON is RFC 7946 WGS84 and script 07 now exports WGS84 directly. The Step 3B.3 and Step 3B.4 derived CSVs are reproducible offline from the archived 30-row site-outcome table. See `docs/REPRODUCIBILITY_STATUS.md` and `data/reference/RAW_RERUN_PROVENANCE.md`.
