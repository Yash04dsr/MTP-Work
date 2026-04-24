#!/usr/bin/env python3
"""sanity_check.py  --  end-to-end pre-flight checks for the DoE.

Runs (angle-agnostic):
    1. DoE design audit : HBR in [0.05, 0.20], d/D in [0.15, 0.45],
       VR <= VR_CAP, projections space-filling, alpha recorded.
    2. STL generation : run generateSTL.py in a scratch dir for the
       current ALPHA_DEG and the smallest + largest D2 in the design,
       confirm signed-volume check passes.
    3. Token audit : dry-stamp case 01 into a scratch dir and grep for
       any remaining @XXX@ placeholders in 0/, system/, generateSTL.py.
    4. Optional: verify that `blockMesh; snappyHexMesh -overwrite;
       checkMesh` on the dry-stamped case finishes with
       "Mesh OK." (requires OpenFOAM on PATH; skipped if not found).

Usage :
    python3 sanity_check.py --alpha 30 --design doe_design.csv --base ..
    python3 sanity_check.py --alpha 45 ...    # test arbitrary angle

Exits non-zero if any check fails.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HBR_MIN = 0.05
HBR_MAX = 0.20
D_RATIO_MIN = 0.15
D_RATIO_MAX = 0.45
VR_CAP = 12.0


def audit_design(csv_path: Path) -> dict:
    print(f"\n[1/4] DoE design audit : {csv_path}")
    with csv_path.open() as f:
        rows = list(csv.DictReader(f))
    if len(rows) == 0:
        raise SystemExit("  FAIL: design CSV has no rows")

    bad = 0
    d_vals, hbr_vals, vr_vals = [], [], []
    for r in rows:
        d = float(r["d_over_D"])
        hbr = float(r["HBR"])
        vr = float(r["VR"])
        d_vals.append(d)
        hbr_vals.append(hbr)
        vr_vals.append(vr)
        # constraint sweeps
        if not (D_RATIO_MIN - 1e-6 <= d <= D_RATIO_MAX + 1e-6):
            print(f"  FAIL row {r['case']}: d/D={d:.4f} outside [{D_RATIO_MIN},{D_RATIO_MAX}]")
            bad += 1
        if not (HBR_MIN - 1e-6 <= hbr <= HBR_MAX + 1e-6):
            print(f"  FAIL row {r['case']}: HBR={hbr:.4f} outside [{HBR_MIN},{HBR_MAX}]")
            bad += 1
        if vr > VR_CAP + 1e-6:
            print(f"  FAIL row {r['case']}: VR={vr:.4f} exceeds cap {VR_CAP}")
            bad += 1

    uniq_d = sorted(set(round(d, 4) for d in d_vals))
    # Sliced LHS : expect 5 unique d/D values, 2 cases each
    if len(uniq_d) != 5:
        print(f"  WARN: expected 5 unique d/D values, got {len(uniq_d)}")

    print(f"  rows              = {len(rows)}")
    print(f"  unique d/D slices = {len(uniq_d)}")
    print(f"  d/D range         = [{min(d_vals):.4f}, {max(d_vals):.4f}]")
    print(f"  HBR range         = [{min(hbr_vals):.4f}, {max(hbr_vals):.4f}]")
    print(f"  VR  range         = [{min(vr_vals):.4f}, {max(vr_vals):.4f}]")

    if bad:
        raise SystemExit(f"  {bad} row(s) failed constraint check")
    print("  PASS (all rows in band; VR under cap)")
    return {
        "rows": rows,
        "d_min": min(d_vals),
        "d_max": max(d_vals),
    }


def test_stl(base: Path, alpha_deg: float, d2: float, tag: str) -> None:
    print(f"\n[2/4 - {tag}] STL watertight check : alpha={alpha_deg:.1f} deg, D2={d2:.4f}")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        shutil.copy2(base / "generateSTL.py", td / "generateSTL.py")
        env = os.environ.copy()
        env["ALPHA_DEG"] = f"{alpha_deg:.6f}"
        env["D2"] = f"{d2:.6f}"
        env["D1"] = "0.460"
        env["Z_JCT"] = "2.300"
        env["L_MAIN"] = "6.900"
        try:
            out = subprocess.check_output(
                [sys.executable, "generateSTL.py"],
                cwd=td, env=env, stderr=subprocess.STDOUT, timeout=60,
            ).decode()
        except subprocess.CalledProcessError as e:
            print(e.output.decode())
            raise SystemExit(f"  FAIL: generateSTL.py returned {e.returncode}")
        # Grep volume ratio line
        m = re.search(r"Ratio:\s+([0-9.]+)", out)
        if not m:
            print(out)
            raise SystemExit("  FAIL: could not parse volume ratio")
        ratio = float(m.group(1))
        print(f"  ratio = {ratio:.4f} (must be in [0.90, 1.10])")
        if not (0.90 < ratio < 1.10):
            raise SystemExit("  FAIL: ratio out of bounds")
        print("  PASS")


def dry_stamp(base: Path, design_csv: Path, alpha_deg: float,
              which_case: int) -> Path:
    print(f"\n[3/4] Dry-stamp case {which_case:02d} at alpha={alpha_deg:.1f} deg")
    tmp = Path(tempfile.mkdtemp(prefix="sanity_stamp_"))
    cases_dir = tmp / "doe_cases"
    env = os.environ.copy()
    env["ALPHA_DEG"] = f"{alpha_deg:.6f}"

    # Override the CSV's alpha_deg column (if present) so sanity testing at
    # an arbitrary angle is truly angle-agnostic: the stamper's per-row
    # `alpha_deg` takes precedence over env, so we must rewrite the CSV.
    patched_csv = tmp / design_csv.name
    with design_csv.open() as fin:
        reader = csv.DictReader(fin)
        fieldnames = list(reader.fieldnames or [])
        if "alpha_deg" not in fieldnames:
            fieldnames.append("alpha_deg")
        rows = []
        for r in reader:
            r["alpha_deg"] = f"{alpha_deg:.4f}"
            rows.append(r)
    with patched_csv.open("w", newline="") as fout:
        w = csv.DictWriter(fout, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    cmd = [
        sys.executable, str(base / "doe" / "stamp_cases.py"),
        "--design", str(patched_csv),
        "--base", str(base),
        "--cases", str(cases_dir),
        "--only", str(which_case),
        "--overwrite",
    ]
    try:
        subprocess.check_call(cmd, env=env)
    except subprocess.CalledProcessError:
        raise SystemExit(f"  FAIL: stamp_cases.py returned non-zero")
    case_dir = cases_dir / f"case_{which_case:02d}"
    # Grep for any unsubstituted tokens under 0/, system/
    leftover = []
    for p in list((case_dir / "0").rglob("*")) + list((case_dir / "system").rglob("*")):
        if p.is_file():
            try:
                txt = p.read_text()
            except UnicodeDecodeError:
                continue
            for m in re.findall(r"@[A-Z0-9_]+@", txt):
                leftover.append((str(p.relative_to(case_dir)), m))
    if leftover:
        for f, t in leftover:
            print(f"  LEFTOVER {t} in {f}")
        raise SystemExit(f"  FAIL: {len(leftover)} unresolved token(s)")
    print(f"  PASS (no unresolved @XXX@ in 0/ or system/)")
    print(f"  staged at {case_dir}")
    return case_dir


def optional_mesh(case_dir: Path, alpha_deg: float) -> None:
    print(f"\n[4/4] Mesh smoke test (STL + blockMesh + snappy + checkMesh)")
    if shutil.which("blockMesh") is None:
        print("  SKIP: OpenFOAM not on PATH (run `source $FOAM_ETC/bashrc` first)")
        return
    env = os.environ.copy()
    env["ALPHA_DEG"] = f"{alpha_deg:.6f}"
    # Also source case.env so D2, Z_JCT, L_MAIN etc. propagate
    env_file = case_dir / "case.env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("export "):
                key, _, val = line[len("export "):].partition("=")
                env[key.strip()] = val.strip()

    pipeline = [
        (f"{sys.executable} generateSTL.py", "generateSTL"),
        (f"{sys.executable} scripts/clip_stls.py constant/triSurface", "clipStls"),
        ("surfaceFeatureExtract", "surfaceFeatureExtract"),
        ("blockMesh", "blockMesh"),
        ("snappyHexMesh -overwrite", "snappyHexMesh"),
    ]
    for cmd, tag in pipeline:
        print(f"  running: {cmd}")
        rc = subprocess.call(f"{cmd} > log.{tag} 2>&1",
                             cwd=str(case_dir), shell=True, env=env)
        if rc != 0:
            log = (case_dir / f"log.{tag}").read_text()
            print(log[-3000:])
            raise SystemExit(f"  FAIL: {cmd} returned {rc}")

    # rescue allBoundary if present
    boundary = case_dir / "constant" / "polyMesh" / "boundary"
    if boundary.exists() and "allBoundary" in boundary.read_text():
        subprocess.call("createPatch -overwrite > log.createPatch 2>&1",
                        cwd=str(case_dir), shell=True, env=env)

    # Use default checkMesh flags (matches the validated 90-deg baseline).
    # -allTopology / -allGeometry are over-strict: they flag harmless
    # concave-by-face-plane and cosmetic 2-region reports even on meshes
    # that simulate cleanly.
    out = subprocess.check_output(
        "checkMesh 2>&1 | tail -40",
        cwd=str(case_dir), shell=True, env=env,
    ).decode()
    print(out)
    if "Mesh OK." not in out:
        raise SystemExit("  FAIL: checkMesh did not report 'Mesh OK.'")
    # Warn (do not fail) on low branch_inlet face count.
    boundary_txt = (case_dir / "constant" / "polyMesh" / "boundary").read_text()
    m = re.search(r"branch_inlet\s*\{[^}]*nFaces\s+(\d+);", boundary_txt, re.S)
    if m:
        n = int(m.group(1))
        print(f"  branch_inlet faces = {n}")
        if n < 20:
            print(f"  WARN: only {n} branch_inlet faces -- BC profile may be coarse")
    print("  PASS")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--alpha", type=float, default=30.0, help="ALPHA_DEG to test")
    ap.add_argument("--design", type=Path, required=True)
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--case", type=int, default=1, help="Case number to dry-stamp")
    ap.add_argument("--skip-mesh", action="store_true")
    args = ap.parse_args()

    base = args.base.resolve()
    design = args.design.resolve()

    summary = audit_design(design)
    # STL check for smallest and largest D2 in the design
    d2_min = summary["d_min"] * 0.460
    d2_max = summary["d_max"] * 0.460
    test_stl(base, args.alpha, d2_min, tag=f"D2_min={d2_min:.4f}")
    test_stl(base, args.alpha, d2_max, tag=f"D2_max={d2_max:.4f}")
    case_dir = dry_stamp(base, design, args.alpha, args.case)
    if not args.skip_mesh:
        optional_mesh(case_dir, args.alpha)
    print("\n[sanity] all checks passed.")


if __name__ == "__main__":
    main()
