#!/usr/bin/env python3
from pathlib import Path
import math
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/reference/step3b2/SC0002_STEP3B2_Control_Screening_Completed.csv"
EXPECTED = ["C162", "C172", "C176", "C222", "C129"]
MIN_SEP_M = 2000.0
MAX_N = 5


def haversine_m(lon1, lat1, lon2, lat2):
    r = 6371008.8
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2-lat1)
    dl = math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(a))


def select(df):
    passed = df[df["screen_pass"].astype(str).str.upper() == "YES"].copy()
    passed = passed.sort_values(["match_score", "rank", "candidate_id"])
    selected = []
    for _, row in passed.iterrows():
        if all(haversine_m(row.center_lon, row.center_lat, s.center_lon, s.center_lat) >= MIN_SEP_M
               for s in selected):
            selected.append(row)
        if len(selected) == MAX_N:
            break
    return [r.candidate_id for r in selected]


def scenario(df, name, force_ids=(), force_all=False):
    x = df.copy()
    if force_all:
        x["screen_pass"] = "YES"
    elif force_ids:
        x.loc[x["candidate_id"].isin(force_ids), "screen_pass"] = "YES"
    got = select(x)
    print(f"{name:32s} -> {','.join(got)}")
    if got != EXPECTED:
        raise AssertionError(f"{name}: {got} != {EXPECTED}")
    return got


def main():
    df = pd.read_csv(SRC)
    scenario(df, "original screening")
    scenario(df, "force C221 pass", ["C221"])
    scenario(df, "force C171 pass", ["C171"])
    scenario(df, "force C221+C171 pass", ["C221","C171"])
    scenario(df, "force all Top20 pass", force_all=True)
    print("PASS — exact selection rule reproduces the frozen controls, and the final five are invariant to forcing the visually excluded candidates (or all Top20) to pass.")

if __name__ == "__main__":
    main()
