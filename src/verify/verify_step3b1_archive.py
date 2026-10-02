#!/usr/bin/env python3
from pathlib import Path
import csv, math

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data/reference/step3b1"
ALL = D / "SC0002_STEP3B1_All_Control_Candidates.csv"
HARD = D / "SC0002_STEP3B1_HardPass_Control_Candidates.csv"
TOP = D / "SC0002_STEP3B1_Top20_Control_Candidates.csv"
REF = D / "SC0002_STEP3B1_SC0002_Reference_Covariates.csv"

EXPECTED_TOP = ["C162","C185","C172","C176","C222","C129","C221","C177","C290","C264","C268","C269","C152","C146","C241","C171","C291","C179","C153","C313"]
SCORE_SCALES = {
    'NDVI_2020': 0.08, 'NDMI_2020': 0.08,
    'NDVI_2021': 0.08, 'NDMI_2021': 0.08,
    'NDVI_2022': 0.08, 'NDMI_2022': 0.08,
    'BASEVEG_2022': 0.10,
    'ELEV_M': 75.0,
    'SLOPE_DEG': 4.0,
}

def read(p):
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def fail(msg): raise AssertionError(msg)
def f(row, key): return float(row[key])

def recompute_score(row, ref):
    return sum(((f(row, k) - f(ref, k)) / scale) ** 2 for k, scale in SCORE_SCALES.items())

def recompute_pass(row, ref):
    return (
        f(row, 'VALID_2020') >= 10 and f(row, 'VALID_2021') >= 10 and f(row, 'VALID_2022') >= 10 and
        f(row, 'BASEVEG_2022') >= 0.75 and
        abs(f(row, 'NDVI_2022') - f(ref, 'NDVI_2022')) <= 0.10 and
        abs(f(row, 'NDMI_2022') - f(ref, 'NDMI_2022')) <= 0.10 and
        abs(f(row, 'BASEVEG_2022') - f(ref, 'BASEVEG_2022')) <= 0.15 and
        abs(f(row, 'ELEV_M') - f(ref, 'ELEV_M')) <= 120 and
        abs(f(row, 'SLOPE_DEG') - f(ref, 'SLOPE_DEG')) <= 6
    )

def main():
    a=read(ALL); h=read(HARD); t=read(TOP); r=read(REF)
    if len(a)!=432: fail(f"all candidates {len(a)} != 432")
    if len({x['candidate_id'] for x in a})!=432: fail("candidate IDs not unique")
    if len(r)!=1: fail(f"reference covariates rows {len(r)} != 1")
    ref=r[0]
    for row in a:
        score=recompute_score(row,ref)
        if not math.isclose(score,f(row,'match_score'),rel_tol=0,abs_tol=1e-10):
            fail(f"{row['candidate_id']}: recomputed match_score {score} != archived {row['match_score']}")
        passed=1 if recompute_pass(row,ref) else 0
        if passed!=int(float(row['match_pass'])):
            fail(f"{row['candidate_id']}: recomputed match_pass {passed} != archived {row['match_pass']}")
    hp=sorted([x for x in a if recompute_pass(x,ref)],key=lambda x:(recompute_score(x,ref),x['candidate_id']))
    if len(hp)!=60: fail(f"hard-pass count {len(hp)} != 60")
    if len(h)!=60: fail(f"archived hard-pass rows {len(h)} != 60")
    if [x['candidate_id'] for x in h] != [x['candidate_id'] for x in hp]: fail("hard-pass archive is not the recomputed sorted hard-pass subset")
    if len(t)!=20: fail(f"Top20 rows {len(t)} != 20")
    got=[x['candidate_id'] for x in t]
    if got!=EXPECTED_TOP: fail(f"unexpected Top20 order: {got}")
    if got!=[x['candidate_id'] for x in hp[:20]]: fail("Top20 is not first 20 recomputed hard-pass candidates by match_score")
    for label,rows in [('all',a),('hard',h),('top20',t)]:
        if set(x.get('outcome_data_used_for_ranking','').upper() for x in rows)!={'NO'}: fail(f"{label}: outcome ranking provenance not uniformly NO")
        if set(x.get('selection_data_end','') for x in rows)!={'2022-12-31'}: fail(f"{label}: unexpected selection_data_end")
    print("PASS — Step 3B.1 independently recomputes all 432 match_score/match_pass values from pre-treatment inputs, reproducing 60 hard-pass candidates and the exact Top20 order.")

if __name__=='__main__': main()
