#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import argparse
import csv
import math

ROOT = Path(__file__).resolve().parents[2]

EXPECTED = {
    "summary": {
        "AOI_builder_planar_area_ha": 63.304526019347165,
        "AOI_geodesic_area_ha": 63.45637540492422,
        "2022_baseline_spectral_vegetation_ha": 58.23981001641681,
        "2022_to_2026_spectral_vegetation_loss_ha": 16.795013412664105,
        "loss_fraction_of_2022_baseline": 0.2883768578216494,
        "2022_to_2026_export_raster_loss_pixel_count": 1694.0,
        "2022_to_2026_export_raster_nominal_loss_area_ha": 16.94,
    },
    "annual": {
        2018: (3, 0.7036171912901886, 0.157948716081458, 1.5440068137026737),
        2019: (60, 0.723266991953337, 0.21628620387086167, 18.536291880007525),
        2020: (62, 0.7584049105184163, 0.24017462755785854, 31.455280124389674),
        2021: (62, 0.6655906264746853, 0.132684243013407, 29.834029270200965),
        2022: (62, 0.7519092577502317, 0.23191520104410154, 19.459544259356456),
        2023: (62, 0.6054368677908601, 0.11935351150673347, 22.722143543323458),
        2024: (60, 0.6776800930874399, 0.15804514331877736, 25.056479207312844),
        2025: (70, 0.5574247006917463, 0.05341328601310135, 24.534315485327753),
        2026: (74, 0.6028311458018436, 0.059403678370284374, 31.25728288750461),
    },
    "time_series": {
        2023: (14.947460851643925, 0.25665366778206333),
        2024: (11.043817638214739, 0.18962660824445812),
        2025: (21.545707303688257, 0.3699481041853483),
        2026: (16.795013412664105, 0.2883768578216494),
    },
    "sensitivity": {
        "Loose": (19.529413533564586, 0.3353275625050902, 1975.0, 19.75),
        "Standard": (16.795013412664105, 0.2883768578216494, 1694.0, 16.94),
        "Strict": (14.498827960917176, 0.24895046801887236, 1461.0, 14.61),
    },
}

EXPECTED_RULES = {
    "2022_baseline_spectral_vegetation_ha": "NDVI_P70>=0.55 AND NDMI_P70>=0.10",
    "2022_to_2026_spectral_vegetation_loss_ha": (
        "baseline vegetation AND NDVI_2022-NDVI_2026>=0.20 "
        "AND NDMI_2022-NDMI_2026>=0.10"
    ),
}

FILES = {
    "annual": "SC0002_Annual_NDVI_NDMI_2018_2026_UTM51N_V4.csv",
    "summary": "SC0002_Spectral_Change_Summary_UTM51N_V4.csv",
    "time": "SC0002_Loss_TimeSeries_2022_2026_UTM51N_V4.csv",
    "sens": "SC0002_Threshold_Sensitivity_UTM51N_V4.csv",
}


def rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def close(got, expected, tol):
    return math.isclose(float(got), float(expected), rel_tol=0.0, abs_tol=tol)


def fail_or_print(failures, label, got, expected, tol):
    ok = close(got, expected, tol)
    print(f"{label:38s} got={float(got):.9f} expected={float(expected):.9f} {'PASS' if ok else 'FAIL'}")
    if not ok:
        failures.append(label)


def main():
    ap = argparse.ArgumentParser(description="Verify curated SC0002 V4 result CSVs.")
    ap.add_argument("--results-dir", type=Path, default=ROOT / "data/reference/step2")
    ap.add_argument("--area-tol-ha", type=float, default=1e-5)
    ap.add_argument("--fraction-tol", type=float, default=1e-7)
    ap.add_argument("--index-tol", type=float, default=1e-7)
    args = ap.parse_args()

    d = args.results_dir
    annual = rows(d / FILES["annual"])
    summary = rows(d / FILES["summary"])
    ts = rows(d / FILES["time"])
    sens = rows(d / FILES["sens"])
    failures = []

    # Grid metadata must be explicit and stable.
    for label, dataset in [("annual", annual), ("summary", summary), ("time_series", ts), ("sensitivity", sens)]:
        for r in dataset:
            if r.get("analysis_crs") != "EPSG:32651":
                failures.append(f"{label}: analysis_crs")
                break
            if float(r.get("analysis_scale_m", "nan")) != 10.0:
                failures.append(f"{label}: analysis_scale_m")
                break
            if r.get("grid_transform") != "10,0,0,0,-10,0":
                failures.append(f"{label}: grid_transform")
                break

    print("Summary:")
    sm = {r["metric"]: r for r in summary}
    if "2022_to_2026_export_raster_valid_pixel_count" in sm:
        failures.append("deprecated valid-pixel QA metric still present in curated summary")
    for metric, expected in EXPECTED["summary"].items():
        if metric not in sm:
            failures.append(f"missing summary metric: {metric}")
            continue
        tol = args.fraction_tol if "fraction" in metric else args.area_tol_ha
        if "pixel_count" in metric:
            tol = 0.0
        fail_or_print(failures, metric, sm[metric]["value"], expected, tol)

    for metric, expected_rule in EXPECTED_RULES.items():
        got = sm.get(metric, {}).get("rule", "")
        if got != expected_rule:
            failures.append(f"rule mismatch: {metric}")

    print("\nAnnual means:")
    by_year = {int(r["year"]): r for r in annual}
    if sorted(by_year) != list(range(2018, 2027)):
        failures.append("annual year coverage")
    for year, (scene_count, ndvi, ndmi, valid_obs) in EXPECTED["annual"].items():
        r = by_year.get(year)
        if r is None:
            continue
        if int(float(r["scene_count"])) != scene_count:
            failures.append(f"{year} scene_count")
        for col, expected in [("mean_NDVI_P70", ndvi), ("mean_NDMI_P70", ndmi), ("mean_valid_obs", valid_obs)]:
            if not close(r[col], expected, args.index_tol):
                failures.append(f"{year} {col}")
        print(f"  {year}: NDVI={float(r['mean_NDVI_P70']):.6f} NDMI={float(r['mean_NDMI_P70']):.6f} valid_obs={float(r['mean_valid_obs']):.4f}")

    print("\nTime series:")
    by_target = {int(r["target_year"]): r for r in ts}
    for year, (ha, frac) in EXPECTED["time_series"].items():
        r = by_target.get(year)
        if r is None:
            failures.append(f"missing time-series year {year}")
            continue
        ok = close(r["spectral_loss_ha"], ha, args.area_tol_ha) and close(r["loss_fraction_of_2022_baseline"], frac, args.fraction_tol)
        print(f"  {year}: {float(r['spectral_loss_ha']):.6f} ha, {float(r['loss_fraction_of_2022_baseline']):.6f} {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"time series {year}")

    print("\nSensitivity:")
    if sens and "export_raster_valid_pixel_count" in sens[0]:
        failures.append("deprecated valid-pixel QA column still present in curated sensitivity CSV")
    by_name = {r["threshold_name"]: r for r in sens}
    ordered = []
    for name, (ha, frac, px, nominal_ha) in EXPECTED["sensitivity"].items():
        r = by_name.get(name)
        if r is None:
            failures.append(f"missing sensitivity {name}")
            continue
        ordered.append(float(r["spectral_loss_ha"]))
        ok = (
            close(r["spectral_loss_ha"], ha, args.area_tol_ha)
            and close(r["loss_fraction_of_2022_baseline"], frac, args.fraction_tol)
            and close(r["export_raster_loss_pixel_count"], px, 0.0)
            and close(r["export_raster_nominal_loss_area_ha"], nominal_ha, 1e-9)
        )
        print(f"  {name:8s}: {float(r['spectral_loss_ha']):.6f} ha, px={float(r['export_raster_loss_pixel_count']):.0f} {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"sensitivity {name}")
    if len(ordered) == 3 and not (ordered[0] >= ordered[1] >= ordered[2]):
        failures.append("sensitivity nesting Loose >= Standard >= Strict")

    if failures:
        print("\nFAIL")
        for item in failures:
            print(" -", item)
        raise SystemExit(1)

    print("\nPASS — curated V4 CSV outputs match the archived UTM51N run.")
    print("This validates archived numbers and metadata, not causality or tree classification.")


if __name__ == "__main__":
    main()
