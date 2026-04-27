#!/usr/bin/env python3
"""aggregate_30deg.py

Aggregates per-case metrics from `all_metrics.csv` files of the 30 deg DoE
into a single summary CSV plus a pack of scatter / heatmap figures
(CoV vs d/D, VR, HBR; same for Delta p).

Inputs:
    doe_design.csv               -- with case, d_over_D, HBR, VR, ...
    cases/case_NN/metrics_out/all_metrics.csv  -- per-case metrics

Outputs (in <outdir>):
    doe_summary_30deg.csv
    fig_scatter_CoV_mass_vs_dD.png
    fig_scatter_CoV_mass_vs_VR.png
    fig_scatter_CoV_mass_vs_HBR.png
    fig_scatter_dP_vs_HBR.png
    fig_scatter_dP_vs_VR.png
    fig_CoV_heatmap_dD_VR.png
    fig_dP_heatmap_dD_VR.png
    fig_pareto_dP_vs_CoV.png
    DOE_SUMMARY_30DEG.md
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_csv_dicts(p: Path) -> list[dict]:
    with p.open() as f:
        return list(csv.DictReader(f))


def fnum(s, default=float("nan")) -> float:
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def aggregate(design_csv: Path, cases_dir: Path) -> list[dict]:
    rows = read_csv_dicts(design_csv)
    summary = []
    for r in rows:
        cid = int(float(r["case"]))
        rec = {
            "case": cid,
            "d_over_D": fnum(r["d_over_D"]),
            "HBR": fnum(r["HBR"]),
            "VR": fnum(r["VR"]),
            "D2_m": fnum(r["D2_m"]),
            "U_branch_mps": fnum(r["U_branch_mps"]),
            "Re_branch": fnum(r["Re_branch"]),
            "alpha_deg": fnum(r["alpha_deg"]),
            "slice_id": int(float(r["slice_id"])),
        }
        m_path = cases_dir / f"case_{cid:02d}" / "metrics_out" / "all_metrics.csv"
        if not m_path.exists():
            rec["status"] = "missing"
            summary.append(rec)
            continue
        mrows = read_csv_dicts(m_path)
        avg = next((x for x in mrows if x.get("time") == "AVG"), None)
        if avg is None:
            rec["status"] = "no_avg_row"
            summary.append(rec)
            continue
        rec["status"] = "ok"
        # CoV and Is, on time-averaged H2 field (preferred) and from snapshots
        for w in ("area", "mass", "vol"):
            rec[f"CoV_{w}_tavg"]   = fnum(avg.get(f"H2_CoV_{w}_tavg"))
            rec[f"CoV_{w}_snap"]   = fnum(avg.get(f"H2_CoV_{w}"))
            rec[f"Is_{w}_tavg"]    = fnum(avg.get(f"H2_Is_{w}_tavg"))
            rec[f"meanH2_{w}_tavg"]= fnum(avg.get(f"H2_mean_{w}_tavg"))
        # Delta P: prefer the clean time-series area-weighted p_rgh (Pa), in kPa
        rec["dP_prgh_area_ts_kPa"] = fnum(avg.get("dP_prgh_area_ts")) / 1000.0
        # Snapshot-based static dP (noisy but full menu)
        for w in ("area", "mass", "vol"):
            rec[f"dP_p_{w}_kPa"]       = fnum(avg.get(f"dP_p_{w}")) / 1000.0
            rec[f"dP_p_rgh_{w}_kPa"]   = fnum(avg.get(f"dP_p_rgh_{w}")) / 1000.0
            rec[f"dP_total_{w}_kPa"]   = fnum(avg.get(f"dP_p_total_{w}")) / 1000.0
        rec["H2_outletAvg_ts"] = fnum(avg.get("H2_outletAvg_ts_mean"))
        summary.append(rec)
    return summary


# ---- plotting --------------------------------------------------------------

def _ok(rows):
    return [r for r in rows if r.get("status") == "ok"]


def scatter_xy(rows, xkey, ykey, ckey, *, xlabel, ylabel, clabel, title, out):
    rows = _ok(rows)
    x = np.array([r[xkey] for r in rows])
    y = np.array([r[ykey] for r in rows])
    c = np.array([r[ckey] for r in rows])
    fig, ax = plt.subplots(figsize=(6.5, 5.0), dpi=140)
    sc = ax.scatter(x, y, c=c, cmap="viridis", s=120, edgecolor="black", linewidth=0.6)
    for r in rows:
        ax.annotate(f"{r['case']:02d}", (r[xkey], r[ykey]),
                    textcoords="offset points", xytext=(6, 6), fontsize=9)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label(clabel)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out}")


def heatmap_dD_VR(rows, zkey, *, title, zlabel, out, log_VR=True):
    rows = _ok(rows)
    x = np.array([r["d_over_D"] for r in rows])
    y = np.array([r["VR"] for r in rows])
    z = np.array([r[zkey] for r in rows])
    if log_VR:
        y_plot = np.log10(y)
        ylabel = r"log$_{10}$(VR)"
    else:
        y_plot = y
        ylabel = "VR"
    # build a smooth interpolated heatmap via Triangulation
    from matplotlib.tri import Triangulation, LinearTriInterpolator
    tri = Triangulation(x, y_plot)
    interp = LinearTriInterpolator(tri, z)
    xi = np.linspace(x.min(), x.max(), 120)
    yi = np.linspace(y_plot.min(), y_plot.max(), 120)
    XI, YI = np.meshgrid(xi, yi)
    ZI = interp(XI, YI)
    fig, ax = plt.subplots(figsize=(7.0, 5.0), dpi=140)
    pc = ax.pcolormesh(XI, YI, ZI, cmap="viridis", shading="auto")
    cbar = fig.colorbar(pc, ax=ax)
    cbar.set_label(zlabel)
    ax.scatter(x, y_plot, c="white", s=80, edgecolor="black", linewidth=0.8, zorder=5)
    for r in rows:
        ax.annotate(f"{r['case']:02d}", (r["d_over_D"], np.log10(r["VR"]) if log_VR else r["VR"]),
                    textcoords="offset points", xytext=(6, 6), fontsize=9, color="white",
                    weight="bold")
    ax.set_xlabel("d/D")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out}")


def pareto_dP_vs_CoV(rows, *, out):
    rows = _ok(rows)
    cov = np.array([r["CoV_mass_tavg"] for r in rows])
    dp  = np.array([abs(r["dP_prgh_area_ts_kPa"]) for r in rows])
    hbr = np.array([r["HBR"] for r in rows])
    fig, ax = plt.subplots(figsize=(6.5, 5.0), dpi=140)
    sc = ax.scatter(cov, dp, c=hbr, cmap="plasma", s=130, edgecolor="black", linewidth=0.7)
    for r in rows:
        ax.annotate(f"{r['case']:02d}", (r["CoV_mass_tavg"], abs(r["dP_prgh_area_ts_kPa"])),
                    textcoords="offset points", xytext=(7, 7), fontsize=9)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("HBR (H$_2$ blend ratio)")
    ax.axvline(0.05, color="red", linestyle="--", linewidth=1.0, alpha=0.6)
    ax.text(0.052, ax.get_ylim()[1]*0.95, "industry CoV target = 5%",
            fontsize=9, color="red", verticalalignment="top")
    ax.set_xlabel("CoV (mass-flux weighted, time-averaged H$_2$)")
    ax.set_ylabel(r"$|\Delta p|$ (kPa, area-weighted, $p_{rgh}$, time-series)")
    ax.set_title("30 deg: Pareto frontier — pressure-drop vs. mixing")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out}")


def write_csv(rows, out: Path):
    keys = sorted({k for r in rows for k in r.keys()})
    # put case + design columns first
    head = ["case", "alpha_deg", "slice_id", "d_over_D", "HBR", "VR",
            "D2_m", "U_branch_mps", "Re_branch", "status",
            "CoV_area_tavg", "CoV_mass_tavg", "CoV_vol_tavg",
            "Is_area_tavg",  "Is_mass_tavg",  "Is_vol_tavg",
            "meanH2_area_tavg", "meanH2_mass_tavg", "meanH2_vol_tavg",
            "H2_outletAvg_ts",
            "dP_prgh_area_ts_kPa",
            "dP_p_area_kPa", "dP_p_mass_kPa", "dP_p_vol_kPa",
            "dP_p_rgh_area_kPa", "dP_p_rgh_mass_kPa", "dP_p_rgh_vol_kPa",
            "dP_total_area_kPa", "dP_total_mass_kPa", "dP_total_vol_kPa",
            "CoV_area_snap", "CoV_mass_snap", "CoV_vol_snap"]
    # append any other keys not in head
    extras = [k for k in keys if k not in head]
    head = head + extras
    with out.open("w") as f:
        w = csv.DictWriter(f, fieldnames=head, restval="")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"  wrote {out}")


def write_md(rows, out: Path):
    rows = sorted(rows, key=lambda r: r["case"])
    ok = _ok(rows)
    with out.open("w") as f:
        f.write("# 30 deg DoE summary\n\n")
        f.write(f"Cases analysed: **{len(ok)}** (out of {len(rows)} stamped). "
                "Time-averaging window = 0.6–1.2 s. CoV is mass-flux weighted "
                "and computed on the time-averaged H$_2$ field (preferred). "
                "$\\Delta p$ is the clean function-object area-weighted "
                "$p_{rgh}$ time-series, in kPa.\n\n")
        f.write("| case | d/D | HBR | VR | CoV_mass | CoV_area | I_s_mass | "
                "$|\\Delta p|$ kPa | $\\langle Y_{H_2}\\rangle_{out}$ |\n")
        f.write("|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for r in rows:
            if r["status"] != "ok":
                f.write(f"| {r['case']:02d} | {r['d_over_D']:.4f} | {r['HBR']:.4f} | "
                        f"{r['VR']:.3f} | _{r['status']}_ | | | | |\n")
                continue
            f.write(
                f"| {r['case']:02d} "
                f"| {r['d_over_D']:.4f} | {r['HBR']:.4f} | {r['VR']:.3f} "
                f"| {r['CoV_mass_tavg']:.4f} | {r['CoV_area_tavg']:.4f} "
                f"| {r['Is_mass_tavg']:.4f} | {abs(r['dP_prgh_area_ts_kPa']):.3f} "
                f"| {r['H2_outletAvg_ts']:.4f} |\n"
            )
        # Best / worst
        if ok:
            best = min(ok, key=lambda r: r["CoV_mass_tavg"])
            worst = max(ok, key=lambda r: r["CoV_mass_tavg"])
            f.write(f"\n**Best mixing (lowest CoV_mass)** : case_{best['case']:02d} "
                    f"@ d/D = {best['d_over_D']:.3f}, VR = {best['VR']:.2f}, "
                    f"HBR = {best['HBR']:.3f} -> CoV = {best['CoV_mass_tavg']:.4f}\n")
            f.write(f"\n**Worst mixing (highest CoV_mass)** : case_{worst['case']:02d} "
                    f"@ d/D = {worst['d_over_D']:.3f}, VR = {worst['VR']:.2f}, "
                    f"HBR = {worst['HBR']:.3f} -> CoV = {worst['CoV_mass_tavg']:.4f}\n")
            cheap = min(ok, key=lambda r: abs(r["dP_prgh_area_ts_kPa"]))
            costly = max(ok, key=lambda r: abs(r["dP_prgh_area_ts_kPa"]))
            f.write(f"\n**Cheapest (lowest $|\\Delta p|$)** : case_{cheap['case']:02d} "
                    f"-> {abs(cheap['dP_prgh_area_ts_kPa']):.3f} kPa\n")
            f.write(f"\n**Costliest (highest $|\\Delta p|$)** : case_{costly['case']:02d} "
                    f"-> {abs(costly['dP_prgh_area_ts_kPa']):.3f} kPa\n")
    print(f"  wrote {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--cases",  required=True, type=Path)
    ap.add_argument("--out",    required=True, type=Path)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    rows = aggregate(args.design, args.cases)

    print("Writing CSV + MD ...")
    write_csv(rows, args.out / "doe_summary_30deg.csv")
    write_md(rows,  args.out / "DOE_SUMMARY_30DEG.md")

    print("Plotting scatter pack ...")
    scatter_xy(rows, "d_over_D", "CoV_mass_tavg", "HBR",
               xlabel="d/D", ylabel="CoV (mass-flux, time-avg H$_2$)",
               clabel="HBR", title="30 deg: CoV vs. d/D",
               out=args.out / "fig_scatter_CoV_mass_vs_dD.png")
    scatter_xy(rows, "VR", "CoV_mass_tavg", "HBR",
               xlabel="VR", ylabel="CoV (mass-flux, time-avg H$_2$)",
               clabel="HBR", title="30 deg: CoV vs. VR",
               out=args.out / "fig_scatter_CoV_mass_vs_VR.png")
    scatter_xy(rows, "HBR", "CoV_mass_tavg", "d_over_D",
               xlabel="HBR (H$_2$ mass blend ratio)",
               ylabel="CoV (mass-flux, time-avg H$_2$)",
               clabel="d/D", title="30 deg: CoV vs. HBR",
               out=args.out / "fig_scatter_CoV_mass_vs_HBR.png")
    # |dP|
    for r in _ok(rows):
        r["abs_dP"] = abs(r["dP_prgh_area_ts_kPa"])
    scatter_xy(rows, "HBR", "abs_dP", "d_over_D",
               xlabel="HBR", ylabel=r"$|\Delta p|$ (kPa, time-series)",
               clabel="d/D", title="30 deg: $|\\Delta p|$ vs. HBR",
               out=args.out / "fig_scatter_dP_vs_HBR.png")
    scatter_xy(rows, "VR", "abs_dP", "HBR",
               xlabel="VR", ylabel=r"$|\Delta p|$ (kPa, time-series)",
               clabel="HBR", title="30 deg: $|\\Delta p|$ vs. VR",
               out=args.out / "fig_scatter_dP_vs_VR.png")

    print("Heatmaps (interpolated on log-VR) ...")
    heatmap_dD_VR(rows, "CoV_mass_tavg",
                  title="30 deg: CoV (mass-flux, time-avg H$_2$)",
                  zlabel="CoV", out=args.out / "fig_CoV_heatmap_dD_VR.png")
    heatmap_dD_VR(rows, "abs_dP",
                  title=r"30 deg: $|\Delta p|$ (kPa)",
                  zlabel=r"$|\Delta p|$ (kPa)",
                  out=args.out / "fig_dP_heatmap_dD_VR.png")

    print("Pareto plot ...")
    pareto_dP_vs_CoV(rows, out=args.out / "fig_pareto_dP_vs_CoV.png")
    print("done.")


if __name__ == "__main__":
    main()
