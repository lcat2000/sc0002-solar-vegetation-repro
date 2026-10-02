#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
download_moeaea_solar_land_v2.py

修正版：
能源署 metadata 的 FileName 欄位不是實際檔名，而是像：
  108年度取得施工太陽光電土地地號開啟
  109年度取得施工太陽光電土地地號開啟

因此不能靠 ".ods" 副檔名判斷。
本版改為：
1) 只要 metadata 年度為 108~113 且有 FileUrl 就下載。
2) 下載後檢查內容是否為 ODS/ZIP。
3) 優先從 Content-Disposition 取得實際檔名；
   若沒有，則自動命名為「108年度取得施工太陽光電土地地號.ods」。
"""

import argparse
import csv
import io
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

MOEAEA_PAGE = (
    "https://www.moeaea.gov.tw/ECW/populace/opendata/"
    "Opendata.aspx?info_kind=03&menu_id=8800&sub_kind=0304"
)
METADATA_CSV_URL = (
    "https://www.moeaea.gov.tw/ECW/populace/opendata/"
    "wHandOpenData_File.ashx?set_id=344"
)

DEFAULT_YEARS = {"108", "109", "110", "111", "112", "113"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/136 Safari/537.36"
    ),
    "Accept": "*/*",
    "Referer": MOEAEA_PAGE,
}

def fetch_bytes(url, timeout=120):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=timeout) as r:
        data = r.read()
        headers = dict(r.headers.items())
        final_url = r.geturl()
    return data, headers, final_url

def decode_text(data):
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5"):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace"), "utf-8(replace)"

def normalize_header(s):
    return re.sub(r"[\s\(\)（）_\-]+", "", (s or "")).lower()

def find_field(fieldnames, candidates):
    norm = {normalize_header(x): x for x in fieldnames if x}
    for c in candidates:
        nc = normalize_header(c)
        if nc in norm:
            return norm[nc]
    for x in fieldnames:
        if not x:
            continue
        nx = normalize_header(x)
        for c in candidates:
            nc = normalize_header(c)
            if nc in nx or nx in nc:
                return x
    return None

def parse_metadata_csv(text):
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        raise RuntimeError("metadata CSV 沒有欄位名稱。")

    fieldnames = [x.strip() if x else x for x in reader.fieldnames]

    year_col = find_field(fieldnames, ["民國年", "年度", "year"])
    name_col = find_field(fieldnames, ["FileName", "檔案名稱", "filename"])
    url_col  = find_field(fieldnames, ["FileUrl", "檔案連結", "fileurl", "url"])

    if not name_col or not url_col:
        raise RuntimeError(
            "無法辨識 FileName / FileUrl 欄位。\n"
            f"實際欄位：{fieldnames}"
        )

    rows = []
    for raw in reader:
        row = {}
        for k, v in raw.items():
            kk = k.strip() if isinstance(k, str) else k
            row[kk] = v.strip() if isinstance(v, str) else v

        filename_label = (row.get(name_col) or "").strip()
        fileurl = (row.get(url_col) or "").strip()
        year = (row.get(year_col) or "").strip() if year_col else ""

        if not year:
            m = re.search(r"(?<!\d)(10[8-9]|11[0-3])年度?", filename_label)
            if m:
                year = m.group(1)

        rows.append({
            "year": year,
            "label": filename_label,
            "url": fileurl,
        })
    return rows, fieldnames

def is_wanted(row, years):
    return row["year"] in years and bool(row["url"])

def safe_filename(name):
    name = re.sub(r'[<>:"/\\|?*]+', "_", (name or "").strip())
    return name.rstrip(". ")

def filename_from_content_disposition(headers):
    cd = headers.get("Content-Disposition") or headers.get("content-disposition")
    if not cd:
        return None

    # RFC 5987 filename*=UTF-8''...
    m = re.search(r"filename\*=UTF-8''([^;]+)", cd, re.I)
    if m:
        from urllib.parse import unquote
        return safe_filename(unquote(m.group(1)))

    m = re.search(r'filename="?([^";]+)"?', cd, re.I)
    if m:
        return safe_filename(m.group(1))
    return None

def content_looks_html(data):
    head = data[:500].lstrip().lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html") or b"<html" in head

def default_ods_name(year):
    return f"{year}年度取得施工太陽光電土地地號.ods"

def download_one(year, url, outdir, overwrite=False, retries=3):
    last_err = None

    for attempt in range(1, retries + 1):
        try:
            data, headers, final_url = fetch_bytes(url)

            if content_looks_html(data):
                raise RuntimeError("伺服器回傳 HTML，不是資料檔。")

            if len(data) < 500:
                raise RuntimeError(f"檔案太小（{len(data)} bytes），疑似不是有效檔案。")

            # ODS is a ZIP-based container, so normally starts with PK.
            # Some servers may also return CSV; we detect that below.
            cd_name = filename_from_content_disposition(headers)

            ctype = (
                headers.get("Content-Type")
                or headers.get("content-type")
                or ""
            ).lower()

            if data.startswith(b"PK"):
                filename = cd_name or default_ods_name(year)
                if not filename.lower().endswith(".ods"):
                    filename = re.sub(r"\.[A-Za-z0-9]+$", "", filename) + ".ods"
            else:
                # If it is text/csv, preserve as CSV instead of pretending it is ODS.
                text_like = (
                    "csv" in ctype
                    or "text" in ctype
                    or b"," in data[:300]
                )
                if text_like:
                    filename = cd_name or f"{year}年度取得施工太陽光電土地地號.csv"
                    if not filename.lower().endswith(".csv"):
                        filename = re.sub(r"\.[A-Za-z0-9]+$", "", filename) + ".csv"
                else:
                    raise RuntimeError(
                        f"下載內容不是 ODS/ZIP，也不像 CSV。Content-Type={ctype}"
                    )

            dest = outdir / safe_filename(filename)

            if dest.exists() and not overwrite:
                print(f"[SKIP] 已存在：{dest.name}")
                return True

            dest.write_bytes(data)
            print(
                f"[OK]   {dest.name} "
                f"({len(data)/1024/1024:.2f} MB, "
                f"Content-Type={ctype or 'unknown'})"
            )
            return True

        except (HTTPError, URLError, TimeoutError, RuntimeError, OSError) as e:
            last_err = e
            print(f"[WARN] {year} 年，第 {attempt}/{retries} 次下載失敗：{e}")
            if attempt < retries:
                time.sleep(2 * attempt)

    print(f"[FAIL] {year} 年：{last_err}")
    return False

def main():
    ap = argparse.ArgumentParser(
        description="下載能源署 108～113 年太陽光電案場土地地號資料"
    )
    ap.add_argument("--outdir", default="solar_data")
    ap.add_argument(
        "--years",
        nargs="*",
        default=sorted(DEFAULT_YEARS)
    )
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    years = {str(y).strip() for y in args.years}
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("能源署太陽光電案場土地地號下載器 V2")
    print("=" * 60)
    print(f"輸出目錄：{outdir.resolve()}")
    print(f"年度：{', '.join(sorted(years))}")
    print()

    print("[1/3] 下載官方 metadata CSV ...")
    meta_bytes, headers, final_url = fetch_bytes(METADATA_CSV_URL, timeout=60)
    meta_path = outdir / "_moeaea_solar_land_metadata.csv"
    meta_path.write_bytes(meta_bytes)

    text, enc = decode_text(meta_bytes)
    print(f"[OK] metadata：{len(meta_bytes)} bytes，解析編碼：{enc}")

    print("[2/3] 解析年度下載連結 ...")
    rows, fields = parse_metadata_csv(text)
    wanted = [r for r in rows if is_wanted(r, years)]

    if not wanted:
        print("[ERROR] 沒找到指定年度下載連結。")
        for r in rows:
            print(
                f"  year={r['year']!r} "
                f"label={r['label']!r} "
                f"url={r['url']!r}"
            )
        sys.exit(4)

    print(f"[OK] 找到 {len(wanted)} 個年度連結：")
    for r in wanted:
        print(f"  {r['year']}  {r['label']}")

    print()
    print("[3/3] 開始下載 ...")

    ok = fail = 0
    for row in sorted(wanted, key=lambda x: x["year"]):
        url = urljoin(MOEAEA_PAGE, row["url"])
        print()
        print(f"年度：{row['year']}")
        print(f"URL ：{url}")

        if download_one(
            row["year"],
            url,
            outdir,
            overwrite=args.overwrite
        ):
            ok += 1
        else:
            fail += 1

    print()
    print("=" * 60)
    print(f"完成：成功 {ok}，失敗 {fail}")
    print(f"資料夾：{outdir.resolve()}")

    print()
    print("目前資料檔：")
    for p in sorted(outdir.glob("*")):
        if p.suffix.lower() in {".ods", ".csv", ".xlsx", ".xls"} and not p.name.startswith("_"):
            print(f"  {p.name}")

    if fail:
        sys.exit(1)

if __name__ == "__main__":
    main()
