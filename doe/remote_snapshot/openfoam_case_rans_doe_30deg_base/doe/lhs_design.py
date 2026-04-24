#!/usr/bin/env python3
"""lhs_design.py  --  LHS sampler for the 90-deg T-junction DoE.

Design variables
----------------
  d/D      diameter ratio (branch / main)          primary DoE variable
  VR       velocity ratio (U_branch / U_main)      primary DoE variable

Derived constraint (Hydrogen Blend Ratio, volumetric)

    HBR = Q_branch / (Q_main + Q_branch)
        = (d/D)^2 * VR / (1 + (d/D)^2 * VR)

We require HBR in [0.05, 0.20] (5 - 20 % H2 blend, industry standard).

Sampling strategy -- *sliced LHS* for mesh reuse
------------------------------------------------
The mesh regeneration step (blockMesh + snappyHexMesh + decomposePar)
costs ~45 min per unique d/D.  By choosing only 5 unique d/D values and
running 2 VR cases per d/D, the mesh is built 5x instead of 10x --> ~3.75 h
saved across the 10-case DoE.

Algorithm :
  1. Draw 5 LHS samples on d/D in [d_min, d_max].
  2. For each d/D, draw 2 LHS samples on HBR in [HBR_min, HBR_max] (an
     inner LHS slice).  This is the Ye-Li-Sudjianto (2000) sliced-LHS
     construction -- it gives space-filling projections on BOTH axes of
     the full 10-point design while preserving the mesh-reuse structure.
  3. Derive VR from HBR :     VR = HBR / ((1 - HBR) * (d/D)^2)
  4. Check VR is physically reasonable (bounded above to avoid choked
     branch flow at small d/D).  Clip if needed with a warning.

Output : doe_design.csv with columns
    case, d_over_D, HBR, VR, D2_m, U_main_mps, U_branch_mps, Re_branch,
    K_main, K_branch, Omega_main, Omega_branch, mix_branch_m, ZJCT, LMAIN

Usage :
    python3 lhs_design.py [--seed 42] [--outdir ./]
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from pathlib import Path

import numpy as np


# ---- Physical / numerical constants ----------------------------------

D1 = 0.460          # main pipe diameter [m] (fixed for the DoE)
U_MAIN = 10.0       # main pipe bulk velocity [m/s] (fixed)
Z_JCT = 2.300       # junction z-coordinate [m] (post-R2)
L_MAIN = 6.900      # main pipe length [m] (post-R2)

# Kinematic viscosity of CH4 at 288 K, ~69 bar (medium-case baseline).
# Used only for informational Re_branch -- not for the BC itself.
NU_CH4 = 1.75e-7    # m^2/s

# Turbulence BC helpers (matches 0/k and 0/omega templates).
TI        = 0.05                 # inlet turbulence intensity
C_MU_25   = 0.09 ** 0.25         # 0.5477
L_MIX_FAC = 0.07                 # mixing length = 0.07 * D


# ---- Design-variable bounds ------------------------------------------

# d/D range : spans the industrially relevant gas-blending tees, from
# small-branch injection (d/D = 0.15) to large-branch (d/D = 0.45).
# Below 0.10 the jet is too weak to penetrate; above 0.5 the geometry
# stops looking like a tee (it's a junction).
D_RATIO_MIN = 0.15
D_RATIO_MAX = 0.45

# HBR range : 5 - 20 % volumetric H2 blend, standard research band
# (EC H2-readiness studies; ENTSOG 2021; Mahajan et al. 2022).
HBR_MIN = 0.05
HBR_MAX = 0.20

# VR safety cap : above this the branch inlet is effectively choked and
# the jet physics deviates from the T-junction mixing literature.  If a
# draw demands VR > VR_CAP the sample is re-drawn.
VR_CAP = 12.0


# ---- LHS core --------------------------------------------------------

def lhs_1d(n: int, rng: np.random.Generator) -> np.ndarray:
    """n-point 1-D Latin hypercube sample on [0, 1]."""
    u = rng.uniform(size=n)
    perm = rng.permutation(n)
    return (perm + u) / n


def sliced_lhs(n_slices: int, pts_per_slice: int,
               rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Two-axis sliced LHS (Ye, Li & Sudjianto 2000)."""
    d_bins = lhs_1d(n_slices, rng)
    d_bins.sort()                             # ordered d/D slices
    hbrs = np.empty((n_slices, pts_per_slice))
    for k in range(n_slices):
        hbrs[k, :] = lhs_1d(pts_per_slice, rng)
    return d_bins, hbrs


# ---- Derived quantities ----------------------------------------------

def vr_from_hbr(hbr: float, d_ratio: float) -> float:
    """VR = HBR / ((1 - HBR) * (d/D)^2)."""
    return hbr / ((1.0 - hbr) * d_ratio ** 2)


def turbulence_seeds(u: float, d: float) -> tuple[float, float, float]:
    """(k, omega, mixing_length) for a given U and pipe diameter D."""
    k = 1.5 * (TI * u) ** 2
    l_mix = L_MIX_FAC * d
    omega = math.sqrt(k) / (C_MU_25 * l_mix)
    return k, omega, l_mix


# ---- Main -------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=42,
                    help="RNG seed for reproducibility (default: 42)")
    ap.add_argument("--n-slices", type=int, default=5,
                    help="Unique d/D values (mesh-reuse slices; default 5)")
    ap.add_argument("--pts-per-slice", type=int, default=2,
                    help="Inner LHS points per d/D slice (default 2)")
    ap.add_argument("--outdir", type=str, default=".")
    ap.add_argument("--max-redraws", type=int, default=100,
                    help="Max per-cell redraws to satisfy VR cap")
    ap.add_argument("--alpha-deg", type=float,
                    default=float(os.environ.get("ALPHA_DEG", 90.0)),
                    help="Injection angle [deg] wrt -z main-flow axis. "
                         "Recorded in doe_design.csv for provenance only; "
                         "LHS variables are (d/D, HBR) independent of alpha.")
    args = ap.parse_args(argv)

    rng = np.random.default_rng(args.seed)
    n_slices = args.n_slices
    pts_per_slice = args.pts_per_slice
    n_total = n_slices * pts_per_slice
    print(f"[lhs_design] sliced LHS: {n_slices} d/D slices x "
          f"{pts_per_slice} HBR points = {n_total} cases")

    d_bins, hbr_bins = sliced_lhs(n_slices, pts_per_slice, rng)
    d_ratios = D_RATIO_MIN + d_bins * (D_RATIO_MAX - D_RATIO_MIN)

    rows = []
    for k in range(n_slices):
        d_ratio = float(d_ratios[k])
        for j in range(pts_per_slice):
            # Redraw HBR within this cell until VR <= VR_CAP.
            attempt = 0
            while True:
                attempt += 1
                hbr01 = hbr_bins[k, j]
                hbr = HBR_MIN + hbr01 * (HBR_MAX - HBR_MIN)
                vr = vr_from_hbr(hbr, d_ratio)
                if vr <= VR_CAP:
                    break
                if attempt > args.max_redraws:
                    print(
                        f"[warn] case (d/D={d_ratio:.3f}, slice {j}) "
                        f"hit VR cap after {attempt} redraws; "
                        f"clipping HBR to cap VR at {VR_CAP}.",
                        file=sys.stderr,
                    )
                    vr = VR_CAP
                    hbr = vr * d_ratio**2 / (1.0 + vr * d_ratio**2)
                    break
                # Resample just this cell's 01 value.
                hbr_bins[k, j] = rng.uniform()

            u_branch = vr * U_MAIN
            d2 = d_ratio * D1
            re_branch = u_branch * d2 / NU_CH4

            k_main, omega_main, l_main = turbulence_seeds(U_MAIN, D1)
            k_branch, omega_branch, l_branch = turbulence_seeds(u_branch, d2)

            rows.append({
                "case":          len(rows) + 1,
                "d_over_D":      round(d_ratio, 4),
                "HBR":           round(hbr, 4),
                "VR":            round(vr, 4),
                "D2_m":          round(d2, 5),
                "U_main_mps":    U_MAIN,
                "U_branch_mps":  round(u_branch, 4),
                "Re_branch":     round(re_branch, 0),
                "K_main":        round(k_main, 6),
                "K_branch":      round(k_branch, 6),
                "Omega_main":    round(omega_main, 4),
                "Omega_branch": round(omega_branch, 4),
                "mix_branch_m":  round(l_branch, 6),
                "ZJCT":          Z_JCT,
                "LMAIN":         L_MAIN,
                "alpha_deg":     round(float(args.alpha_deg), 4),
                # Mesh reuse tag : cases sharing slice_id can share the mesh.
                "slice_id":      k + 1,
            })

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    out_csv = outdir / "doe_design.csv"
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Human-readable summary table
    print()
    print(f" {'case':>4} {'d/D':>6} {'HBR %':>7} {'VR':>6} "
          f"{'D2 mm':>7} {'U_br m/s':>9} {'Re_br':>10} "
          f"{'slice':>5}")
    print("-" * 70)
    for r in rows:
        print(f" {r['case']:>4} {r['d_over_D']:>6.3f} "
              f"{r['HBR']*100:>6.2f} {r['VR']:>6.3f} "
              f"{r['D2_m']*1000:>7.2f} {r['U_branch_mps']:>9.3f} "
              f"{int(r['Re_branch']):>10d} "
              f"{r['slice_id']:>5}")

    print(f"\nWrote {out_csv}")
    print(f"Seed : {args.seed}")


if __name__ == "__main__":
    main()
