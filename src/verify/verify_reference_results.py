#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import math
import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[2]

def ok(msg): print(f"[PASS] {msg}")
def fail(msg): raise AssertionError(msg)
def close(a,b,tol=1e-6):
    if not math.isclose(float(a),float(b),rel_tol=0,abs_tol=tol):
        fail(f"{a} != {b} (tol={tol})")

# 1) Step 2 formal results
s2=ROOT/'data/reference/step2'
ts=pd.read_csv(s2/'SC0002_Loss_TimeSeries_2022_2026_UTM51N_V4.csv')
for y,a,f in [(2023,14.947461,0.256654),(2024,11.043818,0.189627),(2025,21.545707,0.369948),(2026,16.795013,0.288377)]:
    r=ts.loc[ts.target_year==y].iloc[0]; close(r.spectral_loss_ha,a,2e-6); close(r.loss_fraction_of_2022_baseline,f,2e-6)
ok('Step 2 annual loss time series matches archived V4 reference')

sens=pd.read_csv(s2/'SC0002_Threshold_Sensitivity_UTM51N_V4.csv')
for k,a in [('loose',19.529414),('standard',16.795013),('strict',14.498828)]:
    r=sens.loc[sens.threshold_name.str.lower()==k].iloc[0]; close(r.spectral_loss_ha,a,2e-6)
ok('Threshold sensitivity matches archived reference')

# 2) Raster QA
with rasterio.open(s2/'SC0002_Spectral_Vegetation_Loss_2022_2026_UTM51N_V4.tif') as ds:
    if ds.crs.to_epsg()!=32651: fail('Main raster CRS')
    vals,counts=np.unique(ds.read(1),return_counts=True); d=dict(zip(vals.tolist(),counts.tolist()))
    if d!={0:4829,1:1694,255:1329}: fail(f'Main raster counts {d}')
ok('Main loss raster CRS and pixel counts match reference')

# 3) Frozen controls / provenance
controls=pd.read_csv(ROOT/'data/reference/step3b2/SC0002_STEP3B2_Selected_Controls.csv')
ids=controls.sort_values('selected_control_order').candidate_id.tolist(); exp=['C162','C172','C176','C222','C129']
if ids!=exp: fail(f'Frozen controls {ids}')
if set(controls.outcome_data_used_for_selection.astype(str).str.upper())!={'NO'}: fail('Outcome-blind selection provenance')
ok('Frozen control set and outcome-blind provenance match reference')

# 4) Step 3B.3 documented table
b3=pd.read_csv(ROOT/'data/reference/step3b3/SC0002_STEP3B3_Treatment_vs_Control.csv')
expected={
2023:(0.2566536677820633,0.007327429151113419,0.0045190373231734,0.0015008705483439,0.0152414460626738,24.932623863094985),
2024:(0.1896266082444581,0.005212486660396474,0.0043375236622763,0.0,0.0145339893210956,18.441412158406163),
2025:(0.3699481041853483,0.007136454502398774,0.0070039924316912,0.00016676298813357603,0.0117744182282636,36.28116496829495),
2026:(0.2883768578216494,0.013007871031431098,0.0114632382638052,0.0004793613065256882,0.0225004723398132,27.53689867902183),}
for y,v in expected.items():
    r=b3.loc[b3.year==y].iloc[0]
    for col,val in zip(['treatment_loss_fraction','control_mean_loss_fraction','control_median_loss_fraction','control_min_loss_fraction','control_max_loss_fraction','difference_vs_control_mean_pp'],v): close(r[col],val,1e-9)
    if int(r.treatment_rank_desc_among_6)!=1 or int(r.controls_ge_treatment)!=0: fail(f'3B.3 ranking {y}')
ok('Step 3B.3 mean/median/range/difference table matches reference')

rank=pd.read_csv(ROOT/'data/reference/step3b3/SC0002_STEP3B3_2026_Site_Ranking.csv').sort_values('rank_loss_fraction_desc')
if rank.site_id.tolist()!=['SC0002','C162','C176','C172','C222','C129']: fail('2026 ranking order')
ok('Step 3B.3 2026 site ranking matches reference')

# 5) Step 3B.4 documented sensitivity tables
agg=pd.read_csv(ROOT/'data/reference/step3b4/SC0002_STEP3B4_Aggregation_Sensitivity.csv')
for y,gap in [(2023,24.14122217193895),(2024,17.50926189233625),(2025,35.81736859570847),(2026,26.587638548183623)]:
    r=agg.loc[agg.year==y].iloc[0]; close(r.diff_vs_control_max_pp,gap,1e-9)
    for c in ['treatment_gt_control_mean','treatment_gt_control_median','treatment_gt_trimmed_mean','treatment_gt_every_control']:
        if str(r[c]).lower()!='true': fail(f'3B.4 {c} {y}')
env=pd.read_csv(ROOT/'data/reference/step3b4/SC0002_STEP3B4_Robustness_By_Year.csv')
for y,gap in [(2023,24.78695989802575),(2024,18.311099991896253),(2025,36.106922680438316),(2026,27.223685935899194)]:
    r=env.loc[env.year==y].iloc[0]; close(r.smallest_treatment_minus_loo_mean_pp,gap,1e-9)
    for c in ['all_5_loo_means_below_treatment','all_5_loo_sets_have_all_controls_below_treatment','valid_data_guardrail_pass']:
        if str(r[c]).lower()!='true': fail(f'3B.4 {c} {y}')
ok('Step 3B.4 conservative-gap, LOO-envelope, and coverage checks match reference')

print('\nALL PASS — archived SC0002 reference results are internally consistent.')
