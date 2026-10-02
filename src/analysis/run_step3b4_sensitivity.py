#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SC0002 Step 3B.4 sensitivity analysis.

Input:
  SC0002_STEP3B3_Site_Outcome_2022_2026.csv

Frozen design:
  treatment: SC0002
  controls: C162, C172, C176, C222, C129

Sensitivity analyses:
  1) leave-one-control-out (LOO)
  2) mean vs median vs trimmed mean
  3) treatment vs highest-loss control (most conservative single-control check)
  4) treatment vs lowest-loss control
  5) control influence on the mean
  6) valid-data coverage guardrail

This is descriptive matched-control sensitivity analysis.
It does NOT estimate a causal effect or a p-value.
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

TREATMENT = "SC0002"
CONTROLS = ["C162", "C172", "C176", "C222", "C129"]
POST_YEARS = [2023, 2024, 2025, 2026]

REQ_COLS = [
    "site_id",
    "site_type",
    "year",
    "loss_area_ha",
    "loss_fraction_of_2022_baseline",
    "baseline_veg_valid_fraction_this_year",
    "outcome_data_used_for_control_selection",
]


def write_csv_lf(df, path):
    """Write UTF-8 CSV with deterministic LF line endings on all OSes."""
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        df.to_csv(fh, index=False, lineterminator="\n")


def require_columns(df):
    missing = [c for c in REQ_COLS if c not in df.columns]
    if missing:
        raise SystemExit(
            "Missing required columns: " + ", ".join(missing)
        )


def pct(x):
    return f"{100.0 * float(x):.2f}%"


def pp(x):
    return f"{100.0 * float(x):+.2f} pp"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True,
                    help="SC0002_STEP3B3_Site_Outcome_2022_2026.csv")
    ap.add_argument("--outdir", default="step3b4_output")
    args = ap.parse_args()

    src = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(src)
    require_columns(df)

    df["year"] = pd.to_numeric(df["year"], errors="raise").astype(int)
    df["loss_fraction_of_2022_baseline"] = pd.to_numeric(
        df["loss_fraction_of_2022_baseline"],
        errors="raise",
    )
    df["baseline_veg_valid_fraction_this_year"] = pd.to_numeric(
        df["baseline_veg_valid_fraction_this_year"],
        errors="coerce",
    )

    observed_sites = set(df["site_id"].astype(str))
    expected_sites = {TREATMENT, *CONTROLS}
    if observed_sites != expected_sites:
        raise SystemExit(
            "Unexpected site set.\n"
            f"Expected: {sorted(expected_sites)}\n"
            f"Observed: {sorted(observed_sites)}"
        )

    flags = set(
        df["outcome_data_used_for_control_selection"]
        .astype(str).str.upper()
    )
    if flags != {"NO"}:
        raise SystemExit(
            "Outcome-selection provenance flag is not uniformly NO."
        )

    for year in POST_YEARS:
        y = df[df["year"] == year]
        if len(y) != 6:
            raise SystemExit(
                f"{year}: expected 6 site rows, found {len(y)}"
            )

    # ------------------------------------------------------------------
    # A. Full aggregation sensitivity
    # ------------------------------------------------------------------
    agg_rows = []

    for year in POST_YEARS:
        y = df[df["year"] == year].copy()
        t = y[y["site_id"] == TREATMENT].iloc[0]
        c = y[y["site_id"].isin(CONTROLS)].copy()

        tf = float(t["loss_fraction_of_2022_baseline"])
        cf = c["loss_fraction_of_2022_baseline"].astype(float)

        sorted_cf = np.sort(cf.to_numpy())
        trimmed3 = float(sorted_cf[1:-1].mean())  # drop min and max

        cmax_idx = c["loss_fraction_of_2022_baseline"].idxmax()
        cmin_idx = c["loss_fraction_of_2022_baseline"].idxmin()
        cmax = c.loc[cmax_idx]
        cmin = c.loc[cmin_idx]

        mean = float(cf.mean())
        median = float(cf.median())
        cmaxf = float(cmax["loss_fraction_of_2022_baseline"])
        cminf = float(cmin["loss_fraction_of_2022_baseline"])

        agg_rows.append({
            "year": year,
            "treatment_loss_fraction": tf,
            "control_mean": mean,
            "control_median": median,
            "control_trimmed_mean_drop_min_max": trimmed3,
            "control_min": cminf,
            "control_min_site": cmin["site_id"],
            "control_max": cmaxf,
            "control_max_site": cmax["site_id"],

            "diff_vs_mean_pp": 100*(tf-mean),
            "diff_vs_median_pp": 100*(tf-median),
            "diff_vs_trimmed_mean_pp": 100*(tf-trimmed3),
            "diff_vs_control_max_pp": 100*(tf-cmaxf),
            "diff_vs_control_min_pp": 100*(tf-cminf),

            "ratio_vs_mean": tf/mean if mean > 0 else np.nan,
            "ratio_vs_median": tf/median if median > 0 else np.nan,
            "ratio_vs_control_max": tf/cmaxf if cmaxf > 0 else np.nan,

            "treatment_gt_control_mean": tf > mean,
            "treatment_gt_control_median": tf > median,
            "treatment_gt_trimmed_mean": tf > trimmed3,
            "treatment_gt_every_control": bool((cf < tf).all()),

            "treatment_valid_fraction":
                float(t["baseline_veg_valid_fraction_this_year"]),
            "control_min_valid_fraction":
                float(c["baseline_veg_valid_fraction_this_year"].min()),
            "control_mean_valid_fraction":
                float(c["baseline_veg_valid_fraction_this_year"].mean()),
        })

    agg = pd.DataFrame(agg_rows)
    agg_path = outdir / "SC0002_STEP3B4_Aggregation_Sensitivity.csv"
    write_csv_lf(agg, agg_path)

    # ------------------------------------------------------------------
    # B. Leave-one-control-out
    # ------------------------------------------------------------------
    loo_rows = []

    for year in POST_YEARS:
        y = df[df["year"] == year].copy()
        t = y[y["site_id"] == TREATMENT].iloc[0]
        c = y[y["site_id"].isin(CONTROLS)].copy()

        tf = float(t["loss_fraction_of_2022_baseline"])

        full_mean = float(
            c["loss_fraction_of_2022_baseline"].mean()
        )

        for omitted in CONTROLS:
            remain = c[c["site_id"] != omitted].copy()
            rf = remain["loss_fraction_of_2022_baseline"].astype(float)

            loo_mean = float(rf.mean())
            loo_median = float(rf.median())
            loo_max = float(rf.max())

            omitted_f = float(
                c.loc[
                    c["site_id"] == omitted,
                    "loss_fraction_of_2022_baseline"
                ].iloc[0]
            )

            loo_rows.append({
                "year": year,
                "omitted_control": omitted,
                "omitted_control_loss_fraction": omitted_f,

                "full_5_control_mean": full_mean,
                "loo_4_control_mean": loo_mean,
                "loo_4_control_median": loo_median,
                "loo_4_control_max": loo_max,

                "change_in_control_mean_when_omitted_pp":
                    100*(loo_mean-full_mean),

                "treatment_loss_fraction": tf,
                "treatment_minus_loo_mean_pp":
                    100*(tf-loo_mean),
                "treatment_minus_loo_median_pp":
                    100*(tf-loo_median),
                "treatment_minus_loo_max_pp":
                    100*(tf-loo_max),

                "treatment_to_loo_mean_ratio":
                    tf/loo_mean if loo_mean > 0 else np.nan,

                "treatment_gt_loo_mean": tf > loo_mean,
                "treatment_gt_all_remaining_controls":
                    bool((rf < tf).all()),

                "remaining_control_min_valid_fraction":
                    float(
                        remain[
                            "baseline_veg_valid_fraction_this_year"
                        ].min()
                    ),
            })

    loo = pd.DataFrame(loo_rows)
    loo_path = outdir / "SC0002_STEP3B4_Leave_One_Control_Out.csv"
    write_csv_lf(loo, loo_path)

    # ------------------------------------------------------------------
    # C. Influence summary by control across all post years
    # ------------------------------------------------------------------
    influence = (
        loo.groupby("omitted_control")
        .agg(
            mean_abs_change_in_control_mean_pp=(
                "change_in_control_mean_when_omitted_pp",
                lambda s: float(np.mean(np.abs(s))),
            ),
            max_abs_change_in_control_mean_pp=(
                "change_in_control_mean_when_omitted_pp",
                lambda s: float(np.max(np.abs(s))),
            ),
            min_treatment_minus_loo_mean_pp=(
                "treatment_minus_loo_mean_pp",
                "min",
            ),
            max_treatment_minus_loo_mean_pp=(
                "treatment_minus_loo_mean_pp",
                "max",
            ),
            all_years_treatment_gt_loo_mean=(
                "treatment_gt_loo_mean",
                "all",
            ),
            all_years_treatment_gt_remaining_controls=(
                "treatment_gt_all_remaining_controls",
                "all",
            ),
        )
        .reset_index()
        .sort_values(
            "max_abs_change_in_control_mean_pp",
            ascending=False,
        )
    )

    influence_path = outdir / "SC0002_STEP3B4_Control_Influence.csv"
    write_csv_lf(influence, influence_path)

    # ------------------------------------------------------------------
    # D. Per-year robustness envelope
    # ------------------------------------------------------------------
    envelope_rows = []

    for year in POST_YEARS:
        a = agg[agg["year"] == year].iloc[0]
        l = loo[loo["year"] == year].copy()

        envelope_rows.append({
            "year": year,
            "treatment_loss_fraction":
                a["treatment_loss_fraction"],

            "full_control_mean":
                a["control_mean"],
            "full_control_median":
                a["control_median"],
            "control_max":
                a["control_max"],
            "control_max_site":
                a["control_max_site"],

            "min_loo_control_mean":
                l["loo_4_control_mean"].min(),
            "max_loo_control_mean":
                l["loo_4_control_mean"].max(),

            "smallest_treatment_minus_loo_mean_pp":
                l["treatment_minus_loo_mean_pp"].min(),
            "largest_treatment_minus_loo_mean_pp":
                l["treatment_minus_loo_mean_pp"].max(),

            "smallest_treatment_minus_any_control_pp":
                a["diff_vs_control_max_pp"],

            "all_5_loo_means_below_treatment":
                bool(l["treatment_gt_loo_mean"].all()),
            "all_5_loo_sets_have_all_controls_below_treatment":
                bool(
                    l["treatment_gt_all_remaining_controls"].all()
                ),

            "valid_data_guardrail_pass":
                (
                    float(a["treatment_valid_fraction"]) >= 0.95
                    and float(a["control_min_valid_fraction"]) >= 0.95
                ),
        })

    env = pd.DataFrame(envelope_rows)
    env_path = outdir / "SC0002_STEP3B4_Robustness_By_Year.csv"
    write_csv_lf(env, env_path)

    # ------------------------------------------------------------------
    # E. Overall pass/fail summary
    # ------------------------------------------------------------------
    overall = {
        "all_years_treatment_gt_control_mean":
            bool(agg["treatment_gt_control_mean"].all()),
        "all_years_treatment_gt_control_median":
            bool(agg["treatment_gt_control_median"].all()),
        "all_years_treatment_gt_trimmed_mean":
            bool(agg["treatment_gt_trimmed_mean"].all()),
        "all_years_treatment_gt_every_control":
            bool(agg["treatment_gt_every_control"].all()),
        "all_years_all_loo_means_below_treatment":
            bool(env["all_5_loo_means_below_treatment"].all()),
        "all_years_valid_data_guardrail_pass":
            bool(env["valid_data_guardrail_pass"].all()),
    }

    summary_lines = []
    summary_lines.append(
        "SC0002 STEP 3B.4 — MATCHED-CONTROL SENSITIVITY"
    )
    summary_lines.append("=" * 62)
    summary_lines.append("")
    summary_lines.append(
        "Frozen controls: " + ", ".join(CONTROLS)
    )
    summary_lines.append(
        "No control replacement was permitted in this analysis."
    )
    summary_lines.append("")

    summary_lines.append("Aggregation sensitivity")
    summary_lines.append("-" * 30)
    for _, r in agg.iterrows():
        summary_lines.append(
            f"{int(r.year)}: "
            f"SC0002={pct(r.treatment_loss_fraction)}; "
            f"mean={pct(r.control_mean)} "
            f"(diff {pp(r.diff_vs_mean_pp/100)}); "
            f"median={pct(r.control_median)} "
            f"(diff {pp(r.diff_vs_median_pp/100)}); "
            f"trimmed={pct(r.control_trimmed_mean_drop_min_max)} "
            f"(diff {pp(r.diff_vs_trimmed_mean_pp/100)}); "
            f"highest control={r.control_max_site} "
            f"{pct(r.control_max)} "
            f"(conservative gap {pp(r.diff_vs_control_max_pp/100)})"
        )

    summary_lines.append("")
    summary_lines.append("Leave-one-control-out envelope")
    summary_lines.append("-" * 34)

    for _, r in env.iterrows():
        summary_lines.append(
            f"{int(r.year)}: "
            f"LOO control mean range="
            f"{pct(r.min_loo_control_mean)}–"
            f"{pct(r.max_loo_control_mean)}; "
            f"smallest SC0002-minus-LOO-mean gap="
            f"{r.smallest_treatment_minus_loo_mean_pp:+.2f} pp"
        )

    summary_lines.append("")
    summary_lines.append("Overall robustness checks")
    summary_lines.append("-" * 29)

    for k, v in overall.items():
        summary_lines.append(
            f"[{'PASS' if v else 'FAIL'}] {k}"
        )

    summary_lines.append("")
    summary_lines.append("Interpretation")
    summary_lines.append("-" * 14)

    if all(overall.values()):
        summary_lines.append(
            "The descriptive treatment-control separation is robust to "
            "leave-one-control-out analysis, aggregation choice "
            "(mean/median/trimmed mean), comparison with the highest-loss "
            "individual control, and valid-data coverage."
        )
    else:
        summary_lines.append(
            "At least one robustness check did not pass; inspect the CSV "
            "outputs before drawing a conclusion."
        )

    summary_lines.append("")
    summary_lines.append(
        "This remains matched-control descriptive evidence. "
        "Do not label the gaps as causal treatment effects without "
        "additional causal-identification assumptions."
    )

    summary_path = outdir / "SC0002_STEP3B4_Summary.txt"
    summary_path.write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print("\n".join(summary_lines))
    print()
    print("Wrote:")
    for p in [
        agg_path,
        loo_path,
        influence_path,
        env_path,
        summary_path,
    ]:
        print(" ", p.resolve())


if __name__ == "__main__":
    main()
