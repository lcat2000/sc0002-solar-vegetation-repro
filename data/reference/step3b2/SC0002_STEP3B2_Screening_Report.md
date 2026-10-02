# SC0002 Step 3B.2 Screening Result

## Evidence reviewed

- Top-20 candidates frozen by Step 3B.1 pre-treatment ranking.
- Sentinel-2 annual RGB median review images for 2020-2026.
- 2026 review window ends 2026-09-28.
- Metadata scene-count range for each candidate: 130-174.
- Government solar screen: 313/323 official Kaohsiung parcel records geolocated; zero located official points inside or within 100 m of the Top20; ten unresolved records were candidate-specifically reviewed before this step.

No candidate 2023-2026 NDVI/NDMI outcome values were used to pass/fail the visual screening.

## Screening

- PASS: 18 / 20
- EXCLUDE: 2 / 20

Excluded:
- C221 — MAJOR_LANDUSE_CHANGE
- C171 — NOT_COMPARABLE + MAJOR_LANDUSE_CHANGE

## Frozen controls for Step 3B.3

1. C162 — pre-treatment match score 0.251795
2. C172 — pre-treatment match score 0.517143
3. C176 — pre-treatment match score 0.536305
4. C222 — pre-treatment match score 0.674966
5. C129 — pre-treatment match score 0.741550

Selection rule:
PASS only -> ascending pre-treatment match score -> greedy >=2 km center separation -> maximum five controls.

## Important limitation

The annual RGB review is a 10 m Sentinel-2 visual treatment-status screen, not high-resolution cadastral or Google Earth proof. It can identify large clearing/development patterns but may miss small solar installations or subtle land-use changes. The government screen is representative parcel-point based and is not proof of zero cadastral-polygon overlap.
