#!/usr/bin/env python3
"""Render the actual case_05 30deg geometry (D2=0.13631, L_BRANCH=1.8657)."""
import os
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
import pyvista as pv
from pathlib import Path

HERE = Path(__file__).parent
stl_dir = HERE / "case_05_stl"

pv.OFF_SCREEN = True

def render(out: Path, view: str):
    p = pv.Plotter(off_screen=True, window_size=(1600, 900))
    p.set_background("white")
    for name, (col, alpha) in {
        "wall.stl":         ("#95a5a6", 0.25),
        "main_inlet.stl":   ("#27ae60", 0.95),
        "outlet.stl":       ("#c0392b", 0.95),
        "branch_inlet.stl": ("#e67e22", 0.95),
    }.items():
        f = stl_dir / name
        if not f.exists():
            continue
        mesh = pv.read(str(f))
        p.add_mesh(mesh, color=col, opacity=alpha,
                   show_edges=(alpha < 0.9),
                   edge_color="black", line_width=0.3)
    p.add_axes(color="black", line_width=2)
    if view == "side":
        p.camera_position = [(15, 0.3, 3.0), (0, 0.3, 3.0), (0, 1, 0)]
        p.camera.zoom(1.8)
        title = ("30° DoE case_05:  d/D=0.296  VR=1.241  HBR=9.8%\n"
                 "Branch D2=0.136 m, L_branch=1.87 m — view: -x looking at y-z plane")
    else:
        p.camera_position = [(8, 5, 0), (0, 0.5, 3.0), (0, 1, 0)]
        p.camera.zoom(1.4)
        title = ("30° DoE case_05 — isometric view")
    p.add_text(title, font_size=13, color="black", position="upper_left")
    p.screenshot(str(out))
    print(f"wrote {out}")

render(HERE / "case_05_side.png", "side")
render(HERE / "case_05_iso.png", "iso")
