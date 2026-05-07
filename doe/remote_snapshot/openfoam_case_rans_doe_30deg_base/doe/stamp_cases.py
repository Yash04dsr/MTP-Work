#!/usr/bin/env python3
"""stamp_cases.py  --  materialise DoE cases from base + design CSV.

Input :
    ./doe_design.csv           (produced by lhs_design.py)
    <base_dir>                 (the doe_base template, e.g. ../)

Output :
    <cases_dir>/case_01/ .. case_10/
        0/               (tokens replaced per case)
        constant/        (copied verbatim from base)
        system/          (copied; snappyHexMeshDict stamped with d/D)
        generateSTL.py   (copied; takes D2/Z_JCT/L_MAIN from case.env)
        case.env         (shell-sourceable per-case parameters)
        case_info.json   (machine-readable case metadata)

Every case directory is SELF-CONTAINED : you can `cd case_NN && ./Allrun`
and the run is fully defined without any external dependencies.

Usage :
    python3 stamp_cases.py \
        --design  doe_design.csv \
        --base    ..                    \
        --cases   ../../doe_cases       \
        [--overwrite]
"""
from __future__ import annotations

import argparse
import csv
import math
import json
import os
import re
import shutil
import stat
from pathlib import Path


TOKENS = [
    # replaced in 0/U
    ("@UMAIN@",         lambda r: r["U_main_mps"]),
    ("@UBRANCH@",       lambda r: r["U_branch_mps"]),
    ("@D1@",            lambda r: 0.460),            # main pipe diameter [m]
    ("@D2@",            lambda r: r["D2_m"]),
    ("@ZJCT@",          lambda r: r["ZJCT"]),
    # replaced in 0/k
    ("@K_MAIN@",        lambda r: r["K_main"]),
    ("@K_BRANCH@",      lambda r: r["K_branch"]),
    # replaced in 0/omega
    ("@OMEGA_MAIN@",    lambda r: r["Omega_main"]),
    ("@OMEGA_BRANCH@",  lambda r: r["Omega_branch"]),
    ("@MIX_BRANCH@",    lambda r: r["mix_branch_m"]),
    # 30deg fork: tilted-branch direction tokens
    ("@ALPHA_DEG@",     lambda r: ALPHA_DEG),
    ("@SIN_ALPHA@",     lambda r: SIN_ALPHA),
    ("@COS_ALPHA@",     lambda r: COS_ALPHA),
    ("@YJCT@",          lambda r: 0.230),  # = R1 = D1/2
    ("@UBY@",           lambda r: -r["U_branch_mps"] * SIN_ALPHA),
    ("@UBZ@",           lambda r:  r["U_branch_mps"] * COS_ALPHA),
    # Branch interior seed for snappyHexMesh locationsInMesh:
    ("@YBRANCH_INT@",   lambda r: 0.230 + 0.5 * float(max(1.380, 0.230 + 12.0 * r["D2_m"])) * SIN_ALPHA),
    ("@ZBRANCH_INT@",   lambda r: r["ZJCT"] - 0.5 * float(max(1.380, 0.230 + 12.0 * r["D2_m"])) * COS_ALPHA),

]

# Numeric columns cast from CSV strings.
NUM_COLS = (
    "d_over_D", "HBR", "VR", "D2_m", "U_main_mps", "U_branch_mps",
    "Re_branch", "K_main", "K_branch", "Omega_main", "Omega_branch",
    "mix_branch_m", "ZJCT", "LMAIN",
)
INT_COLS = ("case", "slice_id")

# --- 30deg fork: tilted-branch configuration -----------------------
# Branch axis makes ALPHA_DEG with the -z axis.  ALPHA=90 reproduces
# the perpendicular T (= parent 90deg base).  Override via env if needed.
ALPHA_DEG_DEFAULT = 30.0
import os as _os
ALPHA_DEG = float(_os.environ.get("ALPHA_DEG", ALPHA_DEG_DEFAULT))
SIN_ALPHA = math.sin(math.radians(ALPHA_DEG))
COS_ALPHA = math.cos(math.radians(ALPHA_DEG))



def _load_design(path: Path) -> list[dict]:
    with path.open() as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for c in NUM_COLS:
            r[c] = float(r[c])
        for c in INT_COLS:
            r[c] = int(r[c])
    return rows


def _format_num(v) -> str:
    """Format numbers so OpenFOAM's ascii parser is happy."""
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def _sed(path: Path, row: dict) -> None:
    text = path.read_text()
    for tok, fn in TOKENS:
        text = text.replace(tok, _format_num(fn(row)))
    path.write_text(text)


def _stamp_snappy(path: Path, row: dict) -> None:
    """Update junction-refine + jet-refine radii to match per-case D2."""
    text = path.read_text()
    d2 = row["D2_m"]
    z_jct = row["ZJCT"]

    # junctionRefine : sphere radius ~ 3 * D2 (captures jet shear layer)
    jct_radius = max(3.0 * d2, 6.0 * 0.115)   # >= 0.69 for small D2
    # jetRefine : cylinder radius = 0.23 (main pipe radius), unchanged
    # Update only the sphere radius and centre.
    text = re.sub(
        r"(junctionRefine\s*\{\s*type\s+searchableSphere;\s*"
        r"centre\s+\(0\s+0\s+)[0-9.]+(\);\s*radius\s+)[0-9.]+(;)",
        rf"\g<1>{z_jct:.4f}\g<2>{jct_radius:.4f}\g<3>",
        text,
    )
    # jetRefine cylinder : point1 just downstream of sphere, point2 8D
    # downstream.  Keep radius at main-pipe radius 0.23.
    p1 = z_jct + jct_radius * 0.5          # just past sphere edge
    p2 = min(z_jct + 8.0 * 0.460, row["LMAIN"] - 0.10)
    text = re.sub(
        r"(jetRefine\s*\{\s*type\s+searchableCylinder;\s*"
        r"point1\s+\(0\s+0\s+)[0-9.]+(\);\s*"
        r"point2\s+\(0\s+0\s+)[0-9.]+(\);)",
        rf"\g<1>{p1:.4f}\g<2>{p2:.4f}\g<3>",
        text,
    )
    # Substitute template tokens used by locationsInMesh.
    text = text.replace('@Z_JCT@', f'{z_jct:.4f}')
    # Also walk the generic TOKENS list so tilted-branch tokens
    # (@YBRANCH_INT@, @ZBRANCH_INT@, @ALPHA_DEG@) are substituted.
    for tok, fn in TOKENS:
        text = text.replace(tok, _format_num(fn(row)))
    path.write_text(text)


def _make_allrun(case_dir: Path, row: dict) -> None:
    allrun = case_dir / "Allrun"
    script = rf"""#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Auto-generated by stamp_cases.py.  Runs the full pipeline for case {row['case']:02d}
#   d/D = {row['d_over_D']:.4f}   HBR = {row['HBR']*100:.2f}%   VR = {row['VR']:.3f}
# ---------------------------------------------------------------------------
set -eo pipefail
cd "$(dirname "$0")"

# Source OpenFOAM (edit OPENFOAM_BASHRC if your install lives elsewhere).
# OpenFOAM's bashrc emits a harmless pop_var_context warning in
# non-interactive shells (and references an unset var); both trip
# `set -e` / `set -u`, so disable them around the source.
OPENFOAM_BASHRC="${{OPENFOAM_BASHRC:-/usr/lib/openfoam/openfoam2406/etc/bashrc}}"
set +eu
# shellcheck disable=SC1090
source "$OPENFOAM_BASHRC" 2>/dev/null
set -e

# Export per-case geometry for generateSTL.py
# shellcheck disable=SC1091
source ./case.env

# ----- optional mesh-reuse shortcut ---------------------------------------
# If $REUSE_MESH_FROM points to a case with the same d/D slice, copy its
# polyMesh + decomposed processor dirs; otherwise build from scratch.
if [[ "${{REUSE_MESH_FROM:-}}" != "" && -d "${{REUSE_MESH_FROM}}/constant/polyMesh" ]]; then
    echo "[case_{row['case']:02d}] reusing mesh from ${{REUSE_MESH_FROM}}"
    cp -r "${{REUSE_MESH_FROM}}/constant/polyMesh"      constant/
    cp -r "${{REUSE_MESH_FROM}}/constant/triSurface"    constant/ 2>/dev/null || true
    if compgen -G "${{REUSE_MESH_FROM}}/processor*" > /dev/null; then
        for p in "${{REUSE_MESH_FROM}}"/processor*; do
            dst="./$(basename "$p")"
            mkdir -p "$dst/constant"
            cp -r "$p/constant/polyMesh" "$dst/constant/"
        done
    fi
else
    echo "[case_{row['case']:02d}] building mesh from scratch"
    python3 generateSTL.py                                | tee log.generateSTL
    python3 scripts/clip_stls.py constant/triSurface   | tee log.clipStls
    surfaceFeatureExtract                                 | tee log.surfaceFeatureExtract
    blockMesh                                             | tee log.blockMesh
    snappyHexMesh -overwrite                              | tee log.snappyHexMesh
    # rescue branch_inlet faces from allBoundary fallback (see createPatchDict)
    if grep -q "allBoundary" constant/polyMesh/boundary; then
        createPatch -overwrite                            | tee log.createPatch
    fi
    # snappy-era diagnostic fields carry stale boundary entries after createPatch
    rm -f 0/cellLevel 0/pointLevel 0/cellZones_0 0/pointZones_0
    checkMesh -allTopology -allGeometry                   | tee log.checkMesh
    decomposePar -force                                   | tee log.decomposePar
fi

# ----- initial field ------------------------------------------------------
# Always rebuild processor*/0 from the case-local 0/ template so field
# sizes match the (possibly reused) mesh.
rm -rf processor*/0 processor*/0.*
decomposePar -force                                   | tee log.decomposePar

# (potentialFoam warm-start removed -- it leaves rho with wrong dimensions
#  for rhoReactingBuoyantFoam.  High-VR startup is instead handled by
#  relaxation in fvSolution.)

# ----- main solver --------------------------------------------------------
mpirun --use-hwthread-cpus -n 16 rhoReactingBuoyantFoam -parallel    | tee log.solver

# ----- reconstruction + metrics -------------------------------------------
reconstructPar -latestTime                                | tee log.reconstructPar

echo "[case_{row['case']:02d}] SIM DONE at $(date +%FT%T)"
touch SIM_DONE
"""
    allrun.write_text(script)
    allrun.chmod(allrun.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _make_env(case_dir: Path, row: dict) -> None:
    env = (
        f"# Auto-generated per-case parameters for stamp_cases.py\n"
        f"export CASE_ID={row['case']:02d}\n"
        f"export D_OVER_D={row['d_over_D']:.6f}\n"
        f"export HBR={row['HBR']:.6f}\n"
        f"export VR={row['VR']:.6f}\n"
        f"export SLICE_ID={row['slice_id']}\n"
        f"\n"
        f"# Passed to generateSTL.py via os.environ\n"
        f"export D1=0.460\n"
        f"export D2={row['D2_m']:.6f}\n"
        f"export Z_JCT={row['ZJCT']:.4f}\n"
        f"export L_MAIN={row['LMAIN']:.4f}\n"
        f"\n"
        f"# Bulk velocities (for sanity checks / post-processing)\n"
        f"export U_MAIN={row['U_main_mps']:.6f}\n"
        f"export U_BRANCH={row['U_branch_mps']:.6f}\n"
        f"\n"
        f"# 30deg fork: branch tilt parameter (read by generateSTL.py)\n"
        f"export ALPHA_DEG={ALPHA_DEG:.4f}\n"
    )
    (case_dir / "case.env").write_text(env)


def _make_info(case_dir: Path, row: dict) -> None:
    (case_dir / "case_info.json").write_text(
        json.dumps({k: (v if not isinstance(v, float) else round(v, 6))
                    for k, v in row.items()}, indent=2) + "\n"
    )


def stamp_one(base: Path, case_dir: Path, row: dict,
              overwrite: bool = False) -> None:
    if case_dir.exists():
        if not overwrite:
            raise SystemExit(f"refusing to overwrite existing {case_dir}; "
                             f"pass --overwrite or remove it")
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)

    # Copy the file set we actually need for running.  Keep it lean --
    # we don't want to drag along any processor*/ or old log files.
    for name in ("0", "constant", "system"):
        shutil.copytree(base / name, case_dir / name)
    for fname in ("generateSTL.py",):
        shutil.copy2(base / fname, case_dir / fname)
    # ensure scripts/ exists inside the case so Allrun can find clip_stls.py
    scripts_src = base / "scripts"
    if scripts_src.is_dir():
        shutil.copytree(scripts_src, case_dir / "scripts")

    # Stamp the token files.
    _sed(case_dir / "0" / "U",     row)
    _sed(case_dir / "0" / "k",     row)
    _sed(case_dir / "0" / "omega", row)
    _stamp_snappy(case_dir / "system" / "snappyHexMeshDict", row)

    _make_env(case_dir, row)
    _make_info(case_dir, row)
    _make_allrun(case_dir, row)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--base",   required=True, type=Path,
                    help="Path to doe_base (the template case)")
    ap.add_argument("--cases",  required=True, type=Path,
                    help="Output directory where case_NN/ dirs go")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--only", type=int, nargs="+", default=None,
                    help="Restrict to these 1-indexed case numbers (e.g. --only 3 4 5)")
    args = ap.parse_args()

    rows = _load_design(args.design.resolve())
    base = args.base.resolve()
    cases_root = args.cases.resolve()
    cases_root.mkdir(parents=True, exist_ok=True)

    for r in rows:
        if args.only is not None and r["case"] not in args.only:
            continue
        case_dir = cases_root / f"case_{r['case']:02d}"
        print(f"[stamp] case {r['case']:02d}  d/D={r['d_over_D']:.3f}  "
              f"HBR={r['HBR']*100:.1f}%  VR={r['VR']:.3f}  "
              f"-> {case_dir}")
        stamp_one(base, case_dir, r, overwrite=args.overwrite)

    # Also stash the design CSV alongside the cases for provenance.
    shutil.copy2(args.design, cases_root / "doe_design.csv")
    print(f"\n[stamp] wrote {len(rows)} cases under {cases_root}")


if __name__ == "__main__":
    main()
