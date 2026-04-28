#!/usr/bin/env python3
"""make_figures.py -- standard figure pack for OpenFOAM T-junction cases.

Same look-and-feel as the 90 deg pack (matplotlib + kNN interpolation onto a
regular image grid -- smooth gradients, tight bulk-only colour ranges,
white-background matplotlib axes with units), upgraded to be angle-aware so
the same script renders 30 / 90 / 150 deg cases identically.

Produces (PNG, 1600x800 / 900x900):
    fig_geometry.png         STL patches in isometric view, with axes triad + legend
    fig_mesh_xz.png          mesh cells on x=0 slice (cell edges, no fill)
    fig_H2_xz.png            Y_H2 on x=0 slice with bulk-pipe colour range
    fig_H2_outlet.png        Y_H2 on outlet face, mirrored across x=0 to a full
                             physical circle, point-interpolated for a smooth gradient
    fig_velocity_xz.png      |U| on x=0 slice with bulk-pipe colour range
    fig_pressure_xz.png      p_rgh gauge on x=0 slice, bulk-IQR colour range
    fig_streamlines.png      streamtraces seeded from both inlets, colored by speed

The centreline figures (`_render_centerline_interp`) use 1-NN interpolation
from cell centres onto a 520x1400 (Y, Z) image grid and an analytical
geometry mask for clean pipe walls.  The branch is described by its axis
direction nb = (0, sin(alpha), -cos(alpha)) so that for any injection angle
the same algebra puts the tilted branch tube in the right place.

Run with:
    python tools/make_figures.py <case_dir> <out_dir> [--time T]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
import pyvista as pv  # noqa: E402

pv.OFF_SCREEN = True

WIDE   = (1600, 800)
SQUARE = (900, 900)

CMAP_H2     = "viridis"
CMAP_SPEED  = "plasma"
CMAP_PRESS  = "coolwarm"

PATCH_COLORS = {
    "main_inlet":   "#27ae60",
    "branch_inlet": "#e67e22",
    "outlet":       "#c0392b",
    "wall":         "#95a5a6",
}

# Geometry constants (post-R2 half-domain).  These are for camera framing
# and the analytical mask -- per-case branch radius / junction location come
# from case_info.json at runtime.
R_MAIN_HALF = 0.23
L_MAIN_HALF = 6.90
Z_JCT_HALF  = 2.30


# ---------------------------------------------------------------------------
# Cameras: pipe runs along +z (length 6.9 m half-domain) with the branch
# pointing in +y at angle alpha to the main axis.  For the 2-D centreline
# slice we want z horizontal and y vertical.  The matplotlib renderer uses
# its own axes; only fig_mesh_xz / fig_geometry / fig_streamlines use these.
# ---------------------------------------------------------------------------
def camera_xz_slice():
    return [(-6.0, 0.35, 4.6), (0.0, 0.35, 4.6), (0.0, 1.0, 0.0)]


def camera_iso():
    return [(-5.5, 3.0, -3.5), (0.0, 0.35, 4.6), (0.0, 1.0, 0.0)]


def camera_outlet():
    return [(0.0, 0.0, L_MAIN_HALF + 2.5), (0.0, 0.0, L_MAIN_HALF),
            (0.0, 1.0, 0.0)]


SBAR = dict(
    color="black",
    n_labels=5,
    title_font_size=1,
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


# ---------------------------------------------------------------------------
# Triangulate cache: OpenFOAM polyhedral cells from snappyHexMesh occasionally
# leave non-conformal junction faces, which causes VTK's slice() to drop cells
# and leave "white-notch" gaps in longitudinal centreline figures.  Slicing a
# triangulated copy avoids that.  Cache the triangulation for re-use.
# ---------------------------------------------------------------------------
_TRI_CACHE: dict[int, pv.UnstructuredGrid] = {}


def triangulated(ds):
    internal = get_internal(ds)
    key = id(internal)
    if key not in _TRI_CACHE:
        _TRI_CACHE[key] = internal.triangulate()
    return _TRI_CACHE[key]


def add_text(p, txt):
    p.add_text(txt, font_size=13, color="black",
               position=(0.01, 0.94), viewport=True)


def save(p, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    p.screenshot(str(path), transparent_background=False)
    print(f"  wrote {path.name}  ({path.stat().st_size/1024:.1f} KB)")
    p.close()


# ---------------------------------------------------------------------------
# Angle-aware analytical branch mask
# ---------------------------------------------------------------------------
def _branch_axis(alpha_deg: float):
    """Unit vector pointing along the branch tube axis (away from the main
    pipe wall) in the x=0 plane.  alpha is the injection angle measured
    between the branch and the main-pipe axis (alpha=90 -> straight up;
    alpha=30 -> shallow tilt upstream)."""
    a = math.radians(alpha_deg)
    return math.sin(a), -math.cos(a)   # (n_y, n_z)


def _branch_mask(Y, Z, *, alpha_deg, r_branch, zjct,
                 l_branch=1.55, x_plane=0.005, slack=0.0):
    """Boolean mask of (Y, Z) points that lie inside the analytical branch
    tube.  The branch axis starts at (0, R_main, zjct) and runs in
    direction (0, sin(alpha), -cos(alpha))."""
    nb_y, nb_z = _branch_axis(alpha_deg)
    dy = Y - R_MAIN_HALF
    dz = Z - zjct
    s   = dy * nb_y + dz * nb_z                    # arc-length along axis
    perp_y = dy - s * nb_y
    perp_z = dz - s * nb_z
    rperp = np.sqrt(perp_y**2 + perp_z**2 + x_plane**2)
    return (s >= -slack) & (s <= l_branch + slack) & (rperp <= r_branch)


# ---------------------------------------------------------------------------
# Main centreline renderer (matplotlib + kNN, the look the supervisor likes)
# ---------------------------------------------------------------------------
def _orphan_mask_3d(ctrs: np.ndarray, h2_arr: np.ndarray, *,
                    alpha_deg: float, r_branch: float, zjct: float,
                    l_branch: float = 1.55) -> np.ndarray:
    """Boolean orphan-cell mask: cells with H2 > 0.5 that are NOT inside
    the analytical branch tube.  These are snappyHexMesh "frozen-IC"
    cells which contaminate every field (H2, |U|, p_rgh) and dominate
    the 99th-percentile range."""
    nb_y, nb_z = _branch_axis(alpha_deg)
    dy = ctrs[:, 1] - R_MAIN_HALF
    dz = ctrs[:, 2] - zjct
    s = dy * nb_y + dz * nb_z
    perp_y = dy - s * nb_y
    perp_z = dz - s * nb_z
    rperp = np.sqrt(ctrs[:, 0]**2 + perp_y**2 + perp_z**2)
    in_branch_3d = ((s >= -0.05) & (s <= l_branch + 0.05)
                    & (rperp <= r_branch * 1.05))
    return (h2_arr > 0.5) & ~in_branch_3d


def _render_centerline_interp(internal, field: str, out: Path, *,
                              title: str, cmap: str, clim=None,
                              alpha_deg: float = 90.0,
                              r_branch: float = 0.10,
                              zjct: float = Z_JCT_HALF,
                              l_branch: float = 1.55,
                              x_plane: float = 0.005,
                              label: str | None = None,
                              orphan_3d: np.ndarray | None = None):
    """Render a scalar field on the x=0 centreline plane via point-
    interpolation onto a regular Y-Z image grid, masked to the analytical
    pipe shape (main pipe + tilted branch tube).  Eliminates the "white
    notch" slicing artifact at non-orthogonal junctions and gives a smooth
    gradient that's tight on the bulk-fluid range.

    `orphan_3d` is a per-cell boolean array (same length as
    `internal.cell_centers().points`); cells flagged as orphans are masked
    out in the rendered image so a few frozen-IC cells don't contaminate
    the colour map or the gradient.  Build it once via _orphan_mask_3d
    and reuse for every field."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if field not in internal.cell_data:
        raise SystemExit(f"field {field!r} not in internal cell data")

    from scipy.spatial import cKDTree
    global _CTR_CACHE_FIG
    try:
        _CTR_CACHE_FIG
    except NameError:
        _CTR_CACHE_FIG = {}
    key = id(internal)
    if key not in _CTR_CACHE_FIG:
        _CTR_CACHE_FIG[key] = np.asarray(internal.cell_centers().points)
    ctrs = _CTR_CACHE_FIG[key]
    vals = np.asarray(internal.cell_data[field])
    tree = cKDTree(ctrs)

    sa = math.sin(math.radians(alpha_deg))
    y_tip = R_MAIN_HALF + l_branch * sa
    y_lo  = -R_MAIN_HALF - 0.05
    y_hi  = max(y_tip + 0.10, R_MAIN_HALF + 0.30)

    ny, nz = 520, 1400
    y = np.linspace(y_lo, y_hi, ny)
    z = np.linspace(0.0, L_MAIN_HALF, nz)
    Y, Z = np.meshgrid(y, z, indexing="ij")
    X = np.full_like(Y, x_plane)
    qpts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    dist, idx = tree.query(qpts, k=1)
    img = vals[idx].reshape(Y.shape)
    img = np.where(dist.reshape(Y.shape) > 0.04, np.nan, img)

    in_main   = (X**2 + Y**2 < R_MAIN_HALF**2) & (Y <= R_MAIN_HALF)
    in_branch = _branch_mask(Y, Z, alpha_deg=alpha_deg,
                             r_branch=r_branch, zjct=zjct,
                             l_branch=l_branch, x_plane=x_plane)
    geom = in_main | in_branch
    img = np.where(geom & np.isfinite(img), img, np.nan)

    # Mask orphan cells using the 3-D mask propagated through the kNN
    # lookup.  Applies uniformly to H2 / |U| / p_rgh.
    if orphan_3d is not None:
        is_orphan_pixel = orphan_3d[idx].reshape(Y.shape)
        img = np.where(is_orphan_pixel & in_main & ~in_branch,
                       np.nan, img)

    # Belt-and-braces: also mask any obviously-non-physical cell that
    # somehow slipped through the orphan filter (typically only a handful
    # at most after the 3-D filter).
    if field in ("H2", "H2Mean"):
        img = np.where((img > 0.5) & in_main & ~in_branch, np.nan, img)

    # Choose colour range from the bulk-pipe fluid downstream of the
    # junction (|Y| < R_MAIN_HALF, Z > zjct + 0.3) so the dilution
    # gradient and wake/recirculation pattern are the visual focus.  The
    # branch (H2=1) and the high-speed jet automatically saturate at the
    # top of the colourmap.
    if clim is None:
        valid = (in_main
                 & (np.abs(Y) < R_MAIN_HALF)
                 & (Z > zjct + 0.3)
                 & np.isfinite(img))
        if valid.sum() > 0:
            if field == "p_rgh_gauge":
                rng = float(np.nanpercentile(np.abs(img[valid]), 99.0))
                rng = max(rng, 1.0e2)
                clim = (-rng, rng)
            else:
                vmax = float(np.nanpercentile(img[valid], 99.0))
                vmax = max(vmax, 1.0e-6)
                clim = (0.0, vmax)
        else:
            vmax = float(np.nanpercentile(img[np.isfinite(img)], 99.0))
            clim = (0.0, max(vmax, 1.0e-6))

    fig, ax = plt.subplots(figsize=(16, 7))
    img_m = np.ma.array(img, mask=~np.isfinite(img))
    pcm = ax.pcolormesh(Z, Y, img_m, cmap=cmap,
                        vmin=clim[0], vmax=clim[1], shading="auto")
    ax.set_aspect("equal")
    ax.set_xlabel("z [m]")
    ax.set_ylabel("y [m]")
    ax.set_xlim(0.0, L_MAIN_HALF)
    ax.set_ylim(y_lo, y_hi)
    ax.set_title(title)
    cbar = fig.colorbar(pcm, ax=ax, orientation="horizontal",
                        fraction=0.035, pad=0.08)
    cbar.set_label(label or field)
    fig.tight_layout()
    fig.savefig(str(out), dpi=140)
    plt.close(fig)
    print(f"  wrote {out.name}  ({Path(out).stat().st_size/1024:.1f} KB)")


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
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
    add_text(p, "Geometry -- STL patches (T-junction)")
    save(p, out)


def fig_mesh_xz(ds, out: Path):
    internal = get_internal(ds)
    slc = internal.slice(normal="x", origin=(0.001, 0.0, L_MAIN_HALF / 2))
    p = pv.Plotter(off_screen=True, window_size=WIDE)
    p.set_background("white")
    p.add_mesh(
        slc,
        color="white",
        show_edges=True,
        edge_color="#333333",
        line_width=0.25,
        lighting=False,
    )
    p.camera_position = camera_xz_slice()
    p.camera.zoom(1.25)
    add_text(p, f"Mesh -- x=0 slice  ({internal.n_cells:,} cells total)")
    save(p, out)


def fig_H2_outlet(ds, out: Path):
    """Outlet patch coloured by Y_H2, mirrored across x=0 so the figure
    shows the full physical circle, with point-interpolated smooth shading."""
    outlet = get_patch(ds, "outlet")
    if outlet is None or outlet.n_cells == 0:
        internal = get_internal(ds)
        outlet = internal.slice(normal="z", origin=(0, 0, L_MAIN_HALF - 0.01))

    # Convert cell data -> point data so PyVista can interpolate the colour
    # smoothly across each face (instead of flat-shading the cell).
    pdata = outlet.cell_data_to_point_data()

    # Mirror across x=0: reflect the polydata, merge with the original.
    pts = np.asarray(pdata.points)
    mirror_pts = pts.copy()
    mirror_pts[:, 0] = -mirror_pts[:, 0]
    mirror = pdata.copy()
    mirror.points = mirror_pts
    full = pdata.merge(mirror)

    h2_arr = np.asarray(full.point_data.get("H2", full.point_data.get("H2Mean")))
    h2_mean = float(np.nanmean(h2_arr))
    h2_min  = float(np.nanmin(h2_arr))
    h2_max  = float(np.nanmax(h2_arr))

    p = pv.Plotter(off_screen=True, window_size=SQUARE)
    p.set_background("white")
    p.add_mesh(full, scalars="H2" if "H2" in full.point_data else "H2Mean",
               cmap=CMAP_H2, show_edges=False, scalar_bar_args=SBAR,
               clim=(h2_min, h2_max), interpolate_before_map=True)
    p.camera_position = camera_outlet()
    p.camera.zoom(1.5)
    add_text(p, f"Y_H2 on outlet (CoV plane)  "
                f"mean = {h2_mean:.4g}")
    save(p, out)


def fig_streamlines(ds, case: Path, out: Path,
                    *, alpha_deg: float, r_branch: float, zjct: float):
    internal = get_internal(ds)
    pdata = internal.cell_data_to_point_data()

    # Main inlet seeds: ring at z = 0.03, radius 0.7 R_main
    theta = np.linspace(0.0, 2.0 * np.pi, 16, endpoint=False)
    main = np.column_stack(
        [0.7 * R_MAIN_HALF * np.cos(theta),
         0.7 * R_MAIN_HALF * np.sin(theta),
         np.full_like(theta, 0.03)]
    )

    # Branch inlet seeds: at the open end of the branch tube,
    # i.e. base + (l_branch - small) * nb in the x=0 plane.
    L_b = 1.40
    nb_y, nb_z = _branch_axis(alpha_deg)
    by = R_MAIN_HALF + (L_b - 0.04) * nb_y
    bz = zjct        + (L_b - 0.04) * nb_z
    br = np.column_stack(
        [0.7 * r_branch * np.cos(theta),
         np.full_like(theta, by),
         bz + 0.7 * r_branch * np.sin(theta)]
    )

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
    vmax = float(np.nanpercentile(speed, 99.0))

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
    add_text(p, "Streamlines seeded from both inlets  --  colored by speed  U  (m/s)")
    save(p, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", type=Path)
    ap.add_argument("out_dir",  type=Path)
    ap.add_argument("--time", type=float, default=None,
                    help="time step to render (default: last)")
    args = ap.parse_args()

    case = args.case_dir.resolve()
    out  = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    print(f"Case: {case}")
    print(f"Out:  {out}")

    # Per-case parameters
    info_path = case / "case_info.json"
    info = {}
    try:
        if info_path.exists():
            info = json.loads(info_path.read_text())
    except Exception:
        info = {}
    alpha_deg = float(info.get("alpha_deg", 90.0))
    r_branch  = float(info.get("D2_m",  0.10)) / 2.0
    z_jct     = float(info.get("ZJCT",  Z_JCT_HALF))
    print(f"  per-case: alpha={alpha_deg:.1f} deg  "
          f"r_branch={r_branch:.4f} m  z_jct={z_jct:.3f} m")

    print("[1/7] fig_geometry")
    fig_geometry(case, out / "fig_geometry.png")

    print("[2/7] loading volume mesh...")
    ds, t = load_case(case, args.time)
    internal = get_internal(ds)
    cell_fields = list(internal.cell_data.keys())
    print(f"       internal: {internal.n_cells:,} cells, "
          f"fields: {cell_fields[:6]} ...")

    print("[3/7] fig_mesh_xz")
    fig_mesh_xz(ds, out / "fig_mesh_xz.png")

    # Compute orphan-cell mask once -- used by every centreline figure so
    # snappyHexMesh's frozen-IC cells don't pollute the colour ranges.
    ctrs_3d = np.asarray(internal.cell_centers().points)
    h2_arr  = np.asarray(internal.cell_data["H2"])
    orphan_3d = _orphan_mask_3d(ctrs_3d, h2_arr,
                                alpha_deg=alpha_deg, r_branch=r_branch,
                                zjct=z_jct)
    print(f"       orphan-cell mask: {int(orphan_3d.sum())} of "
          f"{orphan_3d.size} cells flagged "
          f"({100.0 * orphan_3d.mean():.4f}%)")

    # Recompute |U| and p_rgh_gauge as cell-data once for kNN reuse.
    U = np.asarray(internal.cell_data["U"])
    internal["|U|"] = np.linalg.norm(U, axis=1)
    p_rgh = np.asarray(internal.cell_data["p_rgh"])
    p_mean = float(np.mean(p_rgh[~orphan_3d]))
    internal["p_rgh_gauge"] = p_rgh - p_mean

    print("[4/7] fig_H2_xz")
    _render_centerline_interp(
        internal, "H2", out / "fig_H2_xz.png",
        title=f"Y_H2 (H2 mass fraction)  --  x=0 centreline slice  (t = {t:g} s)",
        cmap=CMAP_H2, clim=None,
        alpha_deg=alpha_deg, r_branch=r_branch, zjct=z_jct,
        orphan_3d=orphan_3d,
        label="Y_H2 (mass fraction)",
    )

    print("[5/7] fig_H2_outlet")
    fig_H2_outlet(ds, out / "fig_H2_outlet.png")

    print("[6/7] fig_velocity_xz + fig_pressure_xz")
    _render_centerline_interp(
        internal, "|U|", out / "fig_velocity_xz.png",
        title=f"Velocity magnitude |U| (m/s)  --  x=0 centreline  (t = {t:g} s)",
        cmap=CMAP_SPEED, clim=None,
        alpha_deg=alpha_deg, r_branch=r_branch, zjct=z_jct,
        orphan_3d=orphan_3d,
        label="|U| [m/s]",
    )
    _render_centerline_interp(
        internal, "p_rgh_gauge", out / "fig_pressure_xz.png",
        title=f"p_rgh - {p_mean/1e6:.3f} MPa [Pa]  --  "
              f"x=0 centreline (t = {t:g} s)",
        cmap=CMAP_PRESS, clim=None,
        alpha_deg=alpha_deg, r_branch=r_branch, zjct=z_jct,
        orphan_3d=orphan_3d,
        label="p_rgh gauge [Pa]",
    )

    print("[7/7] fig_streamlines")
    fig_streamlines(ds, case, out / "fig_streamlines.png",
                    alpha_deg=alpha_deg, r_branch=r_branch, zjct=z_jct)

    print("DONE.")


if __name__ == "__main__":
    sys.exit(main())
