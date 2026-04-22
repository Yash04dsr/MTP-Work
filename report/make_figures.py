#!/usr/bin/env python3
"""Generate all figures for the mesh-independence chapter."""
import os, math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE   = Path(__file__).resolve().parent
DATA   = HERE / "data"
FIGDIR = HERE / "figures"
FIGDIR.mkdir(exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 130,
    "savefig.dpi": 180,
    "font.family": "DejaVu Sans",
    "font.size": 10.5,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "legend.fontsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

BLUE   = "#1f77b4"
ORANGE = "#d95f02"
GREEN  = "#2ca02c"
GREY   = "#666666"


def read_series(path):
    t, v = [], []
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            parts = ln.split()
            try:
                t.append(float(parts[0]))
                v.append(float(parts[-1]))
            except (ValueError, IndexError):
                pass
    return np.array(t), np.array(v)


def read_residuals(path):
    with open(path) as f:
        header = None
        for ln in f:
            if ln.startswith("# Time"):
                header = ln.lstrip("# ").split()
                break
    rows = np.genfromtxt(path, comments="#", dtype=str)
    t = rows[:, 0].astype(float)
    col = {h: i for i, h in enumerate(header)}
    return t, rows, col


FAST_H2_t,  FAST_H2_v  = read_series(DATA / "fast"   / "H2_outletAvg.dat")
MED_H2_t,   MED_H2_v   = read_series(DATA / "medium" / "H2_outletAvg.dat")
FAST_PIN_t, FAST_PIN_v = read_series(DATA / "fast"   / "p_rgh_inlet.dat")
MED_PIN_t,  MED_PIN_v  = read_series(DATA / "medium" / "p_rgh_inlet.dat")
FAST_POUT_t,FAST_POUT_v= read_series(DATA / "fast"   / "p_rgh_outlet.dat")
MED_POUT_t, MED_POUT_v = read_series(DATA / "medium" / "p_rgh_outlet.dat")

Y_H2_EXPECTED = (
    (6.9e6 * 2.016e-3 / (8.314 * 288)) * 32.0 * math.pi * 0.0575 ** 2
) / (
    (6.9e6 * 2.016e-3 / (8.314 * 288)) * 32.0 * math.pi * 0.0575 ** 2
    + (6.9e6 * 16.043e-3 / (8.314 * 288)) * 10.0 * math.pi * 0.23 ** 2
)


# ------------------------------------------------------------------
# Figure 1 – Mesh comparison
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.0, 4.1))

cases  = ["Coarse\n(380 k)", "Medium\n(953 k)"]
cells  = [380_193, 952_900]
labels = [f"{c/1000:.0f} k" for c in cells]
bars = ax.bar(cases, cells, color=[BLUE, ORANGE], width=0.55, edgecolor="black")

for bar, label in zip(bars, labels):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.02,
            label, ha="center", va="bottom", fontsize=11, fontweight="bold")

ax.set_ylabel("Cell count")
ax.set_title("Mesh refinement levels (Fig. 1)")
ax.set_ylim(0, 1_150_000)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1e3:.0f} k"))
extra = [
    "wall surface: L1",
    "junction:     L1",
    "layers: 3",
]
extra_m = [
    "wall surface: L1",
    "junction:     L2",
    "layers: 3",
]
ax.text(0, 420_000, "\n".join(extra),   ha="center", va="top", fontsize=9, color="white",
        bbox=dict(boxstyle="round,pad=0.3", fc=BLUE, ec="none"))
ax.text(1, 1_000_000, "\n".join(extra_m), ha="center", va="top", fontsize=9, color="white",
        bbox=dict(boxstyle="round,pad=0.3", fc=ORANGE, ec="none"))
ax.text(0.5, -0.22, "Refinement ratio (cells): ×2.5   |   linear in junction: ×2",
        transform=ax.transAxes, ha="center", fontsize=9, color=GREY, style="italic")

plt.tight_layout()
plt.savefig(FIGDIR / "fig1_mesh_comparison.png", bbox_inches="tight")
plt.close()


# ------------------------------------------------------------------
# Figure 2 – H2 at outlet time history
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 4.4))
ax.plot(FAST_H2_t, FAST_H2_v * 100, color=BLUE,   lw=1.4, label="Coarse (380 k)")
ax.plot(MED_H2_t,  MED_H2_v  * 100, color=ORANGE, lw=1.4, label="Medium (953 k)")
ax.axhline(Y_H2_EXPECTED * 100, color=GREEN, lw=1.4, ls="--",
           label=f"Mass-balance steady ({Y_H2_EXPECTED*100:.2f} %)")
ax.axvspan(0.8, 1.5, color=GREY, alpha=0.08, label="Statistically stationary window")
ax.set_xlabel("Physical time [s]")
ax.set_ylabel(r"$\langle Y_{\mathrm{H_2}} \rangle$ at outlet [%]")
ax.set_title("H$_2$ outlet area-average — transient to quasi-steady (Fig. 2)")
ax.set_xlim(0, 1.55)
ax.legend(loc="upper left", frameon=True)
# annotate flow-through
t_ft = 9.4 / 10.0
ax.axvline(t_ft, color=GREY, lw=0.8, ls=":")
ax.text(t_ft + 0.01, 0.3, "1 flow-through", rotation=90, color=GREY, fontsize=8)
plt.tight_layout()
plt.savefig(FIGDIR / "fig2_H2_timehistory.png", bbox_inches="tight")
plt.close()


# ------------------------------------------------------------------
# Figure 3 – Inlet pressure and ΔP time history (acoustic noise)
# ------------------------------------------------------------------
fig, axes = plt.subplots(2, 1, figsize=(8.5, 6.2), sharex=True)

ax = axes[0]
ax.plot(FAST_PIN_t, FAST_PIN_v / 1e6, color=BLUE,   lw=1.1, label="Coarse inlet")
ax.plot(MED_PIN_t,  MED_PIN_v  / 1e6, color=ORANGE, lw=1.1, label="Medium inlet")
ax.axhline(6.9, color=GREEN, lw=1.4, ls="--", label="Outlet BC (6.90 MPa)")
ax.axvspan(0.8, 1.5, color=GREY, alpha=0.08)
ax.set_ylabel(r"$\bar p_{\rm rgh}$ [MPa]")
ax.set_title("Inlet pressure time history (Fig. 3a)")
ax.legend(loc="lower left", ncol=3, fontsize=9)
ax.set_ylim(6.60, 7.10)

ax = axes[1]
dP_fast = np.interp(FAST_PIN_t, FAST_POUT_t, FAST_POUT_v)
dP_fast = (FAST_PIN_v - dP_fast) / 1e3
dP_med  = np.interp(MED_PIN_t,  MED_POUT_t, MED_POUT_v)
dP_med  = (MED_PIN_v  - dP_med)  / 1e3
ax.plot(FAST_PIN_t, dP_fast, color=BLUE,   lw=1.0, label="Coarse")
ax.plot(MED_PIN_t,  dP_med,  color=ORANGE, lw=1.0, label="Medium")
ax.axhline(0, color="black", lw=0.7)
ax.axvspan(0.8, 1.5, color=GREY, alpha=0.08)
ax.set_xlabel("Physical time [s]")
ax.set_ylabel(r"$\Delta p$ [kPa]")
ax.set_title("Inlet-to-outlet pressure difference — acoustic oscillations (Fig. 3b)")
ax.legend(loc="upper right")
ax.set_xlim(0, 1.55)
ax.set_ylim(-300, 300)
plt.tight_layout()
plt.savefig(FIGDIR / "fig3_pressure_timehistory.png", bbox_inches="tight")
plt.close()


# ------------------------------------------------------------------
# Figure 4 – Solver residual convergence (medium case)
# ------------------------------------------------------------------
t_res, rows, col = read_residuals(DATA / "medium" / "residuals.dat")

def safe(name):
    return rows[:, col[name]].astype(float)

fields = [
    ("Ux_initial",    "U$_x$",       BLUE),
    ("p_rgh_initial", "p$_{rgh}$",   ORANGE),
    ("k_initial",     "k",           GREEN),
    ("omega_initial", "ω",           "#9467bd"),
    ("H2_initial",    "Y$_{H_2}$",   "#8c564b"),
]

fig, ax = plt.subplots(figsize=(8.4, 4.6))
for key, lbl, c in fields:
    v = safe(key)
    v = np.clip(v, 1e-16, None)
    ax.semilogy(t_res, v, color=c, lw=0.9, alpha=0.85, label=lbl)

ax.set_xlabel("Physical time [s]")
ax.set_ylabel("Initial residual")
ax.set_title("Solver residuals (medium mesh) — stable bounded convergence (Fig. 4)")
ax.legend(ncol=5, loc="upper right", frameon=True)
ax.set_xlim(0, 1.2)
ax.set_ylim(1e-10, 2)
plt.tight_layout()
plt.savefig(FIGDIR / "fig4_residuals.png", bbox_inches="tight")
plt.close()


# ------------------------------------------------------------------
# Figure 5 – Summary comparison bar chart (CoV, mean H2, ΔP)
# ------------------------------------------------------------------
labels  = ["Coarse (380 k)", "Medium (953 k)"]
COV     = [0.1409, 0.1981]
H2mean  = [0.03219, 0.02650]
dP_kPa  = [10.025,  -9.865]

fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.2))
colors  = [BLUE, ORANGE]

ax = axes[0]
bars = ax.bar(labels, COV, color=colors, edgecolor="black", width=0.55)
for b, v in zip(bars, COV):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.008, f"{v:.3f}",
            ha="center", va="bottom", fontsize=10)
ax.set_title("Mixing CoV\n(on time-averaged field)")
ax.set_ylabel("CoV = σ / μ")
ax.set_ylim(0, 0.26)

ax = axes[1]
bars = ax.bar(labels, [x * 100 for x in H2mean], color=colors, edgecolor="black", width=0.55)
for b, v in zip(bars, H2mean):
    ax.text(b.get_x() + b.get_width() / 2, v * 100 + 0.07, f"{v*100:.2f} %",
            ha="center", va="bottom", fontsize=10)
ax.axhline(Y_H2_EXPECTED * 100, color=GREEN, lw=1.4, ls="--",
           label=f"Mass balance ({Y_H2_EXPECTED*100:.2f} %)")
ax.set_title(r"Outlet $\langle Y_{H_2}\rangle$ time-averaged")
ax.set_ylabel(r"$\langle Y_{H_2}\rangle$ at outlet [%]")
ax.set_ylim(0, 4.2)
ax.legend(loc="lower right", fontsize=9)

ax = axes[2]
bars = ax.bar(labels, dP_kPa, color=colors, edgecolor="black", width=0.55)
for b, v in zip(bars, dP_kPa):
    off = 0.8 if v >= 0 else -2.6
    ax.text(b.get_x() + b.get_width() / 2, v + off, f"{v:+.1f} kPa",
            ha="center", va="bottom" if v >= 0 else "top", fontsize=10)
ax.axhline(0, color="black", lw=0.8)
ax.set_title(r"Mean $\Delta p$ (inlet − outlet)" "\n±σ acoustic: ~70 kPa")
ax.set_ylabel(r"$\Delta p$ [kPa]")
ax.set_ylim(-30, 30)

plt.suptitle("Mesh-independence — time-averaged metrics (Fig. 5)", y=1.03)
plt.tight_layout()
plt.savefig(FIGDIR / "fig5_summary_bars.png", bbox_inches="tight")
plt.close()


# ------------------------------------------------------------------
# Figure 6 – Mass-balance deviation convergence
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.0, 4.2))
dev_pct = [(H2mean[0] - Y_H2_EXPECTED) / Y_H2_EXPECTED * 100,
           (H2mean[1] - Y_H2_EXPECTED) / Y_H2_EXPECTED * 100]
bars = ax.bar(labels, dev_pct, color=colors, edgecolor="black", width=0.55)
for b, v in zip(bars, dev_pct):
    ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"+{v:.1f} %",
            ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.axhline(0, color=GREEN, lw=1.4, ls="--",
           label="Mass-balance exact (0 %)")
ax.set_ylabel(r"Deviation of $\langle Y_{H_2}\rangle$ from mass balance [%]")
ax.set_title("Convergence of bulk-transport invariant (Fig. 6)")
ax.set_ylim(0, 38)
ax.legend(loc="upper right")
plt.tight_layout()
plt.savefig(FIGDIR / "fig6_mass_balance.png", bbox_inches="tight")
plt.close()

print("All figures written to", FIGDIR)
for p in sorted(FIGDIR.glob("*.png")):
    print(" ", p.name, f"{p.stat().st_size/1024:.0f} KB")
