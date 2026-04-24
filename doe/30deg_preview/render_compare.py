#!/usr/bin/env python3
"""Render side-by-side PNGs of the 90deg and 30deg STL geometries."""
import os
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
import pyvista as pv
from pathlib import Path

HERE = Path(__file__).parent
pv.OFF_SCREEN = True

def render_one(stl_dir: Path, title: str, out: Path):
    p = pv.Plotter(off_screen=True, window_size=(1600, 900))
    p.set_background("white")
    colors = {
        "wall.stl":         ("#95a5a6", 0.15),
        "main_inlet.stl":   ("#27ae60", 0.95),
        "outlet.stl":       ("#c0392b", 0.95),
        "branch_inlet.stl": ("#e67e22", 0.95),
    }
    for name, (col, alpha) in colors.items():
        f = stl_dir / name
        if not f.exists():
            continue
        mesh = pv.read(str(f))
        p.add_mesh(mesh, color=col, opacity=alpha,
                   show_edges=(alpha < 0.9),
                   edge_color="black", line_width=0.3)
    p.add_axes(color="black", line_width=2)
    # iso view, camera focused near junction (z≈2.3, y≈0.3)
    p.camera_position = [(8, 6, 9), (0, 0.5, 3.0), (0, 1, 0)]
    p.camera.zoom(1.5)
    p.add_text(title, font_size=14, color="black", position="upper_left")
    p.screenshot(str(out))
    print(f"wrote {out}")

def render_side(stl_dir: Path, title: str, out: Path):
    """Side view in x=0 plane (y-z) to show the tilt clearly."""
    p = pv.Plotter(off_screen=True, window_size=(1600, 900))
    p.set_background("white")
    colors = {
        "wall.stl":         ("#95a5a6", 0.25),
        "main_inlet.stl":   ("#27ae60", 0.95),
        "outlet.stl":       ("#c0392b", 0.95),
        "branch_inlet.stl": ("#e67e22", 0.95),
    }
    for name, (col, alpha) in colors.items():
        f = stl_dir / name
        if not f.exists():
            continue
        mesh = pv.read(str(f))
        p.add_mesh(mesh, color=col, opacity=alpha,
                   show_edges=(alpha < 0.9),
                   edge_color="black", line_width=0.3)
    p.add_axes(color="black", line_width=2)
    # View from +x looking at y-z plane
    p.camera_position = [(15, 0.3, 3.0), (0, 0.3, 3.0), (0, 1, 0)]
    p.camera.zoom(1.8)
    p.add_text(title + "  (view: -x looking at y-z plane)",
               font_size=14, color="black", position="upper_left")
    p.screenshot(str(out))
    print(f"wrote {out}")

render_one(HERE / "stl_alpha90", "α = 90° (perpendicular T, current DoE)",
           HERE / "preview_alpha90_iso.png")
render_one(HERE / "stl_alpha30", "α = 30° (co-flow Y-junction, new 30° DoE)",
           HERE / "preview_alpha30_iso.png")
render_side(HERE / "stl_alpha90", "α = 90° (perpendicular T)",
            HERE / "preview_alpha90_side.png")
render_side(HERE / "stl_alpha30", "α = 30° (co-flow Y, tilted branch)",
            HERE / "preview_alpha30_side.png")
print("done")
