#!/usr/bin/env python3
"""batch_render_all.py — regenerate the full 12-figure pack for every case.

Calls make_figures.py and make_distance_figures.py for each case that has
both constant/polyMesh and a reconstructed time directory (1.2/).

Usage:
    python3 batch_render_all.py
"""
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent  # doe/

CAMPAIGNS = [
    ("results_full/cases",         "90_top"),
    ("results_full_30deg/cases",   "30_top"),
    ("results_full_90deg_bottom",  "90_bot"),
    ("results_full_30deg_bottom",  "30_bot"),
]

MAKE_FIGURES = TOOLS / "make_figures.py"
MAKE_DIST    = TOOLS / "make_distance_figures.py"


def run_cmd(cmd, label):
    print(f"    {label} ... ", end="", flush=True)
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=300
    )
    if result.returncode == 0:
        print("OK")
    else:
        print(f"FAIL (rc={result.returncode})")
        err = result.stderr.strip().split("\n")
        for line in err[-5:]:
            print(f"      {line}")
    return result.returncode == 0


def main():
    total = 0
    success = 0
    failed = []

    for rel_path, camp_label in CAMPAIGNS:
        camp_dir = ROOT / rel_path
        if not camp_dir.exists():
            print(f"\n[SKIP] {camp_label}: {camp_dir} not found")
            continue

        cases = sorted(
            [d for d in camp_dir.iterdir()
             if d.is_dir() and d.name.startswith("case_")],
            key=lambda p: p.name
        )

        print(f"\n{'='*60}")
        print(f"Campaign: {camp_label} ({len(cases)} cases)")
        print(f"{'='*60}")

        for case_dir in cases:
            poly = case_dir / "constant" / "polyMesh"
            time_dir = None
            for t in ["1.2", "1.0", "0.8"]:
                if (case_dir / t).is_dir():
                    time_dir = t
                    break

            if not poly.exists() or time_dir is None:
                print(f"\n  [{case_dir.name}] SKIP — missing polyMesh or time dir")
                continue

            total += 1
            fig_dir = case_dir / "figures"

            # Delete old figures
            if fig_dir.exists():
                for f in fig_dir.glob("*.png"):
                    f.unlink()
            fig_dir.mkdir(exist_ok=True)

            print(f"\n  [{case_dir.name}] time={time_dir}")

            ok1 = run_cmd(
                [sys.executable, str(MAKE_FIGURES),
                 str(case_dir), str(fig_dir), "--time", time_dir],
                "make_figures"
            )

            ok2 = run_cmd(
                [sys.executable, str(MAKE_DIST),
                 "--case", str(case_dir), "--outdir", str(fig_dir),
                 "--time", time_dir, "--field-suffix", "Mean"],
                "make_distance_figures"
            )

            if ok1 and ok2:
                n = len(list(fig_dir.glob("*.png")))
                print(f"    → {n} figures generated")
                success += 1
            else:
                failed.append(f"{camp_label}/{case_dir.name}")

    print(f"\n{'='*60}")
    print(f"DONE: {success}/{total} cases rendered successfully")
    if failed:
        print(f"Failed: {', '.join(failed)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
