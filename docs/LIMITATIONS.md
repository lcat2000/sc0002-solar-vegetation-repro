# Limitations and interpretation boundaries

## Spectral change is not automatically tree loss

NDVI and NDMI measure spectral vegetation / moisture response. A 10 m output pixel can contain PV modules, inter-row vegetation, soil, roads, shadows, and mixed woody / herbaceous cover. Therefore this repository uses **spectral vegetation loss** or **spectral vegetation decline**.

## NDMI has 20 m native SWIR support

NDVI uses B8 and B4 (10 m bands), but NDMI uses B8 and B11; Sentinel-2 B11 is natively 20 m. The analysis is exported/reduced on a 10 m UTM grid for common alignment, but this does not create 10 m native information in B11. Fine-scale NDMI patterns should therefore not be interpreted as independent 10 m measurements.

## SCL class 2 is retained

The production mask excludes SCL classes 0, 1, 3, 7, 8, 9, 10, and 11. SCL class 2 (dark area / topographic shadow) is retained. Because the site is not perfectly flat, residual terrain-shadow effects are a plausible source of spectral variability. A future extension can test an alternative mask that also excludes class 2.

## The combined 2022→2026 result is numerically NDVI-dominated

The 2022→2026 ablation is `29.33%` for NDVI-only, `42.14%` for NDMI-only, and `28.84%` for the combined NDVI+NDMI rule. For the main 2026 comparison, the combined result is therefore very close to NDVI-only; NDMI acts mainly as an additional conservative filter rather than an independent corroborating signal. Conversely, NDMI-only produces a `43.02%` 2020→2021 pre-development null, showing strong moisture/phenology sensitivity. The repository does not treat NDMI-only change as evidence of development.

Monthly same-month loss estimates are also unstable (`0.72%`–`88.39%` in the archived 2022-vs-2023/2024 comparisons), and 2022 monthly mean valid observations range from about `1.76` to `8.06` per pixel. Monthly analysis is used only to bound timing, not to identify an exact onset date. Baseline-year sensitivity is also material: the 2021 baseline contains `42.09 ha` of baseline spectral vegetation versus `58.24 ha` in 2022.

## Annual masks are not cumulative

Every target year is independently compared with the same 2022 baseline. A pixel can cross the threshold in one year and not another because of phenology, soil moisture, valid-observation dates, P70 sample composition, mixed pixels, or construction state. A decrease in annual loss from 2025 to 2026 does not imply PV removal.

## Valid-domain asymmetry can bias loss fractions downward when coverage is incomplete

The primary fraction uses the full 2022 baseline-vegetation area as denominator, while a target-year loss pixel also requires valid target-year NDVI/NDMI. If target-year coverage is incomplete, the primary fraction can be biased downward. Step 3B.3 therefore also exports `loss_fraction_of_valid_2022_baseline` and `baseline_veg_valid_fraction_this_year`; the final control comparison passed the valid-data guardrail, so this issue does not materially affect the reported 2023–2026 comparison. Future exports clamp the reported valid-coverage fraction to [0,1] to avoid tiny floating-point values above 1.

## 2018 is low-observation and exploratory

The 2018 March–July composite contains only 3 source scenes and mean valid observations of about 1.54 per pixel. It is retained for transparency but should not be treated as comparable in reliability to 2019–2026. The main baseline and matched-control conclusions do not depend on 2018.

## Historical imagery is manually reviewed

Google Earth historical imagery is an independent visual evidence stream, but the images are not redistributed here. Reviewers must reproduce the dates manually. The 2023-05-05 image confirms clearing had occurred by that date; it does not identify the exact onset date.

## AOI is an analytical envelope, not a cadastral parcel union

The AOI is built from 93 representative parcel-location points in the largest connected component, followed by a convex hull + 50 m buffer. This can include land inside the hull that is not itself part of the solar project, and it intentionally omits the two smaller disconnected clusters. The AOI therefore represents the reconstructed SC0002 analytical envelope, not a legally surveyed union of exact project parcels.

## Government screen is not exact cadastral overlap

The NLSC workflow yields representative parcel-location points for screening. It is not a substitute for legally surveyed parcel polygons. Use `NO_KNOWN_OFFICIAL_SOLAR_POINT_HIT`, not `EXACT_NO_SOLAR_OVERLAP`, unless exact polygon geometry is independently supplied.

## Government solar archive has a 2025–2026 time blind spot

The reproducibility scope of the Energy Administration archive used here is ROC 108–113 (2019–2024). A control site that first received an official solar permit/record in 2025–2026 would not be detected by this archived government screen. For those years, treatment-status screening relies on the 2025–2026 Sentinel-2 true-colour review and can miss small installations.

## Post-treatment true-colour screening can introduce directional selection bias

The control-screening stage used 2023–2026 true-colour imagery to reject obvious treatment contamination or major unrelated development. Although no post-treatment NDVI/NDMI outcome values were used for ranking or selection, visible clearing or exposed soil can correlate with NDVI/NDMI decline. In principle, excluding such candidates can lower the control-group loss distribution and enlarge the treatment-control contrast.

For this case, that concern was tested against the exact pre-specified selection rule. C221 and C171 were the two visually excluded Top20 candidates, but both ranked below the five ultimately selected controls. Forcing C221, C171, both, or even all Top20 candidates to pass the visual screen leaves the selected set unchanged: `C162, C172, C176, C222, C129`. This invariance is verified by `src/verify/verify_control_selection.py` and archived in `data/reference/step3b2/SC0002_STEP3B2_Selection_Invariance.csv`. The general bias risk remains a limitation of the screening design even though it does not alter the final five controls in this case.

## Live external data can change

Government open data, NLSC current parcel records, and Earth Engine collections are live sources. Re-running later may not reproduce every intermediate row count bit-for-bit. The repository therefore archives the exact V4 AOI geometry and reference outputs.

## Controls reduce, but do not eliminate, confounding

The matched-control `match_score` uses pre-treatment spectral and terrain variables. Valid-observation density is a hard screen, while geographic distance defines the 2–12 km candidate-search ring; neither is a score term. Candidates are then screened for obvious treatment / development. This strengthens the descriptive comparison but does not prove causal identification. Unmeasured differences can remain.

## No causal acreage claim

Do not report: `solar caused 16.795 ha of tree loss`. The supported statement is narrower: SC0002 exhibits a large site-specific post-development spectral vegetation decline, spatially and temporally consistent with independently reviewed clearing and solar construction, and substantially larger than in the frozen matched controls.
