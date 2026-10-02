# Google Earth historical-image review

Google Earth / third-party historical imagery is **not redistributed in this public repository**. The repository contains only the validated review log in `historical_image_review.csv` and instructions for independent reproduction.

Use the exact archived AOI:

```text
data/aoi/SC0002_Envelope_USED_BY_GEE_V4.geojson
```

Validated SC0002 sequence:

| Image date | Review |
|---|---|
| 2022-02-02 | vegetation-dominated baseline |
| 2023-05-05 | clearing / grading |
| 2024-02-17 | PV construction / partial rows |
| 2025-03-08 | large regular PV arrays |
| 2026-02-12 | mature PV development persists |

Important timing caveat: the Sentinel annual analysis uses March–July. Therefore 2022-02-02 is independent pre-window visual evidence, not same-date Sentinel ground truth; 2023-05-05 falls inside the 2023 composite window, so the annual P70 can mix observations from before and after the visible clearing event.

The older draft included images dated 2018-01-25 and 2026-07-13 that belonged to another site. They are excluded from the corrected evidence chain.
