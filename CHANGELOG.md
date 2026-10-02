# Changelog

## v5.2 — path anchoring, packaging, and public site

- Anchored the default `--results-dir` / `--rasters-dir` paths in
  `verify_archived_results.py` and `verify_rasters.py` to the repository root, so
  every verifier now runs from any current working directory.
- Removed `__pycache__` bytecode that had been included in the distributed package.
- Added a static summary page under `site/`, published from a Vercel project whose
  root directory is `site/`, so the archive can go online without putting any web
  file beside the analysis tree.
- Added `.vercel/` to `.gitignore` and to the `verify_sha256.py` runtime-ignore
  set, so running the Vercel CLI in a clone does not invalidate the manifest.
- No scientific inputs, thresholds, archived raw GEE results, control selection, or
  published numerical results changed.

## v5.1 — portability and byte-reproducibility fixes

- Removed the stray leading backslash before the shebang in `verify_step3b1_archive.py` and restored executable mode for direct Unix invocation.
- Made Step 3B.3/3B.4 CSV and summary writers emit deterministic LF line endings on Windows, macOS, and Linux.
- Strengthened `verify_analysis_rebuild.py` to require byte-identical rebuilt CSV/Summary outputs, not only newline-normalized semantic equality.
- Anchored `verify_aoi.py` default AOI and GEE-script paths to the repository root so it works from any current working directory.
- No scientific inputs, thresholds, archived raw GEE results, control selection, or published numerical results changed.

## v5 — audit/reviewer fixes

- Fixed `verify_sha256.py` so documented `.venv`/`venv`/`__pycache__` and other ignored runtime outputs do not invalidate the manifest; CI now creates `.venv` explicitly.
- Corrected the Step 3B.3 six-site GeoJSON to RFC 7946 WGS84; preserved the original mixed-CRS GEE export separately and fixed GEE script 07 for future reruns.
- Corrected Step 3B.1 method wording: `match_score` has nine spectral/terrain terms; valid observations are a hard screen and distance defines the candidate-search ring.
- Strengthened verification by independently recomputing all 432 `match_score`/`match_pass` values and checking all seven embedded GEE AOIs against the archived AOI.
- Added WGS84 geometry validation and exact `Summary.txt` rebuild checks.
- Updated quick-verification output, provenance, and README interpretation caveats.

## v4 — full control-design audit archive

- Archived the full Step 3B.1 candidate chain: 432 all candidates, 60 hard-pass candidates, Top20, and SC0002 reference covariates.
- Archived all 20 Top20 Sentinel-2 RGB review contact sheets.
- Archived original 147-row review metadata plus a Top20-only 140-row metadata table.
- Added a contact-sheet audit index linking rank/candidate to screen decision and final-control status.
- Added offline verifiers for the 432→60→Top20 chain and the RGB review archive.
- Integrated both checks into `verify_all.py` and CI.


## v3 — raw GEE archive closure

- Reran Step 3A, Step 3A.1, and Step 3B.3 on 2026-10-02 using the public self-contained GEE scripts.
- Archived the Step 3A raw CSVs and three-band ablation raster.
- Archived all five Step 3A.1 raw CSVs.
- Archived the Step 3B.3 30-row site-outcome CSV, six loss-mask GeoTIFFs, and six-site GeoJSON.
- Regenerated Step 3B.3 and Step 3B.4 derived tables from the archived raw 30-row CSV; published rounded results are unchanged.
- Added `verify_raw_exports.py` and `verify_analysis_rebuild.py` and integrated them into `verify_all.py` / CI.
- Closed the previously documented raw-output archive gaps and added rerun provenance.

## v2 — reproducibility/public-release fixes

- Removed all hard-coded/private GCP project identifiers from public GEE scripts.
- Embedded the exact archived V4 AOI geometry in each GEE script.
- Fixed Git EOL/hash reproducibility and added cross-platform SHA256 verification.
- Fixed verifier default paths and replaced the dead legacy manifest verifier.
- Added a one-command `verify_all.py` path and CI coverage.
- Added control-selection reproduction and post-treatment-screening invariance sensitivity.
- Expanded limitations for RGB selection bias, 2025–2026 government-data blind spot, valid-domain asymmetry, SCL class 2, B11 native 20 m support, AOI envelope design, and 2018 low-observation data.
- Explicitly documented missing raw Step 3A/3A.1 and Step 3B.3 site-outcome exports rather than reconstructing them from published values.

## GitHub-ready packaging

- Reorganized the root README around reviewer verification and full reproduction.
- Added `docs/VERIFY.md`, `docs/AUDIT_TRAIL.md`, and `docs/PUBLISH_TO_GITHUB.md`.
- Added `verify.ps1` and `verify.sh` convenience wrappers.
- Preserved the complete Step 3B.1 candidate archive and Step 3B.2 RGB review archive.
- No scientific thresholds, archived results, control set, or interpretation boundaries were changed.
