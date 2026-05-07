#!/usr/bin/env python3
"""make_doe_summary.py -- aggregate DoE-wide figures once the campaign finishes.

Inputs  : <results_dir>/case_NN/all_metrics.csv   (per-case, from all_metrics.py)
          <results_dir>/../doe_cases/doe_design.csv  (or an explicit --design)

Outputs : <results_dir>/summary/
          fig_scatter_CoV_vs_dD.png         CoV_m  vs  d/D, coloured by HBR
          fig_scatter_CoV_vs_VR.png         CoV_m  vs  VR , coloured by HBR
          fig_scatter_dP_vs_HBR.png         Delta p vs HBR, coloured by d/D
          fig_CoV_heatmap_dD_VR.png         2D interpolated heatmap of CoV_m
          fig_dP_heatmap_dD_VR.png          2D heatmap of Delta p
          doe_summary.csv                   joined design + metrics table
          DOE_SUMMARY.md                    human-readable write-up

Works even if only a subset of cases are complete; missing cases are just
skipped with a warning.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation


DESIGN_COLS = ("case", "d_over_D", "HBR", "VR",
               "D2_m", "U_main_mps", "U_branch_mps", "slice_id")

METRIC_ALIASES = {
    # Aliases extended to match the current all_metrics.py schema
    # (H2_<stat>_<weight> with weight in {area, mass, vol}).
    "CoV_area":        ("H2_CoV_area", "CoV_area", "CoV_A", "cov_area"),
    "CoV_massFlux":    ("H2_CoV_mass", "CoV_massFlux", "CoV_mdot", "CoV_m", "cov_mass"),
    "CoV_volumeFlux":  ("H2_CoV_vol", "CoV_volumeFlux", "CoV_vol", "CoV_V", "cov_vol"),
    "Is":              ("H2_Is_mass", "H2_Is_area", "Is", "danckwerts_Is", "intensity_of_segregation"),
    "dP_static":       ("dP_p_mass", "dP_p_area", "dP_static", "dP_pstatic", "dp_static"),
    "dP_total":        ("dP_p_total_mass", "dP_p_total_area", "dP_total", "dp_total"),
    "dP_gauge":        ("dP_p_rgh_mass", "dP_p_rgh_area", "dP_gauge", "dp_gauge"),
}


def _read_csv_rows(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def _find_key(row: dict, aliases: tuple[str, ...]) -> str | None:
    for a in aliases:
        if a in row:
            return a
    return None


def _maybe_float(s, default=float("nan")) -> float:
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def _join(design_csv: Path, results_dir: Path) -> list[dict]:
    rows = _read_csv_rows(design_csv)
    joined = []
    for r in rows:
        cid = int(r["case"])
        out = {k: _maybe_float(r[k]) if k != "slice_id" else int(float(r[k]))
               for k in DESIGN_COLS if k in r}
        out["case"] = cid

        mpath = results_dir / f"case_{cid:02d}" / "all_metrics.csv"
        if not mpath.exists():
            out["_status"] = "missing"
            joined.append(out)
            continue

        m_rows = _read_csv_rows(mpath)
        if not m_rows:
            out["_status"] = "empty"
            joined.append(out)
            continue

        # all_metrics.csv typically has one row per case/label; we take the
        # last row (time-averaged metrics).
        m = m_rows[-1]
        out["_status"] = "ok"
        for key, aliases in METRIC_ALIASES.items():
            col = _find_key(m, aliases)
            out[key] = _maybe_float(m[col]) if col else float("nan")
        joined.append(out)

    return joined


def _write_joined_csv(rows: list[dict], path: Path) -> None:
    # Union of keys across all rows -- some rows (e.g. cases without metrics)
    # have a smaller schema than rows where the per-case CSV provided extra
    # alias columns.  Using only rows[0].keys() drops fields and trips
    # DictWriter strict mode.
    keys: list[str] = []
    seen: set[str] = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                keys.append(k)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def _scatter(xs, ys, cs, xlabel, ylabel, clabel, out: Path,
             title: str = "", cmap: str = "viridis"):
    fig, ax = plt.subplots(figsize=(6.5, 5.0), dpi=130)
    sc = ax.scatter(xs, ys, c=cs, cmap=cmap, s=80, edgecolor="k", linewidth=0.6)
    cb = fig.colorbar(sc, ax=ax)
    cb.set_label(clabel)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3, linestyle=":")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"  wrote {out.name}")


def _heatmap(xs, ys, zs, xlabel, ylabel, zlabel, out: Path,
             cmap: str = "viridis"):
    xs = np.asarray(xs); ys = np.asarray(ys); zs = np.asarray(zs)
    mask = np.isfinite(zs)
    if mask.sum() < 4:
        print(f"  [skip] {out.name}: not enough data ({mask.sum()} points)")
        return
    xs = xs[mask]; ys = ys[mask]; zs = zs[mask]

    fig, ax = plt.subplots(figsize=(6.5, 5.0), dpi=130)
    tri = Triangulation(xs, ys)
    tpc = ax.tripcolor(tri, zs, cmap=cmap, shading="gouraud")
    ax.scatter(xs, ys, c="white", s=40, edgecolor="black", linewidth=0.6, zorder=3)
    cb = fig.colorbar(tpc, ax=ax)
    cb.set_label(zlabel)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25, linestyle=":")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"  wrote {out.name}")


def _write_markdown(rows: list[dict], outdir: Path, results_dir: Path) -> None:
    md = outdir / "DOE_SUMMARY.md"
    have = [r for r in rows if r.get("_status") == "ok"]
    missing = [r for r in rows if r.get("_status") != "ok"]

    def fmt(v, spec="%.4g"):
        return spec % v if isinstance(v, (int, float)) and np.isfinite(v) else "-"

    lines = []
    lines.append("# DoE Summary")
    lines.append("")
    lines.append(f"Generated from `{results_dir}`.  "
                 f"Completed cases : **{len(have)} / {len(rows)}**.")
    if missing:
        lines.append("")
        lines.append("Missing / incomplete cases : "
                     + ", ".join(f"case_{r['case']:02d}" for r in missing))
    lines.append("")
    lines.append("## Per-case table")
    lines.append("")
    lines.append(
        "| case | d/D | HBR% | VR | CoV_A | CoV_ṁ | CoV_V | I_s | "
        "Δp_stat [Pa] | Δp_tot [Pa] |"
    )
    lines.append(
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    for r in rows:
        lines.append(
            f"| {int(r['case']):02d} | {fmt(r['d_over_D'], '%.3f')} | "
            f"{fmt(r['HBR']*100, '%.1f')} | {fmt(r['VR'], '%.3f')} | "
            f"{fmt(r.get('CoV_area'))} | {fmt(r.get('CoV_massFlux'))} | "
            f"{fmt(r.get('CoV_volumeFlux'))} | {fmt(r.get('Is'))} | "
            f"{fmt(r.get('dP_static'))} | {fmt(r.get('dP_total'))} |"
        )
    lines.append("")
    md.write_text("\n".join(lines) + "\n")
    print(f"  wrote {md.name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", required=True, type=Path,
                    help="Path to doe_results/ (contains case_NN/all_metrics.csv)")
    ap.add_argument("--design", type=Path, default=None,
                    help="Path to doe_design.csv (defaults to sibling of results)")
    args = ap.parse_args()

    results = args.results.resolve()
    design = args.design or (results.parent / "doe_cases" / "doe_design.csv")
    if not design.exists():
        fallback = results.parent / "doe_base" / "doe" / "doe_design.csv"
        if fallback.exists():
            design = fallback
    if not design.exists():
        raise SystemExit(f"cannot find doe_design.csv (tried {design})")

    outdir = results / "summary"
    outdir.mkdir(parents=True, exist_ok=True)

    rows = _join(design, results)
    _write_joined_csv(rows, outdir / "doe_summary.csv")

    ok = [r for r in rows if r.get("_status") == "ok"]
    if not ok:
        print("No completed cases yet -- skipping figures.")
        _write_markdown(rows, outdir, results)
        return

    xs_d = [r["d_over_D"] for r in ok]
    xs_v = [r["VR"]       for r in ok]
    xs_h = [r["HBR"]*100  for r in ok]
    ys_covm = [r.get("CoV_massFlux", float("nan")) for r in ok]
    ys_covA = [r.get("CoV_area",     float("nan")) for r in ok]
    ys_dp   = [r.get("dP_static",    float("nan")) for r in ok]

    _scatter(xs_d, ys_covm, xs_h,
             "d / D", "CoV (mass-flux weighted)", "HBR [%]",
             outdir / "fig_scatter_CoV_vs_dD.png",
             title="Mixing quality vs. diameter ratio")
    _scatter(xs_v, ys_covm, xs_h,
             "VR = U_branch / U_main", "CoV (mass-flux weighted)", "HBR [%]",
             outdir / "fig_scatter_CoV_vs_VR.png",
             title="Mixing quality vs. velocity ratio")
    _scatter(xs_h, ys_dp, xs_d,
             "HBR [%]", "Δp static [Pa]", "d / D",
             outdir / "fig_scatter_dP_vs_HBR.png", cmap="plasma",
             title="Pressure drop vs. H2 blend ratio")
    _heatmap(xs_d, xs_v, ys_covm,
             "d / D", "VR", "CoV (mass-flux weighted)",
             outdir / "fig_CoV_heatmap_dD_VR.png", cmap="viridis")
    _heatmap(xs_d, xs_v, ys_dp,
             "d / D", "VR", "Δp static [Pa]",
             outdir / "fig_dP_heatmap_dD_VR.png", cmap="plasma")

    _write_markdown(rows, outdir, results)
    print(f"\nSummary pack in {outdir}")


if __name__ == "__main__":
    main()
