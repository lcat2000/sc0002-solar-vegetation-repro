# Step 3B.1 full candidate archive

This directory archives the complete pre-treatment candidate-selection input chain.

Files:

- `SC0002_STEP3B1_All_Control_Candidates.csv` — all **432** deterministic grid candidates exported by GEE.
- `SC0002_STEP3B1_HardPass_Control_Candidates.csv` — the **60** candidates with `match_pass=1`, sorted by ascending `match_score`.
- `SC0002_STEP3B1_Top20_Control_Candidates.csv` — ranked Top-20 table used by downstream screening.
- `SC0002_STEP3B1_Top20_Control_Candidates_GEE_RAW.csv` — original GEE Top20 export; row order is the rank.
- `SC0002_STEP3B1_SC0002_Reference_Covariates.csv` — the treatment-site pre-treatment reference covariates used by the matching script.

All ranking variables are pre-treatment variables. `outcome_data_used_for_ranking=NO` and `selection_data_end=2022-12-31` are retained in the exported candidate tables.

The verifier `src/verify/verify_step3b1_archive.py` checks the complete offline chain:

```text
432 candidates
→ 60 hard-pass candidates
→ sort by match_score
→ first 20 = archived Top20
```

The spatial WGS84 Top20 review geometry is archived separately under `data/reference/step3b2/`.
