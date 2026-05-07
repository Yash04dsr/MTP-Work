#!/usr/bin/env python3
"""batch_add_cov_plot.py — Add fig_CoV_vs_zD.png to every case.

Only runs the CoV vs z/D plot (not the full figure set), so it's fast.
"""
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent

CAMPAIGNS = [
    ("results_full/cases",         "90_top"),
    ("results_full_30deg/cases",   "30_top"),
    ("results_full_90deg_bottom",  "90_bot"),
    ("results_full_30deg_bottom",  "30_bot"),
]

SCRIPT = TOOLS / "make_distance_figures.py"


def main():
    total = 0
    success = 0

    for rel_path, camp_label in CAMPAIGNS:
        camp_dir = ROOT / rel_path
        if not camp_dir.exists():
            continue

        cases = sorted(
            [d for d in camp_dir.iterdir()
             if d.is_dir() and d.name.startswith("case_")],
            key=lambda p: p.name
        )

        print(f"\n{'='*50}")
        print(f"Campaign: {camp_label} ({len(cases)} cases)")
        print(f"{'='*50}")

        for case_dir in cases:
            poly = case_dir / "constant" / "polyMesh"
            time_dir = None
            for t in ["1.2", "1.0", "0.8"]:
                if (case_dir / t).is_dir():
                    time_dir = t
                    break

            if not poly.exists() or time_dir is None:
                continue

            fig_dir = case_dir / "figures"
            fig_dir.mkdir(exist_ok=True)

            total += 1
            print(f"  [{case_dir.name}] ", end="", flush=True)

            result = subprocess.run(
                [sys.executable, str(SCRIPT),
                 "--case", str(case_dir), "--outdir", str(fig_dir),
                 "--time", time_dir, "--field-suffix", "Mean"],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0 and (fig_dir / "fig_CoV_vs_zD.png").exists():
                print("OK")
                success += 1
            else:
                print(f"FAIL")
                for line in result.stderr.strip().split("\n")[-3:]:
                    print(f"    {line}")

    print(f"\n{'='*50}")
    print(f"DONE: {success}/{total} cases got fig_CoV_vs_zD.png")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
