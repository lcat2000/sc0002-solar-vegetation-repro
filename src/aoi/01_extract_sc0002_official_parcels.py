#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SC0002 Step 1: Read official solar parcel tables and extract
Kaohsiung / Dashu / Sanhe Section records.

Input:
  A folder containing official Energy Administration CSV/XLSX/ODS files.

Output:
  SC0002_Official_Parcels.csv

This script does NOT invent coordinates.
Coordinates are obtained in Step 2 from the NLSC public cadastral locator.
"""

import argparse
import re
from pathlib import Path
import pandas as pd

SUPPORTED = {".csv", ".xlsx", ".xls", ".ods"}

KAOHSIUNG_NAMES = {"高雄市", "高雄", "Kaohsiung", "Kaohsiung City"}

COL_ALIASES = {
    "city": ["縣市", "縣市別", "所在縣市", "city", "county", "city_name"],
    "district": ["行政區", "鄉鎮市區", "區", "district", "town", "township"],
    "section": ["地段", "段名", "段", "section", "land_section"],
    "lot": ["地號", "土地地號", "lot", "parcel", "parcel_no", "land_no"],
    "site_name": ["案場名稱", "電廠名稱", "計畫名稱", "場址名稱", "site_name", "project_name", "plant_name"],
    "operator": ["業者", "申請人", "公司名稱", "設置者", "operator", "company", "applicant"],
    "capacity_kw": ["裝置容量", "容量(kW)", "容量kw", "容量", "capacity_kw", "capacity"],
    "permit_year": ["年度", "許可年度", "year", "permit_year"],
    "solar_type": ["類型", "案場類型", "設置型態", "solar_type", "type"],
}

def norm_text(x):
    if pd.isna(x):
        return ""
    return re.sub(r"\s+", "", str(x)).strip().replace("台", "臺")

def find_col(df, aliases):
    lower = {str(c).strip().lower(): c for c in df.columns}
    for a in aliases:
        if a.lower() in lower:
            return lower[a.lower()]
    for c in df.columns:
        c0 = str(c).strip().lower()
        for a in aliases:
            if a.lower() in c0 or c0 in a.lower():
                return c
    return None

def read_table(path):
    suf = path.suffix.lower()
    if suf == ".csv":
        for enc in ("utf-8-sig", "utf-8", "cp950", "big5"):
            try:
                return pd.read_csv(path, encoding=enc)
            except Exception:
                pass
        return pd.read_csv(path)
    if suf in (".xlsx", ".xls"):
        return pd.read_excel(path)
    if suf == ".ods":
        return pd.read_excel(path, engine="odf")
    raise ValueError(path)

def infer_year(filename):
    m = re.search(r"(?<!\d)(10[8-9]|11[0-3])年度?", filename)
    return m.group(1) if m else ""

def normalize_one(df, source_name):
    out = pd.DataFrame(index=df.index)
    for key, aliases in COL_ALIASES.items():
        c = find_col(df, aliases)
        out[key] = df[c] if c is not None else ""

    for c in ["city","district","section","lot","site_name","operator","solar_type"]:
        out[c] = out[c].map(norm_text)

    out["capacity_kw"] = pd.to_numeric(out["capacity_kw"], errors="coerce")
    out["source_file"] = source_name

    inferred = infer_year(source_name)
    py = out["permit_year"].astype(str).str.strip()
    out["permit_year"] = py.where(py.ne(""), inferred)

    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solar-source", required=True, help="Folder containing official CSV/XLSX/ODS files")
    ap.add_argument("--out", default="SC0002_Official_Parcels.csv")
    args = ap.parse_args()

    files = [p for p in Path(args.solar_source).rglob("*") if p.suffix.lower() in SUPPORTED]
    if not files:
        raise SystemExit("No CSV/XLSX/ODS files found.")

    frames = []
    for p in files:
        try:
            df = read_table(p)
            n = normalize_one(df, p.name)
            frames.append(n)
            print(f"[OK] {p.name}: {len(n)} source rows")
        except Exception as e:
            print(f"[WARN] {p.name}: {e}")

    if not frames:
        raise SystemExit("No readable tables.")

    all_df = pd.concat(frames, ignore_index=True)

    # Exact normalized filter.
    m = (
        all_df["city"].str.contains("高雄", na=False)
        & all_df["district"].eq("大樹區")
        & all_df["section"].eq("三和段")
        & all_df["lot"].ne("")
    )
    sc = all_df[m].copy()

    # Exact duplicate parcel rows can occur across source tables.
    # Keep every government record, but add a stable local ID.
    sc.insert(0, "sc_record_id", range(1, len(sc)+1))
    sc = sc.sort_values(["permit_year","lot","source_file"], kind="stable")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sc.to_csv(out, index=False, encoding="utf-8-sig")

    print()
    print("="*64)
    print("SC0002 official parcel extraction complete")
    print(f"Rows: {len(sc)}")
    print(f"District: 大樹區")
    print(f"Section: 三和段")
    print(f"Output: {out.resolve()}")
    if len(sc) != 93:
        print()
        print("[NOTE] Historical SC0002 had 93 parcel records.")
        print("       A different count can be caused by official-data revisions,")
        print("       duplicate policy, or changed year coverage. Do NOT force 93.")

if __name__ == "__main__":
    main()
