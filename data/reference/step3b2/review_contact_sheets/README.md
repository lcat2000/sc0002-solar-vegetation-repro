# Step 3B.2 RGB review contact sheets

This directory archives the **20** Sentinel-2 annual true-color contact sheets used for treatment-status / major-development screening of the Top-20 control candidates.

Each sheet shows annual RGB median imagery for 2020–2026. These images were used only for visual treatment-status screening; they were not NDVI/NDMI numerical outcome inputs.

Associated metadata:

- `../SC0002_STEP3B2_Top20_Review_Image_Metadata.csv` — **140 rows = 20 controls × 7 years**.
- `../SC0002_STEP3B2_Review_Image_Metadata.csv` — the original **147-row** export, including SC0002 plus the 20 controls.
- `../SC0002_STEP3B2_Review_Contact_Sheet_Index.csv` — maps each Top20 rank/candidate to its contact sheet, screen decision, and final-control status.

The treatment-site `SC0002_review_contact_sheet.png` is intentionally not included here because this directory is the control-review archive; the original metadata file retains the SC0002 rows for provenance.

Important limitation: post-treatment true-color screening can, in principle, correlate with spectral outcomes. The repository therefore separately verifies that forcing the visually excluded candidates—or all Top20 candidates—to pass does not change the final five controls under the fixed spatial-selection rule (`verify_control_selection.py`).
