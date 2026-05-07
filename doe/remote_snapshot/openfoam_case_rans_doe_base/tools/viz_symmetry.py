#!/usr/bin/env python3
"""viz_symmetry.py — four-panel explainer figure for the x=0 symmetry plane.

Shows:
  A. Full T-junction geometry with the x=0 symmetry plane highlighted.
  B. The same geometry, cut by x=0; the +x half is the portion that would
     actually be meshed. The cut face (at x=0) becomes the symmetryPlane BC.
  C. Same half-domain, viewed end-on from -x, so you can see the pipe cross-
     section and how the full flow is recovered by mirror-reflection.
  D. Composite illustrating mesh savings: full 953 k-cell medium vs 478 k-cell
     half-domain equivalent.

Usage:
    make_figures_venv/python viz_symmetry.py <case_dir> <output_png>
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
import pyvista as pv  # noqa: E402

pv.OFF_SCREEN = True

PATCH_COLORS = {
    "main_inlet": "#27ae60",
    "branch_inlet": "#e67e22",
    "outlet": "#c0392b",
    "wall": "#95a5a6",
}
SYM_COLOR = "#f1c40f"   # symmetry plane — golden yellow


def load_stls(case: Path) -> dict[str, pv.PolyData]:
    tri = case / "constant" / "triSurface"
    out = {}
    for name in PATCH_COLORS:
        stl = tri / f"{name}.stl"
        if stl.exists():
            out[name] = pv.read(str(stl))
    return out


# Known pipe geometry (from generateSTL.py / CHAPTER.md §2)
#   main pipe:   z in [0, 9.2],   radius 0.23
#   branch pipe: y in [0.23, 1.38] centred on z = 4.6, radius 0.115/2 = 0.0575
PIPE = dict(z_min=0.0, z_max=9.2, R_main=0.23,
            branch_y_min=0.23, branch_y_max=1.38, z_branch=4.6, R_branch=0.0575)


def build_sym_plane_full(margin: float = 0.05) -> pv.PolyData:
    """Big rectangle in the x = 0 plane across the whole domain bounding box."""
    y0 = -PIPE["R_main"] - margin
    y1 = PIPE["branch_y_max"] + margin
    z0 = PIPE["z_min"] - margin
    z1 = PIPE["z_max"] + margin
    return pv.Plane(
        center=(0.0, (y0 + y1) / 2, (z0 + z1) / 2),
        direction=(1.0, 0.0, 0.0),
        i_size=(y1 - y0),
        j_size=(z1 - z0),
    )


def build_sym_plane_interior(z_range: tuple[float, float] | None = None) -> pv.PolyData:
    """Cross-section of the pipe interior in the x = 0 plane — union of two
    rectangles (main pipe + branch stub).

    If z_range is given, the main-pipe rectangle is clipped to that range; the
    branch stub is kept only if z_branch lies inside the range.  Use this to
    visualise a short, zoomed segment near the junction instead of the full
    9.2 m pipe.
    """
    R = PIPE["R_main"]
    Rb = PIPE["R_branch"]
    zb = PIPE["z_branch"]
    z_lo = PIPE["z_min"] if z_range is None else max(PIPE["z_min"], z_range[0])
    z_hi = PIPE["z_max"] if z_range is None else min(PIPE["z_max"], z_range[1])
    main_pts = np.array([
        [0.0, -R, z_lo],
        [0.0,  R, z_lo],
        [0.0,  R, z_hi],
        [0.0, -R, z_hi],
    ])
    pts_list = [main_pts]
    faces_list = [np.array([4, 0, 1, 2, 3])]
    if z_range is None or (z_range[0] <= zb <= z_range[1]):
        branch_pts = np.array([
            [0.0, PIPE["branch_y_min"], zb - Rb],
            [0.0, PIPE["branch_y_max"], zb - Rb],
            [0.0, PIPE["branch_y_max"], zb + Rb],
            [0.0, PIPE["branch_y_min"], zb + Rb],
        ])
        pts_list.append(branch_pts)
        faces_list.append(np.array([4, 4, 5, 6, 7]))
    pts = np.vstack(pts_list)
    faces = np.concatenate(faces_list)
    return pv.PolyData(pts, faces)


def add_patches(p, stls, *, half=False, show_sym=False, wall_opacity=0.25,
                sym_z_range: tuple[float, float] | None = None,
                clip_to_z_range: bool = False):
    for name, surf in stls.items():
        if half:
            surf = surf.clip(normal="x", origin=(0.0, 0.0, 0.0), invert=False)
        if clip_to_z_range and sym_z_range is not None:
            surf = surf.clip(normal="z", origin=(0, 0, sym_z_range[0]), invert=False)
            surf = surf.clip(normal="z", origin=(0, 0, sym_z_range[1]), invert=True)
            if surf.n_points == 0:
                continue
        is_wall = name == "wall"
        p.add_mesh(
            surf,
            color=PATCH_COLORS[name],
            opacity=wall_opacity if is_wall else 0.95,
            show_edges=not is_wall,
            edge_color="black",
            line_width=0.25,
        )
    if show_sym:
        interior = build_sym_plane_interior(sym_z_range)
        p.add_mesh(
            interior,
            color=SYM_COLOR,
            opacity=0.75,
            show_edges=True,
            edge_color="#b7950b",
            line_width=2.0,
            lighting=False,
        )


def add_legend(p, labels):
    p.add_legend(
        labels=labels,
        bcolor="white",
        border=True,
        size=(0.18, 0.18),
        loc="upper right",
        face="rectangle",
    )


def add_text(p, txt, pos=(0.01, 0.94)):
    p.add_text(txt, font_size=12, color="black", position=pos, viewport=True)


# Panel A — full pipe view from -x slightly above, so the yellow sym-plane
# (at x = 0) cuts through the pipe longitudinally from the viewer's side.
CAM_ISO = [(-5.5, 3.0, -3.5), (0.0, 0.35, 4.6), (0.0, 1.0, 0.0)]

# Panels B and C zoom into a +- 1 m window around the junction (z = 3.6 - 5.6)
# where the 3 D geometry is visible.  The full 9.2 m pipe is too slender to
# interpret at iso angles.
Z_ZOOM = (3.6, 5.6)

# Panel B — iso view of the junction from +x +y looking back at (0, 0, 4.6).
# Wall opaque; sym plane (yellow) visible where the half-pipe is open.
CAM_HALF_ISO = [(2.2, 1.4, 5.8), (0.0, 0.35, 4.6), (0.0, 1.0, 0.0)]

# Panel C — end-on view from +x along the x-axis, centred on the junction.
CAM_END_ON = [(3.0, 0.35, 4.6), (0.0, 0.35, 4.6), (0.0, 1.0, 0.0)]


def panel_A_full_with_sym(stls, plotter):
    sym = build_sym_plane_full()
    add_patches(plotter, stls, half=False, show_sym=False, wall_opacity=0.18)
    plotter.add_mesh(
        sym,
        color=SYM_COLOR,
        opacity=0.30,
        show_edges=True,
        edge_color="#b7950b",
        line_width=1.5,
    )
    plotter.camera_position = CAM_ISO
    plotter.camera.zoom(1.25)
    add_text(plotter,
             "A. Full geometry + symmetry plane (yellow) at x = 0")


def panel_B_half_domain(stls, plotter):
    add_patches(plotter, stls, half=True, show_sym=True, wall_opacity=0.92,
                sym_z_range=Z_ZOOM, clip_to_z_range=True)
    plotter.camera_position = CAM_HALF_ISO
    plotter.camera.zoom(1.05)
    plotter.add_axes(color="black", line_width=2)
    add_text(plotter,
             "B. Half-domain (x >= 0).  Yellow = symmetryPlane BC")


def panel_C_end_on(stls, plotter):
    # Clean cross-section of the interior at x = 0, windowed around the junction.
    interior = build_sym_plane_interior(Z_ZOOM)
    plotter.add_mesh(interior, color=SYM_COLOR, opacity=0.95,
                     show_edges=True, edge_color="#b7950b", line_width=3.0,
                     lighting=False)
    R = PIPE["R_main"]
    Rb = PIPE["R_branch"]
    zb = PIPE["z_branch"]
    # Pipe centreline on the cross-section
    cl = pv.Line([0, 0, Z_ZOOM[0]], [0, 0, Z_ZOOM[1]])
    plotter.add_mesh(cl, color="#2c3e50", line_width=1.5, style="wireframe")
    plotter.add_point_labels(
        np.array([
            [0,  R + 0.08, zb - 0.7],
            [0, PIPE["branch_y_max"] + 0.08, zb + 0.05],
            [0,  0.0, zb + 0.03],
        ]),
        [
            f"D (main) = {2*R*1000:.0f} mm",
            f"d (branch) = {2*Rb*1000:.0f} mm",
            "centreline (x = y = 0)",
        ],
        font_size=14, text_color="black", shape=None, always_visible=True,
        point_size=0, show_points=False,
    )
    plotter.camera_position = CAM_END_ON
    plotter.camera.zoom(1.1)
    plotter.add_axes(color="black", line_width=2)
    add_text(plotter,
             "C. symmetryPlane face itself (end-on view)")


def panel_D_savings(plotter):
    plotter.set_background("white")
    text = (
        "Current medium, full domain .............. 953 k cells\n"
        "  + R2  (shorten upstream to 5 D) ...........  -143 k\n"
        "  + R1-lite  (level-1 cyl z = 4.9 - 6.5 m) ... +188 k\n"
        "  + SYMMETRY PLANE at x = 0  .................  -478 k\n"
        "  + non-uniform blockMesh in z ...............  -34 k\n"
        "  -------------------------------------------------\n"
        "                              Total  ~= 486 k cells\n\n"
        "Wall time per case:   ~5.5 h   --->   ~2.6 h\n"
        "Over 10 DoE cases:    ~27 h of wall time saved\n\n"
        "Reference:   Sakowitz, Mihaescu & Fuchs,\n"
        "IJHFF 45 (2014) 135  -  documents validity of\n"
        "x = 0 symmetry plane for 90-deg T-junction RANS."
    )
    plotter.add_text(text, font_size=12, color="black",
                     position=(0.04, 0.20), viewport=True, font="courier")
    plotter.add_text("D. Mesh savings from this change",
                     font_size=13, color="black",
                     position=(0.01, 0.94), viewport=True)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    case = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    stls = load_stls(case)
    if not stls:
        raise SystemExit(f"No STL patches in {case / 'constant' / 'triSurface'}")
    print(f"Loaded patches: {list(stls)}")

    p = pv.Plotter(off_screen=True, shape=(2, 2), window_size=(2000, 1200),
                   border=True, border_color="#555555")
    p.set_background("white")

    p.subplot(0, 0); panel_A_full_with_sym(stls, p)
    p.subplot(0, 1); panel_B_half_domain(stls, p)
    p.subplot(1, 0); panel_C_end_on(stls, p)
    p.subplot(1, 1); panel_D_savings(p)

    p.screenshot(str(out), transparent_background=False)
    print(f"Wrote {out}  ({out.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
