#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import math
import json
import pandas as pd
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]


def ok(msg):
    print(f"[PASS] {msg}")


def fail(msg):
    raise AssertionError(msg)


def close(a, b, tol=1e-6):
    if not math.isclose(float(a), float(b), rel_tol=0, abs_tol=tol):
        fail(f"{a} != {b} (tol={tol})")


# Step 3A raw exports
s3a = ROOT / 'data/reference/step3a'
row_expect = {
    'SC0002_STEP3A_Baseline_Year_Sensitivity.csv': 3,
    'SC0002_STEP3A_2022_2026_Index_Ablation.csv': 3,
    'SC0002_STEP3A_PreDevelopment_Null_Comparisons.csv': 9,
    'SC0002_STEP3A_2023_Event_Window.csv': 5,
}
for name, n in row_expect.items():
    p = s3a / name
    if not p.is_file(): fail(f'missing Step 3A raw export: {name}')
    df = pd.read_csv(p)
    if len(df) != n: fail(f'{name}: expected {n} rows, found {len(df)}')
ok('Step 3A raw CSV export set is complete')

base = pd.read_csv(s3a / 'SC0002_STEP3A_Baseline_Year_Sensitivity.csv')
for y, area, pct in [
    (2020, 19.83911912767003, 32.18829995855562),
    (2021, 9.482106096418788, 22.526438161118464),
    (2022, 16.795013412664105, 28.83768578216494),
]:
    r = base.loc[base.baseline_year == y].iloc[0]
    close(r.combined_loss_ha, area, 1e-8)
    close(100 * r.combined_fraction_of_full_baseline, pct, 1e-8)
ok('Step 3A baseline-year sensitivity raw values match rerun reference')

abl = pd.read_csv(s3a / 'SC0002_STEP3A_2022_2026_Index_Ablation.csv')
for criterion, area in [
    ('NDVI_only_drop_ge_0.20', 17.08070465180643),
    ('NDMI_only_drop_ge_0.10', 24.54374238144223),
    ('NDVI_and_NDMI_combined', 16.795013412664105),
]:
    r = abl.loc[abl.criterion == criterion].iloc[0]
    close(r.loss_area_ha, area, 1e-8)
ok('Step 3A ablation raw values match rerun reference')

with rasterio.open(s3a / 'SC0002_STEP3A_2022_2026_Ablation_Masks.tif') as ds:
    if ds.crs.to_epsg() != 32651 or ds.count != 3 or abs(ds.transform.a - 10) > 1e-12:
        fail('Step 3A ablation raster metadata mismatch')
    expected = [
        {0: 4799, 1: 1724, 255: 1329},
        {0: 4032, 1: 2491, 255: 1329},
        {0: 4829, 1: 1694, 255: 1329},
    ]
    for i in range(3):
        vals, counts = np.unique(ds.read(i + 1), return_counts=True)
        got = dict(zip(vals.tolist(), counts.tolist()))
        if got != expected[i]: fail(f'Step 3A ablation raster band {i+1}: {got}')
ok('Step 3A ablation raster matches expected fixed-grid masks')

# Step 3A.1 raw exports
s3a1 = ROOT / 'data/reference/step3a1'
row_expect = {
    'SC0002_STEP3A1_Monthly_Stats_2022_2024.csv': 36,
    'SC0002_STEP3A1_Same_Month_Comparisons.csv': 24,
    'SC0002_STEP3A1_Bimonthly_Stats_2022_2024.csv': 18,
    'SC0002_STEP3A1_Same_Bimonth_Comparisons.csv': 12,
    'SC0002_STEP3A1_Fixed_2022_Baseline_Supplemental.csv': 12,
}
for name, n in row_expect.items():
    p = s3a1 / name
    if not p.is_file(): fail(f'missing Step 3A.1 raw export: {name}')
    df = pd.read_csv(p)
    if len(df) != n: fail(f'{name}: expected {n} rows, found {len(df)}')
ok('Step 3A.1 raw CSV export set is complete')

bi = pd.read_csv(s3a1 / 'SC0002_STEP3A1_Same_Bimonth_Comparisons.csv')
expected_bi = {
    (2023, 'Jan-Feb'): 29.82, (2024, 'Jan-Feb'): 31.01,
    (2023, 'Mar-Apr'): 56.09, (2024, 'Mar-Apr'): 43.86,
    (2023, 'May-Jun'): 12.76, (2024, 'May-Jun'): 9.71,
    (2023, 'Jul-Aug'): 15.75, (2024, 'Jul-Aug'): 14.68,
    (2023, 'Sep-Oct'): 9.27, (2024, 'Sep-Oct'): 14.22,
    (2023, 'Nov-Dec'): 0.76, (2024, 'Nov-Dec'): 5.04,
}
for (y, period), pct in expected_bi.items():
    r = bi.loc[(bi.target_year == y) & (bi.period_id == period)].iloc[0]
    close(100 * r.loss_fraction_full_baseline, pct, 0.12)
ok('Step 3A.1 same-bimonth raw values match validated reference')

# Step 3B.3 raw export
s3b3 = ROOT / 'data/reference/step3b3'
site = pd.read_csv(s3b3 / 'SC0002_STEP3B3_Site_Outcome_2022_2026.csv')
if len(site) != 30: fail(f'Step 3B.3 site outcome expected 30 rows, found {len(site)}')
expected_sites = {'SC0002', 'C162', 'C172', 'C176', 'C222', 'C129'}
if set(site.site_id.astype(str)) != expected_sites: fail('Step 3B.3 site set mismatch')
if set(site.year.astype(int)) != {2022, 2023, 2024, 2025, 2026}: fail('Step 3B.3 year set mismatch')
if not (site.groupby(['site_id', 'year']).size() == 1).all(): fail('Step 3B.3 duplicate/missing site-year rows')
if set(site.outcome_data_used_for_control_selection.astype(str).str.upper()) != {'NO'}:
    fail('Step 3B.3 provenance flag is not uniformly NO')

sc = site.loc[site.site_id == 'SC0002'].set_index('year')
for y, area, frac in [
    (2022, 58.23981001641681, 0.0),
    (2023, 14.947460851643925, 0.2566536677820633),
    (2024, 11.043817638214739, 0.1896266082444581),
    (2025, 21.545707303688257, 0.3699481041853483),
    (2026, 16.795013412664105, 0.2883768578216494),
]:
    r = sc.loc[y]
    close(r.baseline_veg_area_ha, 58.23981001641681, 1e-8)
    if y > 2022:
        close(r.loss_area_ha, area, 1e-8)
        close(r.loss_fraction_of_2022_baseline, frac, 1e-10)
    if float(r.baseline_veg_valid_fraction_this_year) < 0.999999:
        fail(f'Step 3B.3 SC0002 valid-baseline coverage unexpectedly low in {y}')
ok('Step 3B.3 raw 30-row site-outcome export matches treatment reference')

geo = s3b3 / 'SC0002_STEP3B3_Site_Geometries.geojson'
obj = json.loads(geo.read_text(encoding='utf-8'))
features = obj.get('features', [])
if len(features) != 6: fail('Step 3B.3 site geometry feature count is not 6')
if 'crs' in obj: fail('RFC 7946 GeoJSON must not carry a top-level custom CRS member')

def iter_xy(coords):
    if coords and isinstance(coords[0], (int, float)):
        yield float(coords[0]), float(coords[1])
    else:
        for c in coords:
            yield from iter_xy(c)

expected_centers = {
    'C162': (120.38336489647324, 22.81273725638963),
    'C172': (120.39532582798384, 22.69558044649453),
    'C176': (120.39464227305544, 22.731678010447084),
    'C222': (120.41324962396575, 22.77711658189245),
    'C129': (120.37535754400412, 22.72233523591619),
}
for feat in features:
    sid = feat.get('properties', {}).get('site_id')
    xy = list(iter_xy(feat['geometry']['coordinates']))
    if not xy: fail(f'{sid}: empty geometry')
    if not all(119.0 < x < 122.5 and 21.0 < y < 24.5 for x, y in xy):
        fail(f'{sid}: geometry is not WGS84 lon/lat in the Taiwan vicinity')
    if sid in expected_centers:
        xs=[x for x,_ in xy]; ys=[y for _,y in xy]
        cx=(min(xs)+max(xs))/2; cy=(min(ys)+max(ys))/2
        ex,ey=expected_centers[sid]
        if abs(cx-ex)>0.002 or abs(cy-ey)>0.002:
            fail(f'{sid}: WGS84 geometry center ({cx},{cy}) inconsistent with archived control center ({ex},{ey})')
raw_geo = s3b3 / 'SC0002_STEP3B3_Site_Geometries_GEE_RAW_MIXED_CRS.geojson'
if not raw_geo.is_file(): fail('missing preserved historical mixed-CRS GEE raw geometry export')
ok('Step 3B.3 canonical site geometry contains six RFC 7946 WGS84 sites; original mixed-CRS GEE raw export is preserved separately')

for sid in ['SC0002', 'C162', 'C172', 'C176', 'C222', 'C129']:
    p = s3b3 / f'SC0002_STEP3B3_LOSS_2022_2026_{sid}.tif'
    if not p.is_file(): fail(f'missing Step 3B.3 loss raster: {sid}')
    with rasterio.open(p) as ds:
        if ds.crs.to_epsg() != 32651 or ds.count != 1 or abs(ds.transform.a - 10) > 1e-12:
            fail(f'Step 3B.3 raster metadata mismatch: {sid}')
ok('Step 3B.3 six raw loss-mask GeoTIFFs are present on the fixed grid')

print('\nALL PASS — raw Step 3A, Step 3A.1, and Step 3B.3 GEE exports are complete and validated.')
