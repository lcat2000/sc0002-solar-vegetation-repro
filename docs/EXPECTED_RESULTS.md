# Expected and archived results

This document summarizes the archived reference run. Step 3A, Step 3A.1, and Step 3B.3 raw GEE outputs were rerun and archived on 2026-10-02; see `docs/REPRODUCIBILITY_STATUS.md` and `data/reference/RAW_RERUN_PROVENANCE.md`.

## Step 2 — V4 spectral analysis

```text
2022 baseline spectral vegetation   58.239810 ha
2022→2026 standard loss             16.795013 ha
2026 fraction                       28.8377%
```

Annual loss relative to the same 2022 baseline:

| Year | Loss ha | Fraction |
|---|---:|---:|
| 2023 | 14.947461 | 25.6654% |
| 2024 | 11.043818 | 18.9627% |
| 2025 | 21.545707 | 36.9948% |
| 2026 | 16.795013 | 28.8377% |

Threshold sensitivity:

| Setting | NDVI drop | NDMI drop | Loss ha | Fraction |
|---|---:|---:|---:|---:|
| Loose | 0.15 | 0.08 | 19.529414 | 33.5328% |
| Standard | 0.20 | 0.10 | 16.795013 | 28.8377% |
| Strict | 0.25 | 0.12 | 14.498828 | 24.8950% |

Main raster counts:

```text
0      4829
1      1694
255    1329
```

## Step 3A — baseline sensitivity (raw rerun export archived)

| Baseline | Baseline vegetation | Loss to 2026 | Fraction |
|---|---:|---:|---:|
| 2020 | 61.63 ha | 19.84 ha | 32.19% |
| 2021 | 42.09 ha | 9.48 ha | 22.53% |
| 2022 | 58.24 ha | 16.80 ha | 28.84% |

## Step 3A — ablation (raw rerun export archived)

```text
NDVI-only   17.08 ha / 29.33%
NDMI-only   24.54 ha / 42.14%
Combined    16.80 ha / 28.84%
```

Pre-development combined nulls:

```text
2019→2020   0.00%
2020→2021   4.61%
2021→2022   1.49%
```

The NDMI-only 2020→2021 comparison is much larger (~43%), illustrating sensitivity to moisture / phenology and motivating the combined rule.

## Step 3A.1 — temporal break (raw rerun export archived)

Same-bimonth combined loss:

| Period | 2022→2023 | 2022→2024 |
|---|---:|---:|
| Jan–Feb | 29.82% | 31.01% |
| Mar–Apr | 56.09% | 43.86% |
| May–Jun | 12.76% | 9.71% |
| Jul–Aug | 15.75% | 14.68% |
| Sep–Oct | 9.27% | 14.22% |
| Nov–Dec | 0.76% | 5.04% |

Interpretation: divergence is already visible by Jan–Feb 2023 and is strongest in Mar–Apr. Monthly P70 is too unstable for an exact onset date.

## Observation-quality note

The 2018 annual composite has only 3 source scenes and mean valid observations ~1.54. It is exploratory and is not used for the main baseline/control conclusion.

## Step 3B.1 — full candidate archive

```text
All deterministic candidates      432
Hard-pass (match_pass=1)           60
Top20 forwarded to Step 3B.2       20
```

Top20 order:

```text
C162, C185, C172, C176, C222, C129, C221, C177, C290, C264,
C268, C269, C152, C146, C241, C171, C291, C179, C153, C313
```

All archived ranking rows retain `outcome_data_used_for_ranking=NO` and `selection_data_end=2022-12-31`.

## Step 3B.2 — RGB review archive

```text
Top20 contact sheets                 20
Top20 annual metadata rows          140  (20 × 7 years)
Original metadata rows              147  (SC0002 + 20 controls, 7 years each)
Annual source-scene-count range  130–174
```

## Step 3B.2 — control screening

```text
Top20 reviewed   20
PASS             18
EXCLUDE           2
```

Excluded:

```text
C221  MAJOR_LANDUSE_CHANGE
C171  NOT_COMPARABLE + MAJOR_LANDUSE_CHANGE
```

Final frozen controls:

```text
C162
C172
C176
C222
C129
```

## Step 3B.3 — treatment vs controls

| Year | SC0002 | Control mean | Median | Range | Difference vs mean |
|---|---:|---:|---:|---:|---:|
| 2023 | 25.67% | 0.73% | 0.45% | 0.15–1.52% | +24.93 pp |
| 2024 | 18.96% | 0.52% | 0.43% | 0.00–1.45% | +18.44 pp |
| 2025 | 36.99% | 0.71% | 0.70% | 0.02–1.18% | +36.28 pp |
| 2026 | 28.84% | 1.30% | 1.15% | 0.05–2.25% | +27.54 pp |

2026 ranking:

```text
SC0002  28.84%
C162     2.25%
C176     1.96%
C172     1.15%
C222     1.10%
C129     0.05%
```

## Step 3B.4 — sensitivity

Conservative comparison with the highest-loss control:

```text
2023 +24.14 pp
2024 +17.51 pp
2025 +35.82 pp
2026 +26.59 pp
```

Smallest treatment-minus-LOO-control-mean gap:

```text
2023 +24.79 pp
2024 +18.31 pp
2025 +36.11 pp
2026 +27.22 pp
```

All predefined checks pass:

```text
treatment > control mean
treatment > control median
treatment > trimmed mean
treatment > every control
all leave-one-control-out means < treatment
valid-data coverage guardrail
```

## Step 3B.2 post-treatment-screening selection sensitivity

Forcing C221, C171, both, or all Top20 candidates to pass screening reproduces the same final five controls under the exact pre-specified rule. See `SC0002_STEP3B2_Selection_Invariance.csv`.
