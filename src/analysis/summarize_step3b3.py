#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Summarize SC0002 Step 3B.3 treatment-vs-control outcome results.

This script does NOT select or replace controls.
The frozen controls must already be present in the GEE output:
C162, C172, C176, C222, C129.

Outputs:
- SC0002_STEP3B3_Baseline_2022.csv
- SC0002_STEP3B3_Treatment_vs_Control.csv
- SC0002_STEP3B3_2026_Site_Ranking.csv
- SC0002_STEP3B3_Summary.txt
"""

import argparse
from pathlib import Path
import math
import pandas as pd
import numpy as np

EXPECTED_TREATMENT = "SC0002"
EXPECTED_CONTROLS = ["C162", "C172", "C176", "C222", "C129"]
EXPECTED_YEARS = [2022, 2023, 2024, 2025, 2026]

# Prior SC0002 V4 reference values. These are QA anchors only.
# A small difference can occur if Earth Engine source processing changes.
SC_REF = {
    2022: {"baseline_veg_area_ha": 58.239810},
    2023: {"loss_area_ha": 14.947461,
           "loss_fraction_of_2022_baseline": 0.256654},
    2024: {"loss_area_ha": 11.043818,
           "loss_fraction_of_2022_baseline": 0.189627},
    2025: {"loss_area_ha": 21.545707,
           "loss_fraction_of_2022_baseline": 0.369948},
    2026: {"loss_area_ha": 16.795013,
           "loss_fraction_of_2022_baseline": 0.288377},
}


def write_csv_lf(df, path):
    """Write UTF-8 CSV with deterministic LF line endings on all OSes."""
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        df.to_csv(fh, index=False, lineterminator="\n")


def require_columns(df, names):
    missing = [x for x in names if x not in df.columns]
    if missing:
        raise SystemExit(
            "Missing required columns: " + ", ".join(missing)
        )


def pct(x):
    if pd.isna(x):
        return "N/A"
    return f"{100*x:.2f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", default="step3b3_summary")
    args = ap.parse_args()

    src = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(src)

    required = [
        "site_id",
        "site_type",
        "year",
        "baseline_veg_area_ha",
        "baseline_veg_fraction_of_site",
        "baseline_veg_valid_fraction_this_year",
        "loss_area_ha",
        "loss_fraction_of_2022_baseline",
        "loss_fraction_of_valid_2022_baseline",
        "mean_ndvi_p70",
        "mean_ndmi_p70",
        "mean_valid_obs",
        "scene_count",
        "outcome_data_used_for_control_selection",
    ]
    require_columns(df, required)

    df["year"] = pd.to_numeric(
        df["year"], errors="raise"
    ).astype(int)

    ids = set(df["site_id"].astype(str))
    expected_ids = {
        EXPECTED_TREATMENT,
        *EXPECTED_CONTROLS,
    }

    if ids != expected_ids:
        raise SystemExit(
            "Unexpected site set.\n"
            f"Expected: {sorted(expected_ids)}\n"
            f"Observed: {sorted(ids)}"
        )

    if sorted(df["year"].unique().tolist()) != EXPECTED_YEARS:
        raise SystemExit(
            "Unexpected year set: "
            + repr(sorted(df["year"].unique().tolist()))
        )

    # Exactly one row per site/year.
    counts = df.groupby(["site_id","year"]).size()
    if not (counts == 1).all():
        raise SystemExit(
            "Duplicate or missing site/year rows detected."
        )

    # Confirm outcome was not reported as used for selection.
    selection_flags = set(
        df["outcome_data_used_for_control_selection"]
        .astype(str)
        .str.upper()
    )
    if selection_flags != {"NO"}:
        raise SystemExit(
            "Control-selection provenance flag is not uniformly NO."
        )

    # Baseline table.
    baseline = df[df["year"] == 2022].copy()
    baseline = baseline[
        [
            "site_id",
            "site_type",
            "baseline_veg_area_ha",
            "baseline_veg_fraction_of_site",
            "mean_ndvi_p70",
            "mean_ndmi_p70",
            "mean_valid_obs",
            "scene_count",
        ]
    ].sort_values(
        ["site_type","site_id"],
        ascending=[False, True],
    )

    baseline_path = (
        outdir / "SC0002_STEP3B3_Baseline_2022.csv"
    )
    write_csv_lf(baseline, baseline_path)

    # Main treatment vs controls.
    rows = []

    for year in [2023, 2024, 2025, 2026]:
        y = df[df["year"] == year].copy()

        t = y[y["site_id"] == EXPECTED_TREATMENT].iloc[0]
        c = y[y["site_id"].isin(EXPECTED_CONTROLS)].copy()

        tf = float(t["loss_fraction_of_2022_baseline"])
        cf = pd.to_numeric(
            c["loss_fraction_of_2022_baseline"],
            errors="coerce",
        )

        control_mean = float(cf.mean())
        control_median = float(cf.median())
        control_min = float(cf.min())
        control_max = float(cf.max())

        ratio = (
            tf / control_mean
            if control_mean > 0
            else np.nan
        )

        # Descriptive ordering only; NOT an inferential p-value.
        all_fracs = [tf] + cf.tolist()
        treatment_rank_desc = (
            1
            + sum(
                x > tf
                for x in cf.tolist()
                if not pd.isna(x)
            )
        )

        rows.append({
            "year": year,
            "treatment_loss_area_ha":
                float(t["loss_area_ha"]),
            "treatment_loss_fraction":
                tf,

            "control_n": int(len(c)),
            "control_mean_loss_fraction":
                control_mean,
            "control_median_loss_fraction":
                control_median,
            "control_min_loss_fraction":
                control_min,
            "control_max_loss_fraction":
                control_max,

            "difference_vs_control_mean_fraction":
                tf - control_mean,
            "difference_vs_control_mean_pp":
                100.0 * (tf - control_mean),

            "difference_vs_control_median_fraction":
                tf - control_median,
            "difference_vs_control_median_pp":
                100.0 * (tf - control_median),

            "treatment_to_control_mean_ratio":
                ratio,

            "controls_ge_treatment":
                int((cf >= tf).sum()),
            "controls_gt_treatment":
                int((cf > tf).sum()),
            "treatment_rank_desc_among_6":
                int(treatment_rank_desc),

            "treatment_baseline_valid_fraction_this_year":
                float(t["baseline_veg_valid_fraction_this_year"]),
            "control_mean_baseline_valid_fraction_this_year":
                float(pd.to_numeric(
                    c["baseline_veg_valid_fraction_this_year"],
                    errors="coerce",
                ).mean()),
        })

    comparison = pd.DataFrame(rows)

    comparison_path = (
        outdir / "SC0002_STEP3B3_Treatment_vs_Control.csv"
    )
    write_csv_lf(comparison, comparison_path)

    # 2026 site ranking.
    y26 = df[df["year"] == 2026].copy()

    ranking = y26[
        [
            "site_id",
            "site_type",
            "selected_control_order",
            "pre_treatment_match_score",
            "baseline_veg_area_ha",
            "loss_area_ha",
            "loss_fraction_of_2022_baseline",
            "baseline_veg_valid_fraction_this_year",
            "mean_ndvi_p70",
            "mean_ndmi_p70",
            "mean_valid_obs",
        ]
    ].sort_values(
        "loss_fraction_of_2022_baseline",
        ascending=False,
    ).reset_index(drop=True)

    ranking.insert(
        0,
        "rank_loss_fraction_desc",
        range(1, len(ranking)+1),
    )

    ranking_path = (
        outdir / "SC0002_STEP3B3_2026_Site_Ranking.csv"
    )
    write_csv_lf(ranking, ranking_path)

    # SC0002 V4 consistency check.
    qa_lines = []
    sc = df[df["site_id"] == EXPECTED_TREATMENT].set_index("year")

    base_observed = float(
        sc.loc[2022, "baseline_veg_area_ha"]
    )
    base_ref = SC_REF[2022]["baseline_veg_area_ha"]
    qa_lines.append(
        f"2022 baseline area: observed={base_observed:.6f} ha, "
        f"reference={base_ref:.6f} ha, "
        f"diff={base_observed-base_ref:+.6f} ha"
    )

    for year in [2023, 2024, 2025, 2026]:
        obs_a = float(sc.loc[year, "loss_area_ha"])
        ref_a = SC_REF[year]["loss_area_ha"]
        obs_f = float(
            sc.loc[
                year,
                "loss_fraction_of_2022_baseline"
            ]
        )
        ref_f = SC_REF[year][
            "loss_fraction_of_2022_baseline"
        ]

        qa_lines.append(
            f"{year}: loss observed={obs_a:.6f} ha "
            f"({100*obs_f:.4f}%), "
            f"reference={ref_a:.6f} ha "
            f"({100*ref_f:.4f}%), "
            f"diff={obs_a-ref_a:+.6f} ha / "
            f"{100*(obs_f-ref_f):+.4f} pp"
        )

    # Summary.
    lines = []
    lines.append("SC0002 STEP 3B.3 — TREATMENT VS FROZEN CONTROLS")
    lines.append("=" * 62)
    lines.append("")
    lines.append(
        "Frozen controls: "
        + ", ".join(EXPECTED_CONTROLS)
    )
    lines.append(
        "Outcome data used for control selection: NO"
    )
    lines.append("")

    lines.append("SC0002 V4 consistency QA")
    lines.append("-" * 30)
    lines.extend(qa_lines)
    lines.append("")

    lines.append("Treatment vs control distribution")
    lines.append("-" * 34)

    for _, r in comparison.iterrows():
        lines.append(
            f"{int(r.year)}: "
            f"SC0002={pct(r.treatment_loss_fraction)}; "
            f"control mean={pct(r.control_mean_loss_fraction)}; "
            f"median={pct(r.control_median_loss_fraction)}; "
            f"range={pct(r.control_min_loss_fraction)}"
            f"–{pct(r.control_max_loss_fraction)}; "
            f"diff vs mean="
            f"{r.difference_vs_control_mean_pp:+.2f} pp; "
            f"rank={int(r.treatment_rank_desc_among_6)}/6"
        )

    lines.append("")
    lines.append("2026 site ordering by loss fraction")
    lines.append("-" * 36)

    for _, r in ranking.iterrows():
        lines.append(
            f"{int(r.rank_loss_fraction_desc)}. "
            f"{r.site_id}: "
            f"{100*float(r.loss_fraction_of_2022_baseline):.2f}% "
            f"({float(r.loss_area_ha):.3f} ha)"
        )

    lines.append("")
    lines.append("Interpretation guardrails")
    lines.append("-" * 25)
    lines.append(
        "* This is a matched-control descriptive comparison."
    )
    lines.append(
        "* Do not call the control-mean difference a causal effect without "
        "additional design assumptions."
    )
    lines.append(
        "* The five controls were frozen before any 2023-2026 NDVI/NDMI "
        "outcomes were calculated."
    )
    lines.append(
        "* 2023-2026 annual loss masks are not cumulative; pixels can cross "
        "thresholds differently across years."
    )
    lines.append(
        "* Check baseline-valid fractions before interpreting unusually low "
        "or high annual values."
    )

    summary_path = (
        outdir / "SC0002_STEP3B3_Summary.txt"
    )
    summary_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print("\n".join(lines))
    print()
    print("Wrote:")
    print(" ", baseline_path.resolve())
    print(" ", comparison_path.resolve())
    print(" ", ranking_path.resolve())
    print(" ", summary_path.resolve())


if __name__ == "__main__":
    main()
