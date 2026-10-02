#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import argparse
import csv
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]

MAIN_TIF = "SC0002_Spectral_Vegetation_Loss_2022_2026_UTM51N_V4.tif"
SENS_TIF = "SC0002_Threshold_Sensitivity_Masks_UTM51N_V4.tif"
SUMMARY_CSV = "SC0002_Spectral_Change_Summary_UTM51N_V4.csv"
SENS_CSV = "SC0002_Threshold_Sensitivity_UTM51N_V4.csv"


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def verify_grid(ds, failures, label):
    if str(ds.crs) != "EPSG:32651":
        failures.append(f"{label}: CRS {ds.crs}")
    if abs(ds.transform.a - 10.0) > 1e-9 or abs(ds.transform.e + 10.0) > 1e-9:
        failures.append(f"{label}: pixel size {ds.transform.a}, {ds.transform.e}")
    if ds.nodata != 255:
        failures.append(f"{label}: NoData {ds.nodata}")


def counts(arr):
    u, c = np.unique(arr, return_counts=True)
    return {int(k): int(v) for k, v in zip(u, c)}


def main():
    ap = argparse.ArgumentParser(description="Verify SC0002 V4 GeoTIFF grid, NoData, and loss-pixel counts.")
    ap.add_argument("--rasters-dir", type=Path, default=ROOT / "data/reference/step2")
    ap.add_argument("--results-dir", type=Path, default=ROOT / "data/reference/step2")
    args = ap.parse_args()

    rd = args.rasters_dir
    results = args.results_dir
    failures = []

    summary = {r["metric"]: r for r in read_csv(results / SUMMARY_CSV)}
    expected_main = int(float(summary["2022_to_2026_export_raster_loss_pixel_count"]["value"]))

    with rasterio.open(rd / MAIN_TIF) as ds:
        verify_grid(ds, failures, "main")
        if ds.count != 1:
            failures.append(f"main: band count {ds.count}")
        c = counts(ds.read(1))
        print("Main TIFF counts:", c)
        if c.get(1, 0) != expected_main:
            failures.append(f"main loss pixels: TIFF={c.get(1,0)} CSV={expected_main}")
        if c.get(255, 0) == 0:
            failures.append("main: no explicit 255 NoData cells")
        if any(v not in (0, 1, 255) for v in c):
            failures.append(f"main: unexpected raster values {sorted(c)}")

    sens_rows = read_csv(results / SENS_CSV)
    expected = {r["threshold_name"]: int(float(r["export_raster_loss_pixel_count"])) for r in sens_rows}
    order = ["Loose", "Standard", "Strict"]

    with rasterio.open(rd / SENS_TIF) as ds:
        verify_grid(ds, failures, "sensitivity")
        if ds.count != 3:
            failures.append(f"sensitivity: band count {ds.count}")
        got_counts = []
        for band, name in enumerate(order, start=1):
            c = counts(ds.read(band))
            got = c.get(1, 0)
            got_counts.append(got)
            print(f"{name:8s} TIFF counts: {c}")
            if got != expected[name]:
                failures.append(f"{name}: TIFF loss pixels={got} CSV={expected[name]}")
            if c.get(255, 0) == 0:
                failures.append(f"{name}: no explicit 255 NoData cells")
            if any(v not in (0, 1, 255) for v in c):
                failures.append(f"{name}: unexpected raster values {sorted(c)}")
        if not (got_counts[0] >= got_counts[1] >= got_counts[2]):
            failures.append("raster nesting Loose >= Standard >= Strict")

    if failures:
        print("\nFAIL")
        for item in failures:
            print(" -", item)
        raise SystemExit(1)

    print("\nPASS — raster CRS, 10 m grid, 255 NoData, and loss-pixel counts match the curated CSVs.")
    print("Note: formal hectare estimates use ee.Image.pixelArea() inside the AOI;")
    print("raster pixel_count * 0.01 ha is a full-cell QA quantity, not the formal area estimator.")


if __name__ == "__main__":
    main()
