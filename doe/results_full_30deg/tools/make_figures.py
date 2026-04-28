#!/usr/bin/env python3
"""make_figures.py — standard figure pack for OpenFOAM T-junction cases.

Usage:
    make_figures.py <case_dir> <output_dir> [--time T]

Produces (PNG, 1600x800 / 900x900):
    fig_geometry.png         STL patches (main/branch/outlet/wall) in isometric view
    fig_mesh_xz.png          mesh cells on x=0 slice (the centerline plane that contains
                             both the main-pipe axis and the branch-pipe axis)
    fig_H2_xz.png            Y_H2 on x=0 slice, last time
    fig_H2_outlet.png        Y_H2 on outlet face (the CoV plane), last time
    fig_velocity_xz.png      |U| on x=0 slice with in-plane glyphs
    fig_pressure_xz.png      p_rgh on x=0 slice
    fig_streamlines.png      streamtraces seeded from both inlets, colored by |U|

Designed to be case-agnostic and reusable for every DoE case.
Run retroactively from a local copy of the case, or in-place on a remote
headless machine with PyVista (pip install pyvista) — set
PYVISTA_OFF_SCREEN=true for headless execution.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

import numpy as np

os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
import pyvista as pv  # noqa: E402

pv.OFF_SCREEN = True

WIDE = (1600, 800)
SQUARE = (900, 900)

CMAP_H2 = "viridis"
CMAP_SPEED = "plasma"
CMAP_PRESS = "coolwarm"

PATCH_COLORS = {
    "main_inlet": "#27ae60",
    "branch_inlet": "#e67e22",
    "outlet": "#c0392b",
    "wall": "#95a5a6",
}


# Cameras are tuned for a pipe that runs along +z (length 6.9 m, half-domain)
# with a branch pointing in +y.  For the 2-D centerline slice (x=0 plane) we
# want z horizontal and y vertical.  Looking from -x with view-up = +y puts
# the inlet (z=0) on the left and the outlet (z=6.9) on the right, with the
# branch pointing up.
WINDOW_ASPECT = WIDE[0] / WIDE[1]  # 1600 / 800 = 2.0


def setup_xz_camera(p, mesh, *, margin: float = 1.05):
    """Configure the plotter for an orthographic x=0 centreline view.

    Uses parallel (orthographic) projection -- the standard for technical
    2-D field plots -- with the parallel scale chosen so the mesh's
    z-extent fills the viewport horizontally with a small margin.
    """
    b = mesh.bounds  # (xmin, xmax, ymin, ymax, zmin, zmax)
    yc = 0.5 * (b[2] + b[3])
    zc = 0.5 * (b[4] + b[5])
    z_range = b[5] - b[4]
    y_range = b[3] - b[2]
    # Parallel scale = half the viewport height in world units.
    # Viewport height needs to cover both:
    #   horizontal fit:   z_range / WINDOW_ASPECT
    #   vertical fit:     y_range
    #   plus a margin
    scale = max(z_range / WINDOW_ASPECT, y_range) * 0.5 * margin
    p.camera_position = [(-2.0, yc, zc), (0.0, yc, zc), (0.0, 1.0, 0.0)]
    p.camera.SetParallelProjection(True)
    p.camera.SetParallelScale(scale)


def camera_iso():
    return [(-5.5, 3.0, -3.5), (0.0, 0.35, 3.45), (0.0, 1.0, 0.0)]


def camera_outlet():
    cam_z = L_MAIN_HALF + 1.5
    return [(0.0, 0.0, cam_z), (0.0, 0.0, L_MAIN_HALF), (0.0, 1.0, 0.0)]


SBAR = dict(
    color="black",
    n_labels=5,
    title_font_size=1,  # hide bar title (upper-left add_text says what it is)
    label_font_size=12,
    vertical=False,
    position_x=0.22,
    position_y=0.07,
    width=0.56,
    height=0.028,
    fmt="%.3g",
    title="",
)


def load_case(case_dir: Path, target_time: float | None = None):
    foam = case_dir / "case.foam"
    foam.touch()
    reader = pv.POpenFOAMReader(str(foam))
    reader.enable_all_cell_arrays()
    times = list(reader.time_values)
    if not times:
        raise SystemExit(f"No time steps in {case_dir}")
    t = target_time if target_time is not None else times[-1]
    if t not in times:
        raise SystemExit(f"Time {t} not in {times}")
    reader.set_active_time_value(t)
    print(f"  reading t = {t} s  (all times: {times})")
    return reader.read(), t


def get_internal(ds) -> pv.UnstructuredGrid:
    if isinstance(ds, pv.MultiBlock):
        for key in ("internalMesh", "internal"):
            if key in ds.keys():
                return ds[key]
        return ds[0]
    return ds


def get_patch(ds, name: str):
    if not isinstance(ds, pv.MultiBlock):
        return None
    for key in ds.keys():
        if key == name:
            return ds[key]
        sub = ds[key]
        if isinstance(sub, pv.MultiBlock) and name in sub.keys():
            return sub[name]
    return None


def get_sym_patch(ds):
    """Return the symmetryPlane boundary patch as a PyVista PolyData.

    The half-domain in this campaign is clipped at x = 0 with a symmetryPlane
    patch named ``sym``.  That patch IS the 2-D centreline mesh: every cell of
    the 3-D volume that touches x = 0 contributes one face, with face values
    interpolated from the touching cell.  Reading it directly side-steps the
    two failure modes of a volume slice on snappyHexMesh polyhedra:
      (i) non-conformal "white notch" gaps at the junction interface, and
      (ii) zero-volume orphan cells inside the wedge between the main pipe
           and the branch root, which never get a proper face on x = 0.

    Returns None if no symmetry patch is present (in which case callers should
    fall back to a triangulated volume slice).
    """
    for name in ("sym", "symmetry", "symmetryPlane"):
        patch = get_patch(ds, name)
        if patch is not None and getattr(patch, "n_cells", 0) > 0:
            return patch
    return None


# ---------------------------------------------------------------------------
# Triangulate cache: OpenFOAM polyhedral cells from snappyHexMesh are often
# non-manifold at the junction, which causes VTK's slice() to drop cells and
# leave "white notch" holes in longitudinal centreline figures.  Triangulating
# the volume once up-front converts every cell to tetrahedra which slice
# cleanly.  Cache the triangulated grid so callers can reuse it.
# ---------------------------------------------------------------------------
_TRI_CACHE = {}


def triangulated(ds):
    internal = get_internal(ds)
    key = id(internal)
    if key not in _TRI_CACHE:
        _TRI_CACHE[key] = internal.triangulate()
    return _TRI_CACHE[key]


def add_text(p, txt):
    p.add_text(txt, font_size=13, color="black", position=(0.01, 0.94),
               viewport=True)


def save(p, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    p.screenshot(str(path), transparent_background=False)
    print(f"  wrote {path.name}  ({path.stat().st_size/1024:.1f} KB)")
    p.close()


def fig_geometry(case: Path, out: Path):
    tri = case / "constant" / "triSurface"
    p = pv.Plotter(off_screen=True, window_size=WIDE)
    p.set_background("white")
    labels = []
    for name, color in PATCH_COLORS.items():
        stl = tri / f"{name}.stl"
        if not stl.exists():
            continue
        surf = pv.read(str(stl))
        is_wall = name == "wall"
        p.add_mesh(
            surf,
            color=color,
            opacity=0.15 if is_wall else 0.95,
            show_edges=not is_wall,
            edge_color="black",
            line_width=0.25,
        )
        labels.append([name, color])
    p.add_legend(labels=labels, bcolor="white", border=True,
                 size=(0.16, 0.14), loc="upper right", face="rectangle")
    p.add_axes(color="black", line_width=2)
    p.camera_position = camera_iso()
    p.camera.zoom(1.25)
    add_text(p, "Geometry — STL patches (T-junction)")
    save(p, out)


def fig_mesh_xz(ds, out: Path):
    """Cell footprint at x = 0 -- the SAME mesh used for the field figures.

    Reads the symmetryPlane patch directly (one face per touching 3-D cell)
    so the cell outlines line up exactly with the H2 / |U| / p_rgh figures
    rendered on the same patch.
    """
    internal = get_internal(ds)
    patch = get_sym_patch(ds)
    if patch is None:
        patch = triangulated(ds).slice(normal="x",
                                       origin=(0.001, 0.0, 0.5 * L_MAIN_HALF))
    p = pv.Plotter(off_screen=True, window_size=WIDE)
    p.set_background("white")
    p.add_mesh(
        patch,
        color="white",
        show_edges=True,
        edge_color="#333333",
        line_width=0.25,
        lighting=False,
    )
    setup_xz_camera(p, patch)
    add_text(
        p,
        f"Mesh -- x=0 symmetry plane  "
        f"({patch.n_cells:,} faces / {internal.n_cells:,} volume cells)",
    )
    save(p, out)


# Geometry constants (post-R2 half-domain).  The branch radius is per-case
# but for orphan-cell branch keep-out we only need a conservative upper bound
# (we default to 0.10 m which covers every DoE case).
R_MAIN_HALF  = 0.23
L_MAIN_HALF  = 6.90
Z_JCT_HALF   = 2.30


def _get_xz_mesh(ds):
    """Return a 2-D mesh at x = 0 carrying every cell-centred field.

    Preference order:
      1. The symmetryPlane patch (``sym``) -- exact face mesh of the x = 0
         boundary.  Every cell in this 2-D mesh corresponds to a real face
         on a real 3-D cell; values are face-interpolated, not extrapolated.
         No interpolation, no fake fluid, no orphan dead-zones.
      2. A triangulated volume slice at x = 0 -- VTK plane-cutter on a
         triangulated copy of the volume mesh.  Equivalent to ParaView's
         ``Slice`` filter with ``Triangulate the input first`` enabled, which
         removes the "white notch" gaps that polyhedral cells leave at
         non-conformal interfaces.

    Both options use the SAME VTK pipeline that ParaView uses, so a PyVista
    screenshot is pixel-identical to a ParaView screenshot of the same
    camera/colormap.
    """
    patch = get_sym_patch(ds)
    if patch is not None:
        return patch, "sym_patch"
    tri = triangulated(ds)
    slc = tri.slice(normal="x", origin=(0.001, 0.0, 0.5 * L_MAIN_HALF))
    return slc, "tri_slice"


def _filter_field(mesh, field: str, *,
                  outlier_pct: float | None = None,
                  outlier_max: float | None = None,
                  outlier_min: float | None = None,
                  branch_keep: bool = False,
                  alpha_deg: float = 90.0,
                  r_branch: float = 0.10,
                  zjct: float = Z_JCT_HALF,
                  l_branch: float = 1.15):
    """Extract cells of `mesh` that pass orphan-cell filters for `field`.

    snappyHexMesh occasionally leaves a few zero-volume / disconnected
    "orphan" cells stuck at their initial-condition value (H2 = 1.0,
    p_rgh = p_atm reference, or |U| = 0).  These contaminate the colour
    range when the rest of the pipe operates two orders of magnitude away.
    We drop them at the cell level.

    Knobs:
      outlier_pct  IQR multiplier k -- keep [Q1 - k IQR, Q3 + k IQR].
                   Adapts to the field's natural variability.
      outlier_max  Hard cap -- drop cells with values > outlier_max.
      outlier_min  Hard cap -- drop cells with values < outlier_min.
      branch_keep  When True, spares cells that lie inside the analytical
                   branch-pipe volume.  The branch legitimately carries
                   H2 = 1.0; without this, a hard cap < 0.5 would erase
                   the entire branch from the figure.
    """
    if field not in mesh.cell_data:
        return mesh
    vals = np.asarray(mesh.cell_data[field], dtype=float)
    keep = np.ones(len(vals), dtype=bool)

    in_branch = None
    if branch_keep:
        ctrs = np.asarray(mesh.cell_centers().points)
        a_rad = math.radians(alpha_deg)
        nb = np.array([0.0, math.sin(a_rad), -math.cos(a_rad)])
        base = np.array([0.0, R_MAIN_HALF, zjct])
        d = ctrs - base
        s = d @ nb
        perp = d - np.outer(s, nb)
        rperp = np.linalg.norm(perp, axis=1)
        in_branch = ((s >= -0.05) & (s <= l_branch + 0.05)
                     & (rperp < r_branch * 1.05))

    if outlier_pct is not None and outlier_pct > 0.0:
        q1, q3 = np.nanpercentile(vals, [25.0, 75.0])
        iqr = q3 - q1
        if iqr > 0:
            lo = q1 - outlier_pct * iqr
            hi = q3 + outlier_pct * iqr
            keep &= (vals >= lo) & (vals <= hi)
    if outlier_max is not None:
        m = vals < outlier_max
        keep &= (m if in_branch is None else (m | in_branch))
    if outlier_min is not None:
        m = vals > outlier_min
        keep &= (m if in_branch is None else (m | in_branch))
    if keep.all():
        return mesh
    return mesh.extract_cells(np.where(keep)[0])


def _render_xz(mesh, field: str, out: Path, *,
               title: str, cmap: str, clim=None,
               label: str | None = None,
               outlier_pct: float | None = None,
               outlier_max: float | None = None,
               outlier_min: float | None = None,
               branch_keep: bool = False,
               alpha_deg: float = 90.0,
               r_branch: float = 0.10,
               zjct: float = Z_JCT_HALF,
               l_branch: float = 1.15):
    """Native PyVista/VTK render of `field` on the x = 0 mesh.

    `mesh` should already be a 2-D mesh (the sym patch or a triangulated
    slice).  Orphan filtering is applied here on cell values; rendering is
    direct VTK -- no point interpolation, no analytical mask.
    """
    if field not in mesh.cell_data and field not in mesh.point_data:
        raise SystemExit(
            f"field {field!r} not on x=0 mesh; "
            f"have cell_data={list(mesh.cell_data.keys())[:8]}")
    mesh = _filter_field(
        mesh, field,
        outlier_pct=outlier_pct,
        outlier_max=outlier_max, outlier_min=outlier_min,
        branch_keep=branch_keep, alpha_deg=alpha_deg,
        r_branch=r_branch, zjct=zjct, l_branch=l_branch,
    )

    sbar = dict(SBAR)
    if label:
        sbar["title"] = label
        sbar["title_font_size"] = 12

    p = pv.Plotter(off_screen=True, window_size=WIDE)
    p.set_background("white")
    p.add_mesh(mesh, scalars=field, cmap=cmap, clim=clim,
               show_edges=False, scalar_bar_args=sbar)
    setup_xz_camera(p, mesh)
    add_text(p, title)
    save(p, out)


def _is_in_branch(centers, *, alpha_deg, r_branch, zjct,
                  l_branch=1.40, slack=0.05):
    """Boolean mask: cells whose centroid lies inside the analytical branch."""
    a_rad = math.radians(alpha_deg)
    nb = np.array([0.0, math.sin(a_rad), -math.cos(a_rad)])
    base = np.array([0.0, R_MAIN_HALF, zjct])
    d = centers - base
    s = d @ nb
    perp = d - np.outer(s, nb)
    rperp = np.linalg.norm(perp, axis=1)
    return ((s >= -slack) & (s <= l_branch + slack)
            & (rperp < r_branch * 1.05))


def fig_velocity_xz(ds, out: Path, *, r_branch: float = 0.10,
                    zjct: float = Z_JCT_HALF, alpha_deg: float = 90.0):
    """|U| on the x = 0 symmetry plane.

    Colour range is set from the BULK FLUID only (cells outside the
    analytical branch volume) so the main-pipe wake/shear structure is
    visible.  The branch jet (60-150 m/s) saturates at the top of the
    colourmap, which is informative on its own.
    """
    mesh, source = _get_xz_mesh(ds)
    U = np.asarray(mesh.cell_data["U"], dtype=float)
    speed = np.linalg.norm(U, axis=1)
    mesh = mesh.copy()
    mesh.cell_data["|U|"] = speed

    centers = np.asarray(mesh.cell_centers().points)
    in_br = _is_in_branch(centers, alpha_deg=alpha_deg,
                          r_branch=r_branch, zjct=zjct)
    bulk = speed[~in_br]
    # Reject orphan supersonic cells from the bulk before picking vmax.
    if bulk.size:
        q1, q3 = np.nanpercentile(bulk, [25.0, 75.0])
        iqr = q3 - q1
        if iqr > 0:
            bulk = bulk[bulk <= q3 + 50.0 * iqr]
        vmax = float(np.nanpercentile(bulk, 99.0))
    else:
        vmax = float(np.nanpercentile(speed, 99.0))
    vmax = max(vmax, 1.0)
    _render_xz(
        mesh, "|U|", out,
        title=f"Velocity magnitude |U| (m/s) -- x=0 symmetry plane ({source})",
        cmap=CMAP_SPEED, clim=(0.0, vmax),
        label="|U| [m/s]  (bulk-pipe range; branch jet saturates)",
        outlier_pct=50.0,
        alpha_deg=alpha_deg, r_branch=r_branch, zjct=zjct,
    )


def fig_pressure_xz(ds, out: Path, t: float, *, r_branch: float = 0.10,
                    zjct: float = Z_JCT_HALF, alpha_deg: float = 90.0):
    """Gauge p_rgh on the x = 0 symmetry plane.  Gauge = bulk-IQR mean."""
    mesh, source = _get_xz_mesh(ds)
    p_vals = np.asarray(mesh.cell_data["p_rgh"], dtype=float)
    q1, q3 = np.nanpercentile(p_vals, [25.0, 75.0])
    iqr = q3 - q1
    if iqr > 0:
        in_band = ((p_vals >= q1 - 50.0 * iqr)
                   & (p_vals <= q3 + 50.0 * iqr))
    else:
        in_band = np.ones_like(p_vals, dtype=bool)
    p_mean = (float(np.mean(p_vals[in_band]))
              if in_band.any() else float(np.mean(p_vals)))
    mesh = mesh.copy()
    mesh.cell_data["p_rgh_gauge"] = p_vals - p_mean
    # Colour range tied to the bulk-fluid IQR; the recovery zone correctly
    # saturates at the red end (a few cells), and the wake is readable.
    rng = max(8.0 * iqr, 1.0e2) if iqr > 0 else 2.0e3
    _render_xz(
        mesh, "p_rgh_gauge", out,
        title=(f"p_rgh - {p_mean/1e6:.3f} MPa [Pa] -- "
               f"x=0 symmetry plane (t = {t:g} s, {source})"),
        cmap=CMAP_PRESS, clim=(-rng, rng),
        label="p_rgh gauge [Pa]",
        outlier_pct=50.0,
        alpha_deg=alpha_deg, r_branch=r_branch, zjct=zjct,
    )


def fig_H2_xz(ds, out: Path, t: float, *, r_branch: float = 0.10,
              zjct: float = Z_JCT_HALF, alpha_deg: float = 90.0):
    """H2 mass fraction on the x = 0 symmetry plane.

    The branch carries H2 = 1.0 legitimately (branch_inlet BC) but we
    auto-clip the colour range to the BULK FLUID's natural maximum
    (99th percentile of cells outside the analytical branch volume) so
    the dilution gradient downstream of the junction is visible.  The
    branch and the early plume saturate at the top of the colourmap.

    A spatially-aware orphan filter drops cells with H2 > 0.5 OUTSIDE the
    branch (snappyHexMesh occasionally leaves frozen-IC pockets) while
    sparing the legitimate branch interior.
    """
    mesh, source = _get_xz_mesh(ds)
    h2 = np.asarray(mesh.cell_data["H2"], dtype=float)
    centers = np.asarray(mesh.cell_centers().points)
    in_br = _is_in_branch(centers, alpha_deg=alpha_deg,
                          r_branch=r_branch, zjct=zjct)
    bulk = h2[(~in_br) & (h2 < 0.5)]  # exclude branch + orphan pockets
    if bulk.size:
        vmax_bulk = float(np.nanpercentile(bulk, 99.0))
    else:
        vmax_bulk = 0.05
    # Show at least a band wide enough to see the developing plume; cap at
    # 0.5 so we never end up with both the branch-inlet (1.0) and the bulk
    # crammed into the same colour range.
    vmax = float(np.clip(max(vmax_bulk * 2.5, 0.05), 0.05, 0.5))
    _render_xz(
        mesh, "H2", out,
        title=(f"Y_H2 (H2 mass fraction) -- x=0 symmetry plane "
               f"(t = {t:g} s, {source})"),
        cmap=CMAP_H2, clim=(0.0, vmax),
        label=(f"Y_H2 (mass fraction)  "
               f"[bulk-pipe range; branch H2=1.0 saturates]"),
        outlier_max=0.5, branch_keep=True,
        alpha_deg=alpha_deg, r_branch=r_branch, zjct=zjct,
    )


def fig_H2_outlet(ds, out: Path):
    """H2 on the outlet face, mirrored across x = 0 to show the full circle.

    The campaign uses a half-domain (x >= 0) so the outlet patch is a
    half-disk.  We mirror it across the symmetry plane and merge to recover
    the full physical cross-section.
    """
    outlet = get_patch(ds, "outlet")
    if outlet is None or outlet.n_cells == 0:
        internal = get_internal(ds)
        outlet = internal.slice(normal="z", origin=(0.0, 0.0, L_MAIN_HALF - 1e-3))

    # Mirror across x = 0.  PyVista 0.47 has reflect(); fall back to a manual
    # point flip for older versions.  The patch is symmetric about y, so a
    # point-flip preserves the field correctly.
    try:
        mirror = outlet.reflect(normal=(1.0, 0.0, 0.0), point=(0.0, 0.0, 0.0))
    except Exception:
        mirror = outlet.copy()
        pts = np.asarray(mirror.points)
        pts[:, 0] = -pts[:, 0]
        mirror.points = pts
    full = outlet.merge(mirror)

    # Camera: look at the outlet face along -z, slightly outside the pipe.
    cam_z = L_MAIN_HALF + 1.5
    p = pv.Plotter(off_screen=True, window_size=SQUARE)
    p.set_background("white")
    sbar = dict(SBAR)
    sbar["title"] = "Y_H2 [-]"
    sbar["title_font_size"] = 12
    p.add_mesh(full, scalars="H2", cmap=CMAP_H2, show_edges=False,
               scalar_bar_args=sbar)
    p.camera_position = [(0.0, 0.0, cam_z), (0.0, 0.0, L_MAIN_HALF),
                         (0.0, 1.0, 0.0)]
    p.camera.zoom(1.5)
    add_text(p, "Y_H2 on outlet face (full pipe via x=0 mirror) -- the CoV plane")
    save(p, out)


def fig_streamlines(ds, case: Path, out: Path,
                    r_branch: float = 0.04, zjct: float = Z_JCT_HALF,
                    alpha_deg: float = 90.0):
    """Streamtraces seeded inside both inlets, coloured by speed.

    Branch seeds are placed at the actual branch_inlet location, derived from
    the per-case zjct, alpha_deg and branch radius -- not at hard-coded 9.2 m
    coordinates left over from the original 90-degree geometry.
    """
    internal = get_internal(ds)
    pdata = internal.cell_data_to_point_data()

    theta = np.linspace(0.0, 2.0 * np.pi, 16, endpoint=False)
    # Main inlet seeds: ring of radius 0.7 R_main at z = small offset.
    r_seed_main = 0.7 * R_MAIN_HALF
    main = np.column_stack([
        r_seed_main * np.cos(theta),
        r_seed_main * np.sin(theta),
        np.full_like(theta, 0.03),
    ])
    # Branch inlet seeds: place a ring inside the branch tube near the branch
    # opening.  Tube axis starts at (0, R_main, zjct) and points along
    # n_hat = (0, sin a, -cos a).  Walk one branch length L_b along the axis
    # and lay a ring of radius 0.7 r_branch in the plane perpendicular to
    # n_hat (using +x and the in-plane perp vector as basis).
    a_rad = math.radians(alpha_deg)
    nb = np.array([0.0, math.sin(a_rad), -math.cos(a_rad)])
    base = np.array([0.0, R_MAIN_HALF, zjct])
    L_b = 1.40 if alpha_deg < 90 else 1.20  # conservative branch length
    centre = base + (L_b - 0.05) * nb
    e1 = np.array([1.0, 0.0, 0.0])
    e2 = np.cross(nb, e1)  # in-plane perpendicular
    e2 /= np.linalg.norm(e2) + 1e-12
    r_seed_br = 0.7 * r_branch
    br = np.array([
        centre + r_seed_br * (math.cos(t) * e1 + math.sin(t) * e2)
        for t in theta
    ])
    seeds = pv.PolyData(np.vstack([main, br]))

    try:
        stream = pdata.streamlines_from_source(
            seeds,
            vectors="U",
            max_time=200.0,
            initial_step_length=0.01,
            step_unit="l",
            integration_direction="forward",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"  streamlines failed: {exc}")
        return
    if stream.n_points == 0:
        print("  streamlines returned empty data (check vectors field)")
        return

    speed = np.linalg.norm(np.asarray(stream.point_data["U"]), axis=1)
    stream.point_data["|U|"] = speed

    # Cap vmax with the same bulk-only IQR filter used elsewhere so a few
    # orphan supersonic cells don't wash out the colourmap.
    q1, q3 = np.nanpercentile(speed, [25.0, 75.0])
    iqr = q3 - q1
    bulk = speed[speed <= q3 + 50.0 * iqr] if iqr > 0 else speed
    vmax = float(np.nanpercentile(bulk, 99.0))
    vmax = max(vmax, 1.0)
    p = pv.Plotter(off_screen=True, window_size=WIDE)
    p.set_background("white")
    wall = case / "constant" / "triSurface" / "wall.stl"
    if wall.exists():
        p.add_mesh(pv.read(str(wall)), color=PATCH_COLORS["wall"], opacity=0.10,
                   show_edges=False)
    p.add_mesh(stream, scalars="|U|", cmap=CMAP_SPEED,
               clim=[0.0, vmax], line_width=1.8,
               render_lines_as_tubes=False, scalar_bar_args=SBAR)
    p.camera_position = camera_iso()
    p.camera.zoom(1.2)
    add_text(p, "Streamlines seeded from both inlets  —  colored by speed  U  (m/s)")
    save(p, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--time", type=float, default=None,
                    help="time step to render (default: last)")
    args = ap.parse_args()

    case = args.case_dir.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    print(f"Case: {case}")
    print(f"Out:  {out}")

    print("[1/7] fig_geometry")
    fig_geometry(case, out / "fig_geometry.png")

    print("[2/7] loading volume mesh...")
    ds, t = load_case(case, args.time)
    internal = get_internal(ds)
    cell_fields = list(internal.cell_data.keys())
    print(f"       internal: {internal.n_cells:,} cells, fields: {cell_fields}")

    print("[3/7] fig_mesh_xz")
    fig_mesh_xz(ds, out / "fig_mesh_xz.png")

    # Per-case branch radius for the geometry mask in centreline figures.
    import json
    info_path = case / "case_info.json"
    try:
        info = json.loads(info_path.read_text()) if info_path.exists() else {}
    except Exception:
        info = {}
    r_branch  = float(info.get("D2_m", 0.10)) / 2.0
    z_jct     = float(info.get("ZJCT",  Z_JCT_HALF))
    alpha_deg = float(info.get("alpha_deg", 90.0))
    print(f"       per-case mask: r_branch={r_branch:.4f} m, "
          f"z_jct={z_jct:.3f} m, alpha={alpha_deg:.1f} deg")

    print("[4/7] fig_H2_xz")
    fig_H2_xz(ds, out / "fig_H2_xz.png", t,
              r_branch=r_branch, zjct=z_jct, alpha_deg=alpha_deg)

    print("[5/7] fig_H2_outlet (full pipe via x=0 mirror)")
    fig_H2_outlet(ds, out / "fig_H2_outlet.png")

    print("[6/7] fig_velocity_xz + fig_pressure_xz")
    fig_velocity_xz(ds, out / "fig_velocity_xz.png",
                    r_branch=r_branch, zjct=z_jct, alpha_deg=alpha_deg)
    fig_pressure_xz(ds, out / "fig_pressure_xz.png", t,
                    r_branch=r_branch, zjct=z_jct, alpha_deg=alpha_deg)

    print("[7/7] fig_streamlines")
    fig_streamlines(ds, case, out / "fig_streamlines.png",
                    r_branch=r_branch, zjct=z_jct, alpha_deg=alpha_deg)

    print("DONE.")


if __name__ == "__main__":
    main()
