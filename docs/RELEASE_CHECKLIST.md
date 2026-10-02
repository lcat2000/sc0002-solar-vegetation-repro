# Public release checklist

- [x] Remove private/hard-coded GCP project IDs from all GEE scripts.
- [x] Embed exact archived V4 AOI geometry in all GEE scripts.
- [x] Normalize all repository text files to LF.
- [x] Add `*.txt` and global text LF policy to `.gitattributes`.
- [x] Rebuild `SHA256SUMS.txt` after normalization.
- [x] Verify hashes in CI.
- [x] Fix `verify_archived_results.py` default paths.
- [x] Fix `verify_rasters.py` default paths.
- [x] Remove dead `verify_manifest_legacy.py`; add `verify_sha256.py`.
- [x] Add `verify_all.py`.
- [x] Add geopandas/pyproj stack to `requirements-verify.txt`.
- [x] Add `xlrd` for advertised `.xls` support.
- [x] Document exact control selection rule in English README.
- [x] Add post-treatment RGB screening bias limitation and selection-invariance check.
- [x] Document 2019–2024 official-data time scope / 2025–2026 blind spot.
- [x] Document denominator valid-domain asymmetry.
- [x] Document retained SCL class 2.
- [x] Document B11 native 20 m support.
- [x] Document analytical-envelope AOI limitation.
- [x] Normalize archived AOI property names while preserving geometry.
- [x] Mark 2018 low-observation composite as exploratory.
- [x] Add `.github/` and `SHA256SUMS.txt` to repository documentation.
- [x] Archive Step 3A raw GEE export CSVs and ablation raster from the 2026-10-02 rerun.
- [x] Archive Step 3A.1 raw GEE export CSVs from the 2026-10-02 rerun.
- [x] Archive Step 3B.3 raw 30-row site-outcome CSV and six loss rasters; preserve the original mixed-CRS geometry export and provide a verified canonical RFC 7946 WGS84 site-geometry file.

All public-release reproducibility items are now checked.

## Control-design audit archive

- [x] 432-row Step 3B.1 all-candidate export archived
- [x] 60-row hard-pass candidate table archived and derivable from the 432-row export
- [x] Top20 order offline-verifiable
- [x] 20 Top20 RGB review contact sheets archived
- [x] 140-row Top20 annual image metadata archived
- [x] Contact-sheet audit index links rank, candidate, screen decision, and final selection
- [x] `verify_step3b1_archive.py` PASS
- [x] `verify_step3b2_review_archive.py` PASS
