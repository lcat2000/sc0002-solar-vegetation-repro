#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import argparse
import math
import json
import re
import geopandas as gpd
from pyproj import Geod

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_SOURCE_PLANAR_PROP_HA = 63.304526019347165
EXPECTED_ROUNDTRIP_PLANAR_HA = 63.292023
EXPECTED_LOCAL_WGS84_GEODESIC_HA = 63.299028
EXPECTED_LOCATED = 93
EXPECTED_ALL_LOCATED = 106


def main():
    ap = argparse.ArgumentParser(description="Verify the exact SC0002 AOI archived from the V4 GEE run.")
    ap.add_argument("--aoi", type=Path, default=ROOT / "data/aoi/SC0002_Envelope_USED_BY_GEE_V4.geojson")
    ap.add_argument("--area-tol-ha", type=float, default=0.02)
    args = ap.parse_args()

    p = args.aoi
    gdf = gpd.read_file(p)
    failures = []

    if len(gdf) != 1:
        failures.append(f"feature count={len(gdf)}")
    if gdf.crs is None:
        failures.append("missing CRS")
    elif gdf.crs.to_epsg() != 4326:
        failures.append(f"expected EPSG:4326 GeoJSON, got {gdf.crs}")

    planar_roundtrip_ha = float(gdf.to_crs("EPSG:3826").geometry.area.iloc[0] / 10000.0)
    geom = gdf.to_crs("EPSG:4326").geometry.iloc[0]
    geod = Geod(ellps="WGS84")
    local_geodesic_ha = abs(geod.geometry_area_perimeter(geom)[0]) / 10000.0

    prop_planar = float(gdf.iloc[0].get("area_ha", float("nan")))
    located = int(gdf.iloc[0].get("located_points", gdf.iloc[0].get("located_po", -1)))
    all_located = int(gdf.iloc[0].get("all_located_points", gdf.iloc[0].get("all_locate", -1)))

    print(f"source builder area_ha property : {prop_planar:.6f} ha")
    print(f"GeoJSON→EPSG:3826 round-trip    : {planar_roundtrip_ha:.6f} ha")
    print(f"local WGS84 ellipsoidal area    : {local_geodesic_ha:.6f} ha")
    print(f"chosen located points           : {located}")
    print(f"all located records             : {all_located}")
    print("Earth Engine AOI.area(1)        : 63.456375 ha (verified in archived GEE summary)")

    if math.isnan(prop_planar) or abs(prop_planar - EXPECTED_SOURCE_PLANAR_PROP_HA) > 1e-6:
        failures.append("source area_ha property")
    if abs(planar_roundtrip_ha - EXPECTED_ROUNDTRIP_PLANAR_HA) > args.area_tol_ha:
        failures.append("round-trip EPSG:3826 area")
    if abs(local_geodesic_ha - EXPECTED_LOCAL_WGS84_GEODESIC_HA) > args.area_tol_ha:
        failures.append("local WGS84 geodesic area")
    if located != EXPECTED_LOCATED:
        failures.append("located point count")
    if all_located != EXPECTED_ALL_LOCATED:
        failures.append("all-located count")

    archive_obj = json.loads(p.read_text(encoding="utf-8"))
    archive_coords = archive_obj["features"][0]["geometry"]["coordinates"]
    gee_scripts = sorted((ROOT / "src/gee").glob("*.js"))
    if len(gee_scripts) != 7:
        failures.append(f"expected 7 GEE scripts, found {len(gee_scripts)}")
    else:
        for js in gee_scripts:
            text = js.read_text(encoding="utf-8")
            m = re.search(r"var\s+SC0002_AOI_COORDINATES\s*=\s*(\[\[\[.*?\]\]\])\s*;", text, re.S)
            if not m:
                failures.append(f"{js.name}: embedded AOI array not found")
                continue
            if json.loads(m.group(1)) != archive_coords:
                failures.append(f"{js.name}: embedded AOI differs from archived GeoJSON")

    if failures:
        print("\nFAIL")
        for item in failures:
            print(" -", item)
        raise SystemExit(1)

    print("\nPASS — archived AOI geometry/properties match the validated SC0002 V4 envelope, and all seven GEE scripts embed the exact archived coordinate array.")
    print("Note: Earth Engine AOI.area(1) uses EE's spherical geometry model and is")
    print("therefore not expected to equal pyproj's WGS84 ellipsoidal area exactly.")


if __name__ == "__main__":
    main()
