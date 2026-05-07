#!/usr/bin/env python3
"""
make_cross_campaign_figures.py
==============================
Generate publication-quality figures comparing all 4 campaigns
(90° top, 30° top, 90° bottom, 30° bottom) from cross_campaign_metrics.csv.

Usage:
    python3 make_cross_campaign_figures.py \
        --csv doe/cross_campaign_metrics.csv \
        --outdir doe/cross_campaign/figures
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Circle, Arc
import numpy as np

# ── Style ────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.labelsize": 13,
    "axes.titlesize": 14,
    "legend.fontsize": 10,
    "figure.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
})

STYLES = {
    "90_top": dict(color="#1f77b4", marker="o", label="90° top",    ms=7, zorder=4),
    "30_top": dict(color="#2ca02c", marker="^", label="30° top",    ms=8, zorder=5),
    "90_bot": dict(color="#d62728", marker="s", label="90° bottom", ms=7, zorder=3),
    "30_bot": dict(color="#ff7f0e", marker="D", label="30° bottom", ms=7, zorder=2),
}

CAMP_ORDER = ["90_top", "30_top", "90_bot", "30_bot"]


# ── Data loader ──────────────────────────────────────────────────────────
def load_data(csv_path: Path) -> list[dict]:
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("d_D", "VR", "HBR", "CoV", "dP_LP_kPa", "dP_LP_std_kPa"):
            try:
                r[k] = float(r[k])
            except (ValueError, KeyError):
                r[k] = None
        r["angle"] = int(r["angle"])
    return rows


def by_campaign(rows, camp):
    return [r for r in rows if r["campaign"] == camp]


# ── Fig 1: CoV vs VR power-law scatter ───────────────────────────────────
def fig1_cov_vs_vr(rows, outdir):
    fig, ax = plt.subplots(figsize=(8, 5.5))

    for camp in CAMP_ORDER:
        s = STYLES[camp]
        subset = [r for r in by_campaign(rows, camp) if r["CoV"] and r["VR"]]
        vr = np.array([r["VR"] for r in subset])
        cov = np.array([r["CoV"] for r in subset])
        ax.scatter(vr, cov, color=s["color"], marker=s["marker"],
                   s=s["ms"]**2, label=s["label"], zorder=s["zorder"],
                   edgecolors="white", linewidths=0.5)

        if len(vr) >= 4:
            mask = (vr > 0) & (cov > 0)
            if mask.sum() >= 3:
                log_vr, log_cov = np.log(vr[mask]), np.log(cov[mask])
                b, log_a = np.polyfit(log_vr, log_cov, 1)
                A = np.exp(log_a)
                ss_res = np.sum((log_cov - (b * log_vr + log_a)) ** 2)
                ss_tot = np.sum((log_cov - log_cov.mean()) ** 2)
                r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

                vr_fit = np.linspace(0.5, 6.5, 100)
                ax.plot(vr_fit, A * vr_fit**b, color=s["color"], ls="--",
                        lw=1.5, alpha=0.7)
                sign = "−" if b < 0 else ""
                ax.text(0.98, 0.02 + CAMP_ORDER.index(camp) * 0.065,
                        f'{s["label"]}: CoV = {A:.2f}·VR$^{{{b:.2f}}}$  '
                        f'(R² = {r2:.2f})',
                        transform=ax.transAxes, ha="right", va="bottom",
                        fontsize=9, color=s["color"])

    ax.axhline(0.05, color="gray", ls=":", lw=1.2, alpha=0.7)
    ax.text(0.55, 0.043, "Industrial target CoV ≤ 0.05",
            fontsize=8.5, color="gray", style="italic")

    ax.set_yscale("log")
    ax.set_xlabel("Velocity Ratio (VR)")
    ax.set_ylabel("CoV (area-weighted)")
    ax.set_title("Mixing Quality vs Velocity Ratio — All Campaigns")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.set_xlim(0.4, 6.5)
    ax.set_ylim(0.003, 2.0)
    ax.grid(True, which="both", ls=":", alpha=0.3)
    fig.savefig(outdir / "fig1_CoV_vs_VR.png")
    plt.close(fig)
    print(f"  [1/7] fig1_CoV_vs_VR.png")


# ── Fig 2: Matched-pair arrow plot (top vs bottom) ──────────────────────
def fig2_matched_pairs(rows, outdir):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), sharey=True)

    for idx, angle in enumerate([90, 30]):
        ax = axes[idx]
        top_camp = f"{angle}_top"
        bot_camp = f"{angle}_bot"
        top = {r["case"]: r for r in by_campaign(rows, top_camp)}
        bot = {r["case"]: r for r in by_campaign(rows, bot_camp)}
        common = sorted(set(top) & set(bot), key=int)

        x_pos = np.arange(len(common))
        changes = []

        for i, c in enumerate(common):
            ct = top[c]["CoV"]
            cb = bot[c]["CoV"]
            if ct is None or cb is None:
                continue
            color = "#2ca02c" if ct < cb else "#d62728"
            ax.plot([i, i], [ct, cb], color=color, lw=2, alpha=0.7)
            ax.plot(i, ct, "o", color=STYLES[top_camp]["color"], ms=8,
                    zorder=5, markeredgecolor="white", markeredgewidth=0.5)
            ax.plot(i, cb, "s", color=STYLES[bot_camp]["color"], ms=8,
                    zorder=5, markeredgecolor="white", markeredgewidth=0.5)

            if ct > 0:
                pct = (cb - ct) / ct * 100
                changes.append(pct)
                ax.annotate(f"{pct:+.0f}%", (i, max(ct, cb)),
                            textcoords="offset points", xytext=(0, 8),
                            ha="center", fontsize=7.5, color=color)

        ax.set_xticks(x_pos)
        ax.set_xticklabels([f"#{c}" for c in common], fontsize=9)
        ax.set_xlabel("Case ID")
        ax.set_title(f"{angle}° Injection: Top vs Bottom")
        ax.grid(True, axis="y", ls=":", alpha=0.3)

        if changes:
            med = np.median(changes)
            ax.text(0.02, 0.98, f"Median: {med:+.0f}%\n(bottom vs top)",
                    transform=ax.transAxes, va="top", fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="wheat", alpha=0.8))

    axes[0].set_ylabel("CoV (area-weighted)")

    top_patch = mpatches.Patch(color=STYLES["90_top"]["color"], label="Top injection")
    bot_patch = mpatches.Patch(color=STYLES["90_bot"]["color"], label="Bottom injection")
    axes[1].legend(handles=[top_patch, bot_patch], loc="upper right")

    fig.suptitle("Matched-Pair Comparison: Top vs Bottom Injection", fontsize=14, y=1.02)
    fig.tight_layout()
    fig.savefig(outdir / "fig2_matched_pairs_top_vs_bottom.png")
    plt.close(fig)
    print(f"  [2/7] fig2_matched_pairs_top_vs_bottom.png")


# ── Fig 3: Pareto front ─────────────────────────────────────────────────
def fig3_pareto(rows, outdir):
    fig, ax = plt.subplots(figsize=(8, 5.5))

    all_cov, all_dp = [], []
    for camp in CAMP_ORDER:
        s = STYLES[camp]
        subset = [r for r in by_campaign(rows, camp)
                  if r["CoV"] is not None and r["dP_LP_kPa"] is not None]
        dp = np.array([abs(r["dP_LP_kPa"]) for r in subset])
        cov = np.array([r["CoV"] for r in subset])
        ax.scatter(dp, cov, color=s["color"], marker=s["marker"],
                   s=s["ms"]**2, label=s["label"], zorder=s["zorder"],
                   edgecolors="white", linewidths=0.5)
        all_cov.extend(cov)
        all_dp.extend(dp)

        for r in subset:
            ax.annotate(f'{r["case"]}', (abs(r["dP_LP_kPa"]), r["CoV"]),
                        textcoords="offset points", xytext=(4, 4),
                        fontsize=6.5, color=s["color"], alpha=0.8)

    ax.axhline(0.05, color="gray", ls=":", lw=1.2, alpha=0.6)
    ax.text(6, 0.04, "CoV = 0.05", fontsize=8, color="gray", style="italic")

    ax.set_xlabel("|ΔP$_{rgh}$| (kPa, LP-filtered)")
    ax.set_ylabel("CoV (area-weighted)")
    ax.set_title("Pareto Front: Mixing vs Pressure Drop")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.set_xlim(-0.5, 10)
    ax.set_ylim(-0.02, 1.5)
    ax.grid(True, ls=":", alpha=0.3)
    fig.savefig(outdir / "fig3_pareto.png")
    plt.close(fig)
    print(f"  [3/7] fig3_pareto.png")


# ── Fig 4: CoV heatmap 2×2 ──────────────────────────────────────────────
def fig4_heatmap(rows, outdir):
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    layout = [
        ("90_top", "90° Top"),    ("30_top", "30° Top"),
        ("90_bot", "90° Bottom"), ("30_bot", "30° Bottom"),
    ]

    from matplotlib.colors import LogNorm
    vmin, vmax = 0.005, 1.5
    norm = LogNorm(vmin=vmin, vmax=vmax)

    for idx, (camp, title) in enumerate(layout):
        ax = axes[idx // 2][idx % 2]
        subset = [r for r in by_campaign(rows, camp) if r["CoV"] and r["d_D"] and r["VR"]]

        dd_vals = sorted(set(round(r["d_D"], 3) for r in subset))
        vr_vals = sorted(set(round(r["VR"], 2) for r in subset))

        if not dd_vals or not vr_vals:
            ax.set_title(title)
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes)
            continue

        grid = np.full((len(vr_vals), len(dd_vals)), np.nan)
        labels = [[""]*len(dd_vals) for _ in range(len(vr_vals))]

        for r in subset:
            dd_idx = dd_vals.index(round(r["d_D"], 3))
            vr_idx = vr_vals.index(round(r["VR"], 2))
            grid[vr_idx, dd_idx] = r["CoV"]
            labels[vr_idx][dd_idx] = f'#{r["case"]}\n{r["CoV"]:.3f}'

        im = ax.imshow(grid, aspect="auto", origin="lower", norm=norm,
                       cmap="RdYlGn_r",
                       extent=[-0.5, len(dd_vals)-0.5, -0.5, len(vr_vals)-0.5])

        for yi in range(len(vr_vals)):
            for xi in range(len(dd_vals)):
                if labels[yi][xi]:
                    val = grid[yi, xi]
                    tc = "white" if val > 0.5 else "black"
                    ax.text(xi, yi, labels[yi][xi], ha="center", va="center",
                            fontsize=7, color=tc, fontweight="bold")

        ax.set_xticks(range(len(dd_vals)))
        ax.set_xticklabels([f"{v:.3f}" for v in dd_vals], fontsize=8)
        ax.set_yticks(range(len(vr_vals)))
        ax.set_yticklabels([f"{v:.2f}" for v in vr_vals], fontsize=8)
        ax.set_xlabel("d/D")
        ax.set_ylabel("VR")
        ax.set_title(title, fontweight="bold")

    fig.suptitle("Design-Space Heatmap of CoV", fontsize=15, y=1.01)
    cbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap="RdYlGn_r"),
                        ax=axes, shrink=0.6, pad=0.02, label="CoV (log scale)")
    fig.tight_layout()
    fig.savefig(outdir / "fig4_heatmap_CoV.png")
    plt.close(fig)
    print(f"  [4/7] fig4_heatmap_CoV.png")


# ── Fig 5: Bar chart — median CoV ───────────────────────────────────────
def fig5_bar_chart(rows, outdir):
    fig, ax = plt.subplots(figsize=(7, 5))

    medians, mins, maxs = [], [], []
    labels_list, colors = [], []

    for camp in CAMP_ORDER:
        s = STYLES[camp]
        covs = [r["CoV"] for r in by_campaign(rows, camp) if r["CoV"] is not None]
        if not covs:
            continue
        medians.append(np.median(covs))
        mins.append(min(covs))
        maxs.append(max(covs))
        labels_list.append(s["label"])
        colors.append(s["color"])

    x = np.arange(len(medians))
    err_lo = [medians[i] - mins[i] for i in range(len(medians))]
    err_hi = [maxs[i] - medians[i] for i in range(len(medians))]

    bars = ax.bar(x, medians, color=colors, edgecolor="white", linewidth=1.2,
                  width=0.6, zorder=3)
    ax.errorbar(x, medians, yerr=[err_lo, err_hi], fmt="none",
                ecolor="black", capsize=6, capthick=1.5, lw=1.5, zorder=4)

    for i, (m, lo, hi) in enumerate(zip(medians, mins, maxs)):
        ax.text(i, m + err_hi[i] + 0.03, f"med={m:.3f}",
                ha="center", fontsize=9, fontweight="bold")

    ax.axhline(0.05, color="gray", ls=":", lw=1.5, alpha=0.7)
    ax.text(len(medians) - 0.5, 0.06, "CoV = 0.05 target",
            fontsize=8.5, color="gray", style="italic", ha="right")

    ax.set_xticks(x)
    ax.set_xticklabels(labels_list, fontsize=11)
    ax.set_ylabel("CoV (area-weighted)")
    ax.set_title("Median Outlet Mixing Quality by Campaign")
    ax.set_ylim(0, max(maxs) * 1.2)
    ax.grid(True, axis="y", ls=":", alpha=0.3)
    fig.savefig(outdir / "fig5_bar_median_CoV.png")
    plt.close(fig)
    print(f"  [5/7] fig5_bar_median_CoV.png")


# ── Fig 6: Physical mechanism schematic ──────────────────────────────────
def fig6_mechanism(rows, outdir):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    for idx, (ax, title, inject_y, plume_style) in enumerate([
        (axes[0], "Top Injection (y = +R)", 1, "spread"),
        (axes[1], "Bottom Injection (y = −R)", -1, "column"),
    ]):
        ax.set_xlim(-0.5, 8)
        ax.set_ylim(-2, 2)
        ax.set_aspect("equal")
        ax.axis("off")

        pipe_y_top = 1.0
        pipe_y_bot = -1.0
        ax.plot([0, 7.5], [pipe_y_top, pipe_y_top], "k-", lw=2.5)
        ax.plot([0, 7.5], [pipe_y_bot, pipe_y_bot], "k-", lw=2.5)

        jct_z = 2.0
        branch_len = 1.2
        bx_lo = jct_z - 0.15
        bx_hi = jct_z + 0.15
        by_base = inject_y * pipe_y_top
        by_tip = by_base + inject_y * branch_len
        ax.plot([bx_lo, bx_lo], [by_base, by_tip], "k-", lw=2)
        ax.plot([bx_hi, bx_hi], [by_base, by_tip], "k-", lw=2)
        ax.plot([bx_lo, bx_hi], [by_tip, by_tip], "k-", lw=2)

        ax.annotate("", xy=(jct_z, by_base - inject_y * 0.1),
                    xytext=(jct_z, by_tip - inject_y * 0.2),
                    arrowprops=dict(arrowstyle="->,head_width=0.15",
                                   color="dodgerblue", lw=2))
        ax.text(jct_z + 0.3, (by_base + by_tip) / 2, "H₂",
                fontsize=11, color="dodgerblue", fontweight="bold")

        ax.annotate("", xy=(0.8, 0), xytext=(0, 0),
                    arrowprops=dict(arrowstyle="->,head_width=0.12",
                                   color="gray", lw=1.8))
        ax.text(0.1, 0.15, "CH₄ main\nflow →", fontsize=8, color="gray")

        ax.annotate("", xy=(3.5, -1.7), xytext=(3.5, -1.2),
                    arrowprops=dict(arrowstyle="->,head_width=0.1",
                                   color="black", lw=1.5))
        ax.text(3.7, -1.5, "g", fontsize=11, fontstyle="italic")

        if plume_style == "spread":
            from matplotlib.patches import Ellipse
            for dz, w, h, alpha_v in [(0.5, 0.6, 1.2, 0.35),
                                       (1.5, 1.2, 1.6, 0.25),
                                       (3.0, 1.8, 1.8, 0.15),
                                       (4.5, 2.0, 1.9, 0.10)]:
                e = Ellipse((jct_z + dz, inject_y * 0.3), w, h,
                            fc="dodgerblue", alpha=alpha_v, ec="none")
                ax.add_patch(e)
            ax.text(5.5, 0.6, "Thin layer\nat crown;\nspreads laterally",
                    fontsize=8.5, color="dodgerblue", ha="center",
                    bbox=dict(fc="white", alpha=0.8, ec="none", pad=2))
            ax.annotate("Buoyancy\ntraps plume", xy=(4, 0.85),
                        xytext=(5.5, 1.5),
                        arrowprops=dict(arrowstyle="->", color="red", lw=1.2),
                        fontsize=8, color="red", ha="center")
        else:
            from matplotlib.patches import Ellipse
            for dz, w, h, yc, alpha_v in [
                (0.3, 0.4, 0.6, -0.7, 0.4),
                (1.0, 0.5, 0.5, -0.4, 0.3),
                (2.0, 0.5, 0.5, -0.1, 0.25),
                (3.0, 0.5, 0.4,  0.2, 0.2),
                (4.5, 0.5, 0.4,  0.4, 0.15),
            ]:
                e = Ellipse((jct_z + dz, yc), w, h,
                            fc="dodgerblue", alpha=alpha_v, ec="none")
                ax.add_patch(e)
            ax.annotate("Buoyancy\nlifts column", xy=(3.5, 0.1),
                        xytext=(5.5, 1.3),
                        arrowprops=dict(arrowstyle="->", color="red", lw=1.2),
                        fontsize=8, color="red", ha="center")
            ax.text(5.5, -0.5, "Coherent column;\nrises without\nspreading",
                    fontsize=8.5, color="dodgerblue", ha="center",
                    bbox=dict(fc="white", alpha=0.8, ec="none", pad=2))

        ax.set_title(title, fontsize=13, fontweight="bold", pad=10)

    fig.suptitle("Physical Mechanism: Why Top Injection Mixes Better",
                 fontsize=14, y=1.02)
    fig.tight_layout()
    fig.savefig(outdir / "fig6_mechanism_schematic.png")
    plt.close(fig)
    print(f"  [6/7] fig6_mechanism_schematic.png")


# ── Fig 7: CoV vs d/D at low VR ─────────────────────────────────────────
def fig7_cov_vs_dD(rows, outdir):
    fig, ax = plt.subplots(figsize=(8, 5.5))

    for camp in CAMP_ORDER:
        s = STYLES[camp]
        subset = [r for r in by_campaign(rows, camp)
                  if r["CoV"] and r["d_D"] and r["VR"]
                  and 0.6 <= r["VR"] <= 1.5]
        if len(subset) < 2:
            continue
        subset.sort(key=lambda r: r["d_D"])
        dd = [r["d_D"] for r in subset]
        cov = [r["CoV"] for r in subset]
        ax.plot(dd, cov, color=s["color"], marker=s["marker"],
                ms=s["ms"], label=f'{s["label"]} (VR ∈ [0.6, 1.5])',
                lw=1.5, alpha=0.85, markeredgecolor="white", markeredgewidth=0.5)
        for r in subset:
            ax.annotate(f'VR={r["VR"]:.1f}', (r["d_D"], r["CoV"]),
                        textcoords="offset points", xytext=(5, 5),
                        fontsize=6.5, color=s["color"], alpha=0.7)

    ax.set_xlabel("Diameter Ratio (d/D)")
    ax.set_ylabel("CoV (area-weighted)")
    ax.set_title("Effect of d/D on Mixing at Low VR (0.6 – 1.5)")
    ax.legend(loc="best", framealpha=0.9)
    ax.grid(True, ls=":", alpha=0.3)
    fig.savefig(outdir / "fig7_CoV_vs_dD.png")
    plt.close(fig)
    print(f"  [7/7] fig7_CoV_vs_dD.png")


# ── Main ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="cross_campaign_metrics.csv")
    parser.add_argument("--outdir", required=True, help="output directory")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = load_data(csv_path)
    print(f"Loaded {len(rows)} rows from {csv_path}")
    print(f"Campaigns: {sorted(set(r['campaign'] for r in rows))}")
    print()

    fig1_cov_vs_vr(rows, outdir)
    fig2_matched_pairs(rows, outdir)
    fig3_pareto(rows, outdir)
    fig4_heatmap(rows, outdir)
    fig5_bar_chart(rows, outdir)
    fig6_mechanism(rows, outdir)
    fig7_cov_vs_dD(rows, outdir)

    print(f"\nAll figures saved to {outdir}/")


if __name__ == "__main__":
    main()
