#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Normalize Energy Administration solar-land files and extract Kaohsiung parcel
records for the validated historical screening period ROC 108-113 (2019-2024).

Source dataset:
取得電業設置發電設備工作許可證太陽光電案場土地地號
Energy Administration, MOEA
metadata set_id=344

Important implementation details:
1) Some source spreadsheets contain title/update rows before the true header.
   The reader auto-detects the row containing:
   申請年度 / 縣市 / 鄉鎮區 / 地段 / 地號.
2) Spreadsheet merged cells can appear as blank/NaN continuation rows after
   pandas import. Hierarchical/project fields are forward-filled:
   permit_year, city, district, section, site_name, operator, capacity_kw,
   solar_type.
   The parcel lot number is NEVER forward-filled.
3) Percent-encoded downloaded filenames are decoded before filename-year
   fallback.
"""

import argparse
import hashlib
import re
from pathlib import Path
from urllib.parse import unquote

import pandas as pd

SUPPORTED = {".csv", ".xlsx", ".xls", ".ods"}

COL_ALIASES = {
    "city": [
        "縣市", "縣市別", "所在縣市",
        "city", "county", "city_name",
    ],
    "district": [
        "行政區", "鄉鎮區", "鄉鎮市區", "鄉鎮市",
        "district", "town", "township",
    ],
    "section": [
        "地段", "段名", "section", "land_section",
    ],
    "lot": [
        "地號", "土地地號", "lot", "parcel", "parcel_no", "land_no",
    ],
    "site_name": [
        "案場名稱", "電廠名稱", "計畫名稱", "場址名稱",
        "site_name", "project_name", "plant_name",
    ],
    "operator": [
        "業者", "業者名稱", "申請人", "公司名稱", "設置者",
        "operator", "company", "applicant",
    ],
    "capacity_kw": [
        "裝置容量", "容量(kW)", "容量kw", "容量",
        "capacity_kw", "capacity",
    ],
    "permit_year": [
        "申請年度", "年度", "許可年度", "year", "permit_year",
    ],
    "solar_type": [
        "類型", "案場類型", "設置型態", "solar_type", "type",
    ],
}

DEFAULT_YEARS = {"108", "109", "110", "111", "112", "113"}

HEADER_REQUIRED_GROUPS = [
    {"申請年度", "年度", "許可年度"},
    {"縣市", "縣市別", "所在縣市"},
    {"鄉鎮區", "鄉鎮市區", "行政區", "鄉鎮市"},
    {"地段", "段名"},
    {"地號", "土地地號"},
]

FORWARD_FILL_FIELDS = [
    "permit_year",
    "city",
    "district",
    "section",
    "site_name",
    "operator",
    "capacity_kw",
    "solar_type",
]


def norm_text(x):
    if pd.isna(x):
        return ""
    return re.sub(r"\s+", "", str(x)).strip().replace("台", "臺")


def norm_col(x):
    return re.sub(r"[\s_\-()（）]+", "", str(x or "")).strip().lower()


def blank_to_na(series):
    s = series.copy()
    mask = s.isna() | s.astype(str).str.strip().isin(
        ["", "nan", "None", "<NA>"]
    )
    return s.mask(mask, pd.NA)


def find_col(df, aliases, field_name):
    columns = list(df.columns)
    normalized = {c: norm_col(c) for c in columns}
    aliases_n = [norm_col(a) for a in aliases if norm_col(a)]

    exact = [c for c, cn in normalized.items() if cn in aliases_n]
    exact = list(dict.fromkeys(exact))

    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise ValueError(
            f"Ambiguous exact columns for {field_name}: {exact}"
        )

    fuzzy = []
    for c, cn in normalized.items():
        for an in aliases_n:
            if len(an) < 2:
                continue
            if an in cn or cn in an:
                fuzzy.append(c)
                break

    fuzzy = list(dict.fromkeys(fuzzy))

    if len(fuzzy) == 1:
        return fuzzy[0]
    if len(fuzzy) > 1:
        raise ValueError(
            f"Ambiguous fuzzy columns for {field_name}: {fuzzy}"
        )

    return None


def read_csv_any(path, header=0):
    last = None
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5"):
        try:
            return pd.read_csv(path, encoding=enc, header=header)
        except Exception as e:
            last = e
    if last:
        raise last
    raise RuntimeError(f"Could not read CSV: {path}")


def read_sheet(path, header=0):
    suf = path.suffix.lower()

    if suf == ".csv":
        return read_csv_any(path, header=header)

    if suf in (".xlsx", ".xls"):
        return pd.read_excel(path, header=header)

    if suf == ".ods":
        return pd.read_excel(path, engine="odf", header=header)

    raise ValueError(path)


def header_row_score(values):
    cells = {norm_col(v) for v in values if norm_col(v)}
    score = 0

    for group in HEADER_REQUIRED_GROUPS:
        aliases = {norm_col(x) for x in group}
        if cells.intersection(aliases):
            score += 1

    return score


def detect_header_row(path, max_rows=20):
    """
    Read first rows without a header and identify the row containing the
    official column names. Returns zero-based row number.
    """
    raw = read_sheet(path, header=None)
    limit = min(max_rows, len(raw))

    best_row = 0
    best_score = -1

    for i in range(limit):
        score = header_row_score(raw.iloc[i].tolist())

        if score > best_score:
            best_score = score
            best_row = i

        if score == len(HEADER_REQUIRED_GROUPS):
            return i, score

    return best_row, best_score


def read_table(path):
    header_row, score = detect_header_row(path)

    # Require at least city + district + section + lot, with year usually the
    # fifth hit. A score of 4 is accepted because some old files may omit year
    # from the header and rely on filename fallback.
    if score < 4:
        raise RuntimeError(
            f"Could not reliably detect official header row "
            f"(best row={header_row}, score={score}/5)"
        )

    return read_sheet(path, header=header_row), header_row, score


def infer_year(filename):
    decoded = unquote(filename)
    m = re.search(r"(?<!\d)(1\d{2})年度?", decoded)
    return m.group(1) if m else ""


def record_key(row):
    raw = "|".join(
        str(row.get(k, ""))
        for k in (
            "permit_year",
            "city",
            "district",
            "section",
            "lot",
            "site_name",
            "operator",
            "source_file",
        )
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def normalize_one(df, source_name):
    out = pd.DataFrame(index=df.index)
    resolved = {}

    for key, aliases in COL_ALIASES.items():
        c = find_col(df, aliases, key)
        resolved[key] = c
        out[key] = df[c] if c is not None else pd.NA

    if (
        resolved.get("section") is not None
        and resolved.get("section") == resolved.get("lot")
    ):
        raise ValueError(
            "section and lot resolved to the same source column: "
            + repr(resolved["section"])
        )

    # Merged spreadsheet cells are read as blanks on continuation rows.
    # Forward-fill only project/hierarchy fields, NEVER parcel lot.
    for c in FORWARD_FILL_FIELDS:
        out[c] = blank_to_na(out[c]).ffill()

    for c in [
        "city",
        "district",
        "section",
        "lot",
        "site_name",
        "operator",
        "solar_type",
    ]:
        out[c] = out[c].map(norm_text)

    out["source_file"] = source_name

    inferred = infer_year(source_name)

    py = blank_to_na(out["permit_year"]).astype("string")
    py = py.fillna(inferred)

    # Accept values such as 108, 108.0, 108年, 民國108年.
    out["permit_year"] = (
        py.astype(str)
        .str.extract(r"(?<!\d)(1\d{2})(?!\d)", expand=False)
        .fillna(inferred)
    )

    out["capacity_kw"] = pd.to_numeric(
        out["capacity_kw"],
        errors="coerce",
    )

    return out, resolved


def print_source_diagnostics(source_name, df, header_row, header_score, normalized, resolved):
    print(f"[FILE] {source_name}")
    print(
        f"       detected header row={header_row} "
        f"(score={header_score}/5)"
    )
    print(f"       columns={list(df.columns)}")
    print(
        "       resolved: "
        f"year={resolved.get('permit_year')!r}, "
        f"city={resolved.get('city')!r}, "
        f"district={resolved.get('district')!r}, "
        f"section={resolved.get('section')!r}, "
        f"lot={resolved.get('lot')!r}"
    )

    lots = normalized["lot"].ne("").sum()
    kaoh = normalized["city"].str.contains("高雄", na=False).sum()

    print(
        f"[OK]   normalized rows={len(normalized)}, "
        f"non-empty lot rows={lots}, "
        f"rows carrying Kaohsiung after forward-fill={kaoh}"
    )


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("--solar-source", required=True)
    ap.add_argument(
        "--out",
        default="Kaohsiung_Official_Solar_Parcels_108_113.csv",
    )
    ap.add_argument(
        "--years",
        nargs="*",
        default=sorted(DEFAULT_YEARS),
    )
    args = ap.parse_args()

    wanted_years = {str(x) for x in args.years}

    files = [
        p
        for p in Path(args.solar_source).rglob("*")
        if p.suffix.lower() in SUPPORTED
        and not p.name.startswith("_moeaea_solar_land_metadata")
    ]

    if not files:
        raise SystemExit(
            "No source CSV/XLS/XLSX/ODS files found."
        )

    frames = []

    for p in sorted(files):
        try:
            df, header_row, header_score = read_table(p)
            normalized, resolved = normalize_one(df, p.name)

            print_source_diagnostics(
                p.name,
                df,
                header_row,
                header_score,
                normalized,
                resolved,
            )

            frames.append(normalized)

        except Exception as e:
            print(f"[WARN] {p.name}: {e}")

    if not frames:
        raise SystemExit(
            "No readable official tables."
        )

    all_df = pd.concat(frames, ignore_index=True)

    # Keep only real parcel rows.
    valid_parcel = (
        all_df["permit_year"].isin(wanted_years)
        & all_df["city"].str.contains("高雄", na=False)
        & all_df["district"].ne("")
        & all_df["section"].ne("")
        & all_df["lot"].ne("")
    )

    out = all_df[valid_parcel].copy()

    # Remove exact duplicate parcel rows caused by source duplication while
    # preserving distinct site/operator records if the same parcel occurs in
    # more than one official record.
    dedup_cols = [
        "permit_year",
        "city",
        "district",
        "section",
        "lot",
        "site_name",
        "operator",
        "source_file",
    ]
    before_dedup = len(out)
    out = out.drop_duplicates(subset=dedup_cols, keep="first").copy()

    out = out.sort_values(
        [
            "permit_year",
            "district",
            "section",
            "lot",
            "source_file",
        ],
        kind="stable",
    ).reset_index(drop=True)

    out.insert(
        0,
        "official_record_id",
        range(1, len(out) + 1),
    )
    out.insert(
        1,
        "record_key",
        [record_key(r) for _, r in out.iterrows()],
    )

    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)

    out.to_csv(
        dest,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print("=" * 72)
    print(f"Kaohsiung official parcel rows : {len(out)}")
    print(f"Duplicate rows removed         : {before_dedup - len(out)}")
    print(f"Years requested                : {', '.join(sorted(wanted_years))}")
    print()

    if not out.empty:
        print("Rows by ROC year:")
        by_year = (
            out.groupby("permit_year")
            .size()
            .reindex(sorted(wanted_years), fill_value=0)
        )
        for year, count in by_year.items():
            print(f"  {year}: {count}")

        print()
        print("Top Kaohsiung districts:")
        for district, count in out["district"].value_counts().head(20).items():
            print(f"  {district}: {count}")

        sanhe = out[
            out["district"].eq("大樹區")
            & out["section"].eq("三和段")
        ]

        print()
        print(
            "Diagnostic 大樹區 / 三和段 rows : "
            f"{len(sanhe)}"
        )

    if out.empty:
        print()
        print("[ERROR] Extraction produced zero Kaohsiung parcel rows.")
        raise SystemExit(5)

    print()
    print(f"Output: {dest.resolve()}")


if __name__ == "__main__":
    main()
