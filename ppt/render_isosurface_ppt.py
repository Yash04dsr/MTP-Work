#!/usr/bin/env python3
"""Generate presentation-grade H2 isosurface figures for case_04 and case_08.

Fixed iso-values across both cases for direct visual comparison.
Better pipe opacity, camera angle, and annotations.
"""

import numpy as np
import pyvista as pv
from pathlib import Path

pv.OFF_SCREEN = True

BASE = Path(__file__).resolve().parent.parent / "doe" / "results_full" / "cases"

FIXED_ISO_VALUES = [0.005, 0.02, 0.06]
ISO_COLORS = ["#2ecc71", "#f39c12", "#e74c3c"]
ISO_LABELS = [
    "H$_2$ = 0.5%  (dilute edge)",
    "H$_2$ = 2.0%  (bulk plume)",
    "H$_2$ = 6.0%  (dense core)",
]


def mirror_y(mesh):
    """Mirror half-domain mesh across x=0 symmetry plane."""
    reflected = mesh.copy()
    reflected.points[:, 0] *= -1
    return mesh.merge(reflected)


def render_case(case_name: str, case_dir: Path, out_path: Path,
                subtitle: str):
    """Render a single case with fixed iso-values."""
    foam_file = case_dir / "case.foam"
    if not foam_file.exists():
        foam_file.touch()

    reader = pv.OpenFOAMReader(str(foam_file))
    reader.set_active_time_value(reader.time_values[-1])
    ds = reader.read()

    internal = ds["internalMesh"]
    fld = "H2Mean" if "H2Mean" in internal.array_names else "H2"

    p = pv.Plotter(off_screen=True, window_size=(1920, 1080))
    p.set_background("white")

    wall_stl = case_dir / "constant" / "triSurface" / "wall.stl"
    if wall_stl.exists():
        wall = pv.read(str(wall_stl))
        wall_full = mirror_y(wall)
        p.add_mesh(wall_full, color="#b0bec5", opacity=0.18,
                   show_edges=False, smooth_shading=True)

    legend_entries = []
    for k, val in enumerate(FIXED_ISO_VALUES):
        try:
            iso = internal.contour([val], scalars=fld)
        except Exception:
            continue
        if iso is None or iso.n_points == 0:
            continue
        iso_full = mirror_y(iso)
        color = ISO_COLORS[k]
        opacity = 0.75 if k == 0 else (0.55 if k == 1 else 0.45)
        p.add_mesh(iso_full, color=color, opacity=opacity,
                   show_edges=False, smooth_shading=True)
        legend_entries.append([f"{fld} = {val}", color])

    if legend_entries:
        p.add_legend(labels=legend_entries, bcolor="white", border=True,
                     size=(0.22, 0.06 * len(legend_entries)),
                     loc="upper right", face="rectangle")

    p.add_axes(color="black", line_width=2)

    p.camera_position = [(-3.5, 3.0, -3.0), (0.0, 0.1, 3.5), (0, 1, 0)]
    p.camera.zoom(1.2)

    p.add_text(subtitle, position="lower_left", font_size=14,
               color="black", shadow=True)
    p.add_text(f"Fixed iso-values: {FIXED_ISO_VALUES}",
               position="upper_left", font_size=9, color="gray")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    p.screenshot(str(out_path), transparent_background=False)
    p.close()
    print(f"Wrote {out_path}  ({out_path.stat().st_size/1024:.0f} KB)")


def main():
    out_dir = Path(__file__).resolve().parent

    render_case(
        "case_04",
        BASE / "case_04",
        out_dir / "fig_iso_case04_best.png",
        "90\u00b0 Top | Case 04 | VR = 3.81 | CoV = 0.066",
    )

    render_case(
        "case_08",
        BASE / "case_08",
        out_dir / "fig_iso_case08_worst.png",
        "90\u00b0 Top | Case 08 | VR = 0.69 | CoV = 0.707",
    )


if __name__ == "__main__":
    main()
