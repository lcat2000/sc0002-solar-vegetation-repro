#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Screen Top20 control candidates against Energy Administration official solar
parcel records after the parcel IDs have been located with NLSC.

Default mode is POINT-BASED:
- a located official parcel representative point inside a candidate => HIT
- a located point just outside the candidate boundary => REVIEW_NEAR_BOUNDARY
- otherwise => NO_POINT_HIT if locator coverage is complete enough

This is NOT exact parcel-polygon overlap.

Optional exact mode:
  --parcel-polygons <file>
If the user has an authorized/exported cadastral polygon layer containing the
official solar parcels, the script will perform true polygon intersection.

The program never uses 2023-2026 NDVI/NDMI outcomes.
"""

import argparse
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

METRIC_CRS = "EPSG:32651"

def read_csv_flexible(path):
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    return pd.read_csv(path)

def boolish(v):
    return str(v).strip().lower() in {"true", "1", "yes", "y"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates",
                    default="data/SC0002_STEP3B2_Top20_Control_Candidates_WGS84.geojson")
    ap.add_argument("--official-parcels-csv", required=True,
                    help="Output from 01_extract_kaohsiung_official_solar.py")
    ap.add_argument("--located-csv", required=True,
                    help="Kaohsiung_Official_Solar_NLSC_All.csv")
    ap.add_argument("--outdir", default="official_overlap_screen")
    ap.add_argument("--near-boundary-m", type=float, default=100.0)
    ap.add_argument("--minimum-coverage", type=float, default=0.99)
    ap.add_argument("--parcel-polygons",
                    help="Optional exact official-solar parcel polygon layer.")
    ap.add_argument("--polygon-id-field", default="record_key",
                    help="ID field used only in optional exact polygon mode.")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    candidates = gpd.read_file(args.candidates)
    if candidates.crs is None:
        candidates = candidates.set_crs("EPSG:4326")

    if "candidate_id" not in candidates.columns:
        raise SystemExit("Candidate GeoJSON has no candidate_id field.")

    candidates_m = candidates.to_crs(METRIC_CRS)

    official = read_csv_flexible(args.official_parcels_csv)
    located = read_csv_flexible(args.located_csv)

    total_official = len(official)

    if "record_key" in official.columns and "record_key" in located.columns:
        # Keep only rows belonging to the official archive being screened.
        located = located[
            located["record_key"].astype(str).isin(
                set(official["record_key"].astype(str))
            )
        ].copy()

    for c in ["located", "longitude", "latitude"]:
        if c not in located.columns:
            located[c] = None

    good = (
        located["located"].map(boolish)
        & pd.to_numeric(located["longitude"], errors="coerce").notna()
        & pd.to_numeric(located["latitude"], errors="coerce").notna()
    )

    pts_df = located[good].copy()
    pts_df["longitude"] = pd.to_numeric(pts_df["longitude"])
    pts_df["latitude"] = pd.to_numeric(pts_df["latitude"])

    pts = gpd.GeoDataFrame(
        pts_df,
        geometry=[
            Point(xy)
            for xy in zip(pts_df["longitude"], pts_df["latitude"])
        ],
        crs="EPSG:4326",
    ).to_crs(METRIC_CRS)

    located_count = len(pts)
    coverage = (located_count / total_official) if total_official else 0.0

    summaries = []
    details = []

    exact_layer = None
    if args.parcel_polygons:
        exact_layer = gpd.read_file(args.parcel_polygons)
        if exact_layer.crs is None:
            raise SystemExit("Exact parcel polygon layer has no CRS.")
        exact_layer = exact_layer.to_crs(METRIC_CRS)

    for _, cand in candidates_m.iterrows():
        cid = cand["candidate_id"]
        geom = cand.geometry

        inside = pts[pts.geometry.intersects(geom)].copy()

        # Points outside but close to the square may represent parcels that cross
        # the control boundary. Flag for manual review instead of silently NO.
        if len(pts):
            dist = pts.geometry.distance(geom)
            near = pts[
                (dist > 0)
                & (dist <= args.near_boundary_m)
            ].copy()
        else:
            near = pts.iloc[0:0].copy()

        exact_count = None
        if exact_layer is not None:
            exact_hits = exact_layer[
                exact_layer.geometry.intersects(geom)
            ]
            exact_count = len(exact_hits)

        if exact_layer is not None:
            status = "EXACT_YES" if exact_count else "EXACT_NO"
        elif len(inside) > 0:
            status = "POINT_HIT_YES"
        elif len(near) > 0:
            status = "REVIEW_NEAR_BOUNDARY"
        elif coverage >= args.minimum_coverage:
            status = "NO_POINT_HIT"
        else:
            status = "UNKNOWN_INCOMPLETE_LOCATOR_COVERAGE"

        summaries.append({
            "candidate_id": cid,
            "official_archive_rows": total_official,
            "located_official_points": located_count,
            "locator_coverage_fraction": coverage,
            "point_hits_inside": len(inside),
            "point_hits_within_boundary_buffer": len(near),
            "near_boundary_m": args.near_boundary_m,
            "exact_polygon_hits":
                exact_count if exact_count is not None else "",
            "government_solar_screen_status": status,
            "interpretation":
                (
                    "exact cadastral polygon intersection"
                    if exact_layer is not None
                    else "representative official-parcel point screen; not exact parcel overlap"
                ),
        })

        for relation, subset in [
            ("INSIDE", inside),
            ("NEAR_BOUNDARY", near),
        ]:
            for _, hit in subset.iterrows():
                details.append({
                    "candidate_id": cid,
                    "relation": relation,
                    "distance_to_candidate_m":
                        0.0 if relation == "INSIDE"
                        else float(hit.geometry.distance(geom)),
                    "official_record_id": hit.get("official_record_id", ""),
                    "record_key": hit.get("record_key", ""),
                    "permit_year": hit.get("permit_year", ""),
                    "district": hit.get("district", ""),
                    "section": hit.get("section", ""),
                    "lot": hit.get("lot", ""),
                    "site_name": hit.get("site_name", ""),
                    "operator": hit.get("operator", ""),
                    "longitude": hit.get("longitude", ""),
                    "latitude": hit.get("latitude", ""),
                })

    summary_df = pd.DataFrame(summaries)
    detail_df = pd.DataFrame(details)

    summary_path = outdir / "SC0002_STEP3B2_Government_Solar_Screen.csv"
    detail_path = outdir / "SC0002_STEP3B2_Government_Solar_Hits_Detail.csv"

    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    detail_df.to_csv(detail_path, index=False, encoding="utf-8-sig")

    print(summary_df.to_string(index=False))
    print()
    print(f"Wrote: {summary_path.resolve()}")
    print(f"Wrote: {detail_path.resolve()}")
    print()
    print("Interpretation:")
    print("  EXACT_YES / EXACT_NO              = polygon mode only")
    print("  POINT_HIT_YES                     = confirmed official parcel point inside")
    print("  REVIEW_NEAR_BOUNDARY              = manual review required")
    print("  NO_POINT_HIT                      = no located point hit; not exact geometry proof")
    print("  UNKNOWN_INCOMPLETE_LOCATOR_COVERAGE = locate more official records first")

if __name__ == "__main__":
    main()
