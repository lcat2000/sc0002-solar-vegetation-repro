#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import math
import re
import time
import unicodedata
from pathlib import Path

import pandas as pd
import geopandas as gpd
import requests
import urllib3
from requests.exceptions import SSLError
from shapely.geometry import Point
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

MAP_URL = "https://maps.nlsc.gov.tw/T09/mapshow.action"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/136 Safari/537.36"
)
METRIC_CRS = "EPSG:3826"
WGS84 = "EPSG:4326"
KHH_BBOX = (120.10, 22.40, 121.20, 23.55)
BAD_V11D9_SEED = (120.31, 22.63)


def norm(s):
    if pd.isna(s):
        return ""
    s = unicodedata.normalize("NFKC", str(s).strip())
    s = s.replace("台", "臺")
    return re.sub(r"\s+", "", s)


def read_csv_flexible(path):
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    return pd.read_csv(path)


def plausible(lon, lat):
    # Reject fake/browser geolocation sentinels and the old V11D9 seed.
    if abs(lon) < 1e-9 and abs(lat) < 1e-9:
        return False
    if abs(lon - 120.31) < 1e-6 and abs(lat - 22.63) < 1e-6:
        return False

    a, b, c, d = KHH_BBOX
    return a <= lon <= c and b <= lat <= d


def mercator_to_lonlat(x, y):
    lon = x * 180.0 / 20037508.34
    lat = y * 180.0 / 20037508.34
    lat = 180.0 / math.pi * (
        2.0 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0
    )
    return lon, lat


def split_lot(lot):
    s = norm(lot).replace("地號", "").replace("之", "-").replace(".", "-")
    s = re.sub(r"[^0-9\-]", "", s)
    if not s:
        return "", ""
    if "-" in s:
        p = [x for x in s.split("-") if x]
        return p[0], p[1] if len(p) > 1 else ""
    return s, ""


def dismiss_popups(page):
    # Native JS dialogs are handled ONCE in main().
    # Do not register page.on("dialog") here; this function is called many times
    # and repeated handlers would all try to accept the same dialog.

    # Startup "提醒您" modal -> 確定
    for sel in [
        "button:has-text('確定')",
        "input[value='確定']",
        "text=確定",
        ".ui-dialog-buttonpane button",
    ]:
        try:
            loc = page.locator(sel)
            for i in range(min(loc.count(), 8)):
                el = loc.nth(i)
                if el.is_visible():
                    el.click(timeout=1200)
                    page.wait_for_timeout(400)
                    break
        except Exception:
            pass

    # Close survey / generic dialogs
    for sel in [
        ".ui-dialog-titlebar-close",
        "[title='關閉']",
        "[aria-label='Close']",
        "button.close",
        ".modal .close",
    ]:
        try:
            loc = page.locator(sel)
            for i in range(min(loc.count(), 12)):
                el = loc.nth(i)
                if el.is_visible():
                    el.click(timeout=800)
                    page.wait_for_timeout(200)
        except Exception:
            pass


def expose_land_form(page):
    """
    The form is often already present in DOM. If not visible, click 定位查詢 then 地號.
    """
    dismiss_popups(page)

    # Click top menu "定位查詢" if present.
    try:
        loc = page.get_by_text("定位查詢", exact=True)
        for i in range(min(loc.count(), 5)):
            el = loc.nth(i)
            if el.is_visible():
                el.click(timeout=1500)
                page.wait_for_timeout(700)
                break
    except Exception:
        pass

    # Click land-lot tab "地號".
    try:
        loc = page.get_by_text("地號", exact=True)
        for i in range(min(loc.count(), 10)):
            el = loc.nth(i)
            if el.is_visible():
                el.click(timeout=1500)
                page.wait_for_timeout(700)
                break
    except Exception:
        pass


def select_with_option_text(page, wanted_text, after_index=-1, allow_fuzzy=False):
    """
    Select by exact normalized option text. Cadastral section names must not use
    substring matching because parent/shorter section names can be different
    legal sections (e.g. 大人宮段一小段 != 大人宮段).
    """
    wanted = norm(wanted_text)

    def alias_set(s):
        vals = {s}
        vals.add(s.replace("臺", "台"))
        vals.add(s.replace("台", "臺"))
        vals.add(s.replace("塩", "鹽"))
        vals.add(s.replace("鹽", "塩"))
        return {norm(x) for x in vals if x}

    wanted_aliases = alias_set(wanted)

    data = page.eval_on_selector_all(
        "select",
        """sels => sels.map((s, idx) => ({
            idx,
            id: s.id || "",
            name: s.name || "",
            visible: !!(s.offsetWidth || s.offsetHeight || s.getClientRects().length),
            options: Array.from(s.options).map(o => ({text:o.text, value:o.value}))
        }))"""
    )

    for item in data:
        if item["idx"] <= after_index:
            continue
        for o in item["options"]:
            txt = norm(o["text"])
            if txt in wanted_aliases or wanted in alias_set(txt):
                sel = page.locator("select").nth(item["idx"])
                try:
                    sel.select_option(value=o["value"])
                except Exception:
                    try:
                        sel.select_option(label=o["text"])
                    except Exception:
                        continue
                page.wait_for_timeout(900)
                return item["idx"]

    if allow_fuzzy:
        for item in data:
            if item["idx"] <= after_index:
                continue
            for o in item["options"]:
                txt = norm(o["text"])
                if wanted and (wanted in txt or txt in wanted):
                    sel = page.locator("select").nth(item["idx"])
                    try:
                        sel.select_option(value=o["value"])
                    except Exception:
                        try:
                            sel.select_option(label=o["text"])
                        except Exception:
                            continue
                    page.wait_for_timeout(900)
                    return item["idx"]

    return None


def locate_land_form_container(page):
    """
    Find a compact ancestor containing 縣市 / 鄉鎮市區 / 地段 / 地號.
    """
    return page.evaluate_handle(
        """() => {
          const nodes = Array.from(document.querySelectorAll('div,section,td,form'));
          let best = null, bestLen = Infinity;
          for (const n of nodes) {
            const t = (n.innerText || '').replace(/\\s+/g,'');
            if (t.includes('縣市') && t.includes('鄉鎮市區') &&
                t.includes('地段') && t.includes('地號')) {
              if (t.length < bestLen) { best = n; bestLen = t.length; }
            }
          }
          return best;
        }"""
    )


def fill_land_lot_inputs(page, mother, child):
    """
    NLSC desktop land form has:
      地段: [代碼 input] [地段 dropdown]
      地號: [ONE input]  [定位 button]

    Older V11D7/8 logic could mistake the 地段代碼 input for a lot-number input.
    This version explicitly finds the input in the row/container containing "地號"
    and fills the combined lot string, e.g. 595 or 595-14.
    """
    combined = mother if not child else f"{mother}-{child}"

    result = page.evaluate(
        """(val) => {
          const all = Array.from(document.querySelectorAll('input'));
          const candidates = [];

          for (const inp of all) {
            const type = (inp.type || '').toLowerCase();
            if (!['text','number',''].includes(type)) continue;

            let node = inp;
            let depth = 0;
            let labelText = '';
            while (node && depth < 6) {
              const t = (node.innerText || node.textContent || '').replace(/\\s+/g,'');
              if (t.includes('地號')) {
                labelText = t;
                break;
              }
              node = node.parentElement;
              depth++;
            }

            if (!labelText.includes('地號')) continue;

            const meta = [
              inp.id || '',
              inp.name || '',
              inp.placeholder || '',
              inp.title || '',
              labelText
            ].join(' ').replace(/\\s+/g,'');

            let score = 0;
            if (meta.includes('地號')) score += 100;
            if (/land|parcel|lot|no/i.test(meta)) score += 20;
            if (meta.includes('地段')) score -= 60;
            if ((inp.offsetWidth || inp.offsetHeight || inp.getClientRects().length)) score += 10;

            candidates.push({inp, score, meta});
          }

          candidates.sort((a,b)=>b.score-a.score);
          if (!candidates.length) {
            return {ok:false, reason:'lot_input_not_found'};
          }

          const target = candidates[0].inp;
          target.focus();
          target.value = val;
          target.dispatchEvent(new Event('input',{bubbles:true}));
          target.dispatchEvent(new Event('change',{bubbles:true}));

          return {
            ok:true,
            reason:'land_number_row_input',
            id:target.id || '',
            name:target.name || '',
            value:target.value || '',
            meta:candidates[0].meta
          };
        }""",
        combined
    )

    if not result.get("ok"):
        return False, result.get("reason","lot_input_not_found")

    return True, (
        f"land_number_row_input:"
        f"id={result.get('id','')},"
        f"name={result.get('name','')},"
        f"value={result.get('value','')}"
    )


def click_land_locate(page):
    """
    V11D12 diagnostics proved that #div_cross_query is the ONLY real
    input[type=button] whose value is exactly "定位" on this NLSC land form.

    Earlier versions wrongly treated it as unrelated. V11D13 therefore clicks
    #div_cross_query directly using Playwright's real mouse/input event path
    (Locator.click), not DOM element.click().
    """
    btn = page.locator("#div_cross_query")

    if btn.count() == 0:
        return {"ok": False, "reason": "div_cross_query_not_found"}

    try:
        onclick = btn.get_attribute("onclick")
        value = btn.get_attribute("value")
        typ = btn.get_attribute("type")
        disabled = btn.is_disabled()
        visible = btn.is_visible()

        if not visible:
            return {
                "ok": False,
                "reason": "div_cross_query_not_visible",
                "onclick": onclick,
                "value": value,
                "type": typ,
            }

        # Real Playwright click so mouse/pointer/focus handlers also fire.
        btn.click(timeout=5000, force=True)
        page.wait_for_timeout(2000)

        return {
            "ok": True,
            "id": "div_cross_query",
            "tag": "INPUT",
            "type": typ,
            "value": value,
            "onclick": onclick,
            "disabled": disabled,
            "visible": visible,
            "click_method": "playwright_locator_click_force",
        }

    except Exception as e:
        return {
            "ok": False,
            "reason": f"div_cross_query_click_error:{type(e).__name__}:{e}",
        }


def extract_center(page):
    # OpenLayers-like global objects
    objs = page.evaluate(
        """() => {
          const out=[];
          for (const k of Object.keys(window).slice(0,8000)) {
            try {
              const o=window[k];
              if (!o || typeof o!=='object') continue;
              if (typeof o.getCenter==='function') {
                const c=o.getCenter();
                if (c && typeof c.lon==='number' && typeof c.lat==='number')
                  out.push([c.lon,c.lat,'getCenter_lonlat',k]);
                else if (Array.isArray(c) && c.length>=2)
                  out.push([c[0],c[1],'getCenter_array',k]);
              }
              if (typeof o.getView==='function') {
                const v=o.getView();
                if (v && typeof v.getCenter==='function') {
                  const c=v.getCenter();
                  if (Array.isArray(c) && c.length>=2)
                    out.push([c[0],c[1],'getView_getCenter',k]);
                }
              }
              if (o.map && typeof o.map.getView==='function') {
                const v=o.map.getView();
                const c=v && typeof v.getCenter==='function' ? v.getCenter() : null;
                if (Array.isArray(c) && c.length>=2)
                  out.push([c[0],c[1],'nested_map_view_center',k]);
              }
            } catch(e){}
          }
          return out;
        }"""
    )

    for x, y, method, key in objs:
        try:
            x, y = float(x), float(y)
        except Exception:
            continue
        if plausible(x, y):
            return x, y, f"js:{method}:{key}"
        if abs(x) > 180 and abs(y) > 90:
            lon, lat = mercator_to_lonlat(x, y)
            if plausible(lon, lat):
                return lon, lat, f"js3857:{method}:{key}"

    # Inputs that expose map center
    vals = page.eval_on_selector_all(
        "input",
        """els => els.map(e => ({
          id:e.id||'', name:e.name||'', value:e.value||''
        }))"""
    )
    nums = []
    for v in vals:
        try:
            nums.append((float(str(v["value"]).strip()), (v["id"]+" "+v["name"]).lower()))
        except Exception:
            pass

    lons = [(sum(w in m for w in ("lon","lng","center","x")), v) for v,m in nums if 119 <= v <= 123]
    lats = [(sum(w in m for w in ("lat","center","y")), v) for v,m in nums if 21 <= v <= 26]
    if lons and lats:
        lons.sort(reverse=True)
        lats.sort(reverse=True)
        lon, lat = lons[0][1], lats[0][1]
        if plausible(lon, lat):
            return lon, lat, "dom_input"

    return None, None, "center_not_found"


def wait_for_center_change(page, initial_center, timeout_ms=15000, dialog_start=0):
    """
    Wait for an actual map-center change, but return immediately when NLSC
    explicitly reports that the parcel has no data.
    """
    deadline = time.time() + timeout_ms / 1000.0
    last_good = None

    while time.time() < deadline:
        dismiss_popups(page)

        # Early classification: NLSC itself says the lot has no data.
        new_dialogs = _dialog_log[dialog_start:]
        for d in new_dialogs:
            msg = str(d.get("message", "")).strip()
            if "地號查詢無資料" in msg or "地號查無資料" in msg:
                return None, None, "nlsc_no_current_data"

        lon, lat, method = extract_center(page)
        if lon is not None:
            last_good = (lon, lat, method)
            if initial_center is None:
                return last_good

            ilon, ilat = initial_center
            if abs(lon - ilon) > 0.01 or abs(lat - ilat) > 0.01:
                page.wait_for_timeout(1200)
                lon2, lat2, method2 = extract_center(page)
                if lon2 is not None:
                    return lon2, lat2, method2 + ":moved"
                return last_good

        page.wait_for_timeout(600)

    return last_good if last_good else (None, None, "center_not_found_after_locate")


def locate_by_form(page, district, section, lot, debug_dir=None, record_id=""):
    page.goto(MAP_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1500)
    dismiss_popups(page)
    expose_land_form(page)

    initial_lon, initial_lat, _ = extract_center(page)
    initial_center = None if initial_lon is None else (initial_lon, initial_lat)

    county_idx = select_with_option_text(page, "高雄市", after_index=-1, allow_fuzzy=False)
    if county_idx is None:
        return {"located":False, "status":"technical_failure", "reason":"county_select_not_found"}

    town_idx = select_with_option_text(page, district, after_index=county_idx, allow_fuzzy=False)
    if town_idx is None:
        return {"located":False, "status":"technical_failure", "reason":"town_select_not_found"}

    section_idx = select_with_option_text(page, section, after_index=town_idx, allow_fuzzy=False)
    if section_idx is None:
        return {
            "located":False,
            "status":"technical_failure",
            "reason":"section_select_not_found_exact",
            "expected_section": section,
        }

    selected_section_text = page.evaluate(
        """(idx) => {
          const s = document.querySelectorAll('select')[idx];
          return (s && s.selectedIndex >= 0) ? s.options[s.selectedIndex].text : null;
        }""",
        section_idx
    )

    mother, child = split_lot(lot)
    ok, fill_method = fill_land_lot_inputs(page, mother, child)
    if not ok:
        return {"located":False, "status":"technical_failure", "reason":f"lot_fill_failed:{fill_method}"}

    landcode_value = page.evaluate(
        """() => {
          const e = document.querySelector('#landcode');
          return e ? e.value : null;
        }"""
    )

    form_state = page.evaluate(
        """() => {
          const sels = Array.from(document.querySelectorAll('select')).map((s,idx)=>({
            idx,
            id:s.id||'',
            name:s.name||'',
            value:s.value||'',
            text:s.options && s.selectedIndex >= 0 ? s.options[s.selectedIndex].text : ''
          }));
          const land = document.querySelector('#landcode');
          const btn = document.querySelector('#div_cross_query');
          return {
            selects:sels,
            landcode: land ? land.value : null,
            button:{
              id:btn ? btn.id : null,
              value:btn ? btn.value : null,
              onclick:btn ? btn.getAttribute('onclick') : null,
              disabled:btn ? !!btn.disabled : null
            }
          };
        }"""
    )

    dialog_start = len(_dialog_log)
    click_info = click_land_locate(page)
    if not click_info.get("ok"):
        return {
            "located": False,
            "status": "technical_failure",
            "reason": f"locate_click_failed:{click_info}"
        }

    lon, lat, method = wait_for_center_change(
        page, initial_center, timeout_ms=18000, dialog_start=dialog_start
    )

    located_ok = lon is not None and lat is not None and plausible(lon, lat)

    if located_ok:
        status = "located_current_parcel"
        reason = "ok"
    elif method == "nlsc_no_current_data":
        status = "nlsc_no_current_data"
        reason = "nlsc_no_current_data"
    else:
        status = "technical_failure"
        reason = method

    result = {
        "located": located_ok,
        "status": status,
        "reason": reason,
        "longitude": lon if located_ok else None,
        "latitude": lat if located_ok else None,
        "locate_method": method,
        "county_select_index": county_idx,
        "town_select_index": town_idx,
        "section_select_index": section_idx,
        "expected_section": section,
        "selected_section": selected_section_text,
        "lot_fill_method": fill_method,
        "landcode_value": landcode_value,
        "form_state": json.dumps(form_state, ensure_ascii=False),
        "click_info": json.dumps(click_info, ensure_ascii=False),
        "dialogs_after_click": json.dumps(_dialog_log[dialog_start:], ensure_ascii=False),
        "final_url": page.url,
    }

    if debug_dir and not result["located"]:
        try:
            shot = Path(debug_dir) / f"record_{record_id}.png"
            page.screenshot(path=str(shot), full_page=True)
            result["debug_screenshot"] = str(shot)
        except Exception:
            pass

    return result



_dialog_log = []

def safe_accept_dialog(dialog):
    """
    Record NLSC alert/confirm text, then accept once.
    """
    try:
        msg = dialog.message
        typ = dialog.type
        _dialog_log.append({"type": typ, "message": msg})
        print(f"           [DIALOG] type={typ} message={msg}")
    except Exception:
        pass

    try:
        dialog.accept()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# SC0002-specific main
# ---------------------------------------------------------------------------
from shapely.geometry import Point
from shapely.ops import unary_union
import numpy as np

KNOWN_SC0002_LON = 120.4144537
KNOWN_SC0002_LAT = 22.7140551

def build_proximity_clusters(gdf_metric, max_gap_m=300.0):
    """
    Transitive point clustering:
      two records are connected when their point distance <= max_gap_m.
    This reproduces the historical SC0002 cluster logic at case-study scale.
    """
    n = len(gdf_metric)
    if n == 0:
        return []

    geoms = list(gdf_metric.geometry)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    # n is small (~93 historically), O(n^2) is transparent and sufficient.
    for i in range(n):
        for j in range(i + 1, n):
            if geoms[i].distance(geoms[j]) <= max_gap_m:
                union(i, j)

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    return list(groups.values())

def main():
    ap = argparse.ArgumentParser(
        description="Locate SC0002 official parcels in NLSC and rebuild the heuristic envelope."
    )
    ap.add_argument("--parcels-csv", required=True)
    ap.add_argument("--outdir", default="sc0002_aoi_output")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--insecure-nlsc", action="store_true")
    ap.add_argument("--debug-screenshots", action="store_true")
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--limit", type=int, default=0,
                    help="Testing only. 0 = all parcels.")
    ap.add_argument("--max-gap-m", type=float, default=300.0)
    ap.add_argument("--buffer-m", type=float, default=50.0)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    debug_dir = outdir / "debug_screenshots"
    if args.debug_screenshots:
        debug_dir.mkdir(exist_ok=True)

    df = read_csv_flexible(args.parcels_csv)
    for c in ["sc_record_id","district","section","lot","site_name","operator",
              "capacity_kw","permit_year","solar_type","source_file"]:
        if c not in df.columns:
            df[c] = ""

    # Safety: this program is SC0002-only.
    df = df[
        df["district"].map(norm).eq("大樹區")
        & df["section"].map(norm).eq("三和段")
    ].copy()

    if df.empty:
        raise SystemExit("No 大樹區 / 三和段 parcel rows found.")

    if args.limit:
        df = df.head(args.limit).copy()

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not args.headed,
            args=["--ignore-certificate-errors"] if args.insecure_nlsc else []
        )
        context = browser.new_context(
            locale="zh-TW",
            user_agent=USER_AGENT,
            ignore_https_errors=args.insecure_nlsc,
            geolocation={"latitude":0.0, "longitude":0.0},
            permissions=["geolocation"],
            extra_http_headers={"Accept-Language":"zh-TW,zh;q=0.9"}
        )
        page = context.new_page()
        page.on("dialog", safe_accept_dialog)

        total = len(df)
        for i, (_, row) in enumerate(df.iterrows(), start=1):
            rid = str(row.get("sc_record_id", i))
            district = norm(row.get("district",""))
            section = norm(row.get("section",""))
            lot = norm(row.get("lot",""))

            print(f"[{i}/{total}] {rid}: {district} / {section} / {lot}")
            rec = row.to_dict()

            try:
                loc = locate_by_form(
                    page, district, section, lot,
                    debug_dir if args.debug_screenshots else None,
                    rid,
                )
            except PlaywrightTimeoutError:
                loc = {"located":False, "status":"technical_failure", "reason":"timeout"}
            except Exception as e:
                loc = {
                    "located":False,
                    "status":"technical_failure",
                    "reason":f"error:{type(e).__name__}:{e}"
                }

            rec.update(loc)
            results.append(rec)

            print(
                f"        -> located={rec.get('located')} "
                f"status={rec.get('status')} "
                f"lon={rec.get('longitude')} lat={rec.get('latitude')}"
            )

            pd.DataFrame(results).to_csv(
                outdir / "SC0002_NLSC_locator_cache.csv",
                index=False, encoding="utf-8-sig"
            )
            time.sleep(max(0.5, args.sleep))

        browser.close()

    result = pd.DataFrame(results)
    result.to_csv(
        outdir / "SC0002_Parcels_All.csv",
        index=False, encoding="utf-8-sig"
    )

    good = (
        result.get("located", False).astype(str).str.lower().isin(["true","1"])
        & pd.to_numeric(result.get("longitude"), errors="coerce").notna()
        & pd.to_numeric(result.get("latitude"), errors="coerce").notna()
    )

    located = result[good].copy()
    unresolved = result[~good].copy()
    unresolved.to_csv(
        outdir / "SC0002_Parcels_Unresolved.csv",
        index=False, encoding="utf-8-sig"
    )

    if located.empty:
        raise SystemExit("No SC0002 parcels could be located.")

    located["longitude"] = pd.to_numeric(located["longitude"])
    located["latitude"] = pd.to_numeric(located["latitude"])

    pts = gpd.GeoDataFrame(
        located,
        geometry=[Point(xy) for xy in zip(located["longitude"], located["latitude"])],
        crs=WGS84
    )
    pts.to_file(outdir / "SC0002_Parcel_Points.geojson", driver="GeoJSON")

    pts_m = pts.to_crs(METRIC_CRS).reset_index(drop=True)
    groups = build_proximity_clusters(pts_m, args.max_gap_m)

    # Pick the group nearest the historical government/NLSC-derived centroid.
    target = gpd.GeoSeries(
        [Point(KNOWN_SC0002_LON, KNOWN_SC0002_LAT)],
        crs=WGS84
    ).to_crs(METRIC_CRS).iloc[0]

    ranked = []
    for gid, idxs in enumerate(groups, start=1):
        gg = pts_m.iloc[idxs]
        center = unary_union(list(gg.geometry)).centroid
        ranked.append((center.distance(target), gid, idxs, center))

    ranked.sort(key=lambda x: x[0])
    _, chosen_gid, chosen_idxs, chosen_center = ranked[0]
    chosen = pts_m.iloc[chosen_idxs].copy()

    # Historical envelope rule:
    # 1 point => 50m buffer
    # >=2 points => convex hull + 50m buffer
    union_pts = unary_union(list(chosen.geometry))
    if len(chosen) == 1:
        envelope = union_pts.buffer(args.buffer_m)
        method = f"single_point_buffer_{args.buffer_m:g}m"
    else:
        envelope = union_pts.convex_hull.buffer(args.buffer_m)
        method = f"convex_hull_plus_{args.buffer_m:g}m"

    envelope_gdf = gpd.GeoDataFrame(
        [{
            "case_id":"SC0002",
            "district":"大樹區",
            "section":"三和段",
            "located_points":len(chosen),
            "all_located_points":len(pts_m),
            "cluster_count":len(groups),
            "max_gap_m":args.max_gap_m,
            "buffer_m":args.buffer_m,
            "method":method,
            "area_ha":envelope.area/10000.0,
        }],
        geometry=[envelope],
        crs=METRIC_CRS
    )

    # Save both metric and WGS84 forms.
    envelope_gdf.to_file(
        outdir / "SC0002_Envelope_EPSG3826.gpkg",
        layer="SC0002_Envelope",
        driver="GPKG"
    )
    env_wgs = envelope_gdf.to_crs(WGS84)
    env_wgs.to_file(outdir / "SC0002_Envelope.geojson", driver="GeoJSON")
    env_wgs.to_file(outdir / "SC0002_Envelope.shp", driver="ESRI Shapefile", encoding="utf-8")

    chosen_wgs = chosen.to_crs(WGS84)
    chosen_wgs.to_file(outdir / "SC0002_Chosen_Parcel_Points.geojson", driver="GeoJSON")

    c_wgs = gpd.GeoSeries([chosen_center], crs=METRIC_CRS).to_crs(WGS84).iloc[0]

    summary = pd.DataFrame([{
        "case_id":"SC0002",
        "official_input_rows":len(df),
        "located_rows":len(located),
        "unresolved_rows":len(unresolved),
        "proximity_clusters_found":len(groups),
        "chosen_cluster_id":chosen_gid,
        "chosen_cluster_points":len(chosen),
        "max_gap_m":args.max_gap_m,
        "buffer_m":args.buffer_m,
        "envelope_area_ha":envelope.area/10000.0,
        "centroid_lon":c_wgs.x,
        "centroid_lat":c_wgs.y,
        "historical_reference_area_ha":63.304526,
        "historical_reference_centroid_lon":KNOWN_SC0002_LON,
        "historical_reference_centroid_lat":KNOWN_SC0002_LAT,
        "area_difference_ha":envelope.area/10000.0 - 63.304526,
    }])
    summary.to_csv(
        outdir / "SC0002_Envelope_Summary.csv",
        index=False, encoding="utf-8-sig"
    )

    print()
    print("="*72)
    print("SC0002 AOI rebuild complete")
    print(f"Official input rows       : {len(df)}")
    print(f"Located rows              : {len(located)}")
    print(f"Unresolved rows           : {len(unresolved)}")
    print(f"Proximity clusters        : {len(groups)}")
    print(f"Chosen cluster points     : {len(chosen)}")
    print(f"Envelope area             : {envelope.area/10000.0:.6f} ha")
    print(f"Centroid                  : {c_wgs.x:.9f}, {c_wgs.y:.9f}")
    print(f"Historical reference area : 63.304526 ha")
    print(f"Area difference           : {envelope.area/10000.0 - 63.304526:+.6f} ha")
    print()
    print("Earth Engine upload files:")
    print(f"  {outdir / 'SC0002_Envelope.shp'}")
    print(f"  {outdir / 'SC0002_Envelope.shx'}")
    print(f"  {outdir / 'SC0002_Envelope.dbf'}")
    print(f"  {outdir / 'SC0002_Envelope.prj'}")
    print()
    print("Then upload as:")
    print("  Public GEE scripts in this repository embed the archived AOI directly; no asset upload is required.")

if __name__ == "__main__":
    main()
