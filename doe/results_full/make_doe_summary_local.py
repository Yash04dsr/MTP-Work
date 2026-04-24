#!/usr/bin/env python3
"""Build a DoE-wide summary from the 10 case CSVs + case_info.json files.

Generates:
  doe_summary_table.csv   one row per case with d/D, VR, HBR, CoV, dP
  doe_summary_CoV_dP.png  side-by-side bar charts
  doe_scatter_dD_VR.png   scatter of cases in design space, coloured by CoV
"""
import csv, json, math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
CASES = HERE / "cases"
OUT = HERE / "doe_summary"
OUT.mkdir(exist_ok=True)

rows = []
for c in sorted(CASES.iterdir()):
    if not c.is_dir() or not c.name.startswith("case_"):
        continue
    # case_info.json
    info_path = c / "case_info.json"
    stash_info = c / "_stash" / "case_info.json"
    info = {}
    for ipath in (info_path, stash_info):
        if ipath.exists():
            info = json.loads(ipath.read_text())
            break
    # all_metrics.csv (the AVG row)
    csv_path = c / "_stash" / "all_metrics.csv"
    if not csv_path.exists():
        csv_path = c / "all_metrics.csv"
    cov_area = None
    dp_p_rgh = None
    if csv_path.exists():
        with csv_path.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["time"] == "AVG":
                    try:
                        cov_area = float(row["H2_CoV_area"])
                    except (ValueError, KeyError):
                        cov_area = float("nan")
                    try:
                        dp_p_rgh = float(row["dP_p_rgh_area"])
                    except (ValueError, KeyError):
                        dp_p_rgh = float("nan")
                    break
    rows.append({
        "case": c.name,
        "d_over_D": info.get("d_over_D"),
        "VR":       info.get("VR"),
        "HBR":      info.get("HBR"),
        "CoV_area": cov_area,
        "dP_p_rgh_area_Pa": dp_p_rgh,
    })

# ---- write summary CSV ----
with (OUT / "doe_summary_table.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("wrote", OUT / "doe_summary_table.csv")

# Filter cases with actual CoV data for the plots
plot_rows = [r for r in rows
             if r["CoV_area"] is not None and not math.isnan(r["CoV_area"])]
cases_lbl = [r["case"].replace("case_", "") for r in plot_rows]
covs      = np.array([r["CoV_area"] for r in plot_rows])
dps_kpa   = np.array([r["dP_p_rgh_area_Pa"] / 1000.0
                      for r in plot_rows])

# ---- figure 1: CoV + dP bar charts ----
fig, ax = plt.subplots(1, 2, figsize=(12, 5))
bars = ax[0].bar(cases_lbl, covs, color="#2980b9")
ax[0].set_ylabel("Outlet CoV (H2, area-weighted)")
ax[0].set_xlabel("DoE case")
ax[0].set_title("Mixing quality (lower = better)")
ax[0].grid(axis="y", linestyle=":", alpha=0.5)
for bar, v in zip(bars, covs):
    ax[0].text(bar.get_x() + bar.get_width()/2, v + 0.01,
               f"{v:.2f}", ha="center", va="bottom", fontsize=9)

bars = ax[1].bar(cases_lbl, dps_kpa, color="#c0392b")
ax[1].set_ylabel(r"$\Delta P_{p\_rgh}$ (area-weighted) [kPa]")
ax[1].set_xlabel("DoE case")
ax[1].set_title("Pressure drop (snapshot-weighted)")
ax[1].grid(axis="y", linestyle=":", alpha=0.5)
ax[1].axhline(0, color="black", lw=0.5)

fig.suptitle("90° DoE — 10 cases (case_01 = IC-only, excluded from plots)",
             fontsize=12, y=1.02)
fig.tight_layout()
fig.savefig(OUT / "doe_summary_CoV_dP.png", dpi=150, bbox_inches="tight")
print("wrote", OUT / "doe_summary_CoV_dP.png")
plt.close(fig)

# ---- figure 2: design space scatter ----
dDs = np.array([r["d_over_D"] for r in plot_rows])
VRs = np.array([r["VR"]       for r in plot_rows])
fig, ax = plt.subplots(figsize=(8, 6))
sc = ax.scatter(dDs, VRs, c=covs, s=220, cmap="viridis_r",
                edgecolor="black", linewidth=1)
for dD, VR, lbl in zip(dDs, VRs, cases_lbl):
    ax.annotate(lbl, (dD, VR), xytext=(6, 6),
                textcoords="offset points", fontsize=9)
cbar = fig.colorbar(sc, ax=ax)
cbar.set_label("Outlet CoV (H2, area-weighted)")
ax.set_xlabel("d/D")
ax.set_ylabel("VR  (U_branch / U_main)")
ax.set_title("90° DoE design space — colour = mixing CoV (low = good)")
ax.grid(True, linestyle=":", alpha=0.5)
fig.tight_layout()
fig.savefig(OUT / "doe_scatter_dD_VR.png", dpi=150, bbox_inches="tight")
print("wrote", OUT / "doe_scatter_dD_VR.png")
plt.close(fig)

# ---- markdown summary ----
md = ["# 90° DoE — Full Campaign Summary", "", "| case | d/D | VR | HBR | CoV (outlet, area) | ΔP_p_rgh (snapshot) |",
      "|------|-----|----|-----|--------------------|---------------------|"]
for r in rows:
    cov_s = f"{r['CoV_area']:.4f}" if r['CoV_area'] is not None and not math.isnan(r['CoV_area']) else "IC-only"
    dp_s = f"{r['dP_p_rgh_area_Pa']:+.1f} Pa" if r['dP_p_rgh_area_Pa'] is not None and not math.isnan(r['dP_p_rgh_area_Pa']) else "—"
    md.append(f"| {r['case']} | {r['d_over_D']:.4f} | {r['VR']:.3f} | {r['HBR']:.3f} | {cov_s} | {dp_s} |")
md += ["", "Notes:", "- case_01 crashed at t≈0.946 s (FPE in yPlus wall function), only IC snapshot remained locally → no CoV/ΔP. Its postProcessing.tar.gz *does* retain plane-averaged H2 up to 0.946 s if needed.",
       "- CoV is outlet H2 mass-fraction, area-weighted, time-averaged over [0.8, 1.2] s.",
       "- ΔP is p_rgh inlet − outlet at snapshot t=1.2 s (raw CSV value). Sign convention differs from the 'clean' time-averaged ΔP printed in logs."]
(OUT / "DOE_SUMMARY.md").write_text("\n".join(md) + "\n")
print("wrote", OUT / "DOE_SUMMARY.md")
print("DONE")
