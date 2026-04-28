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


# Cameras are tuned for a pipe that runs along +z (length 9.2 m) with a branch
# pointing in +y.  For the 2-D centerline slice (x=0 plane) we want z horizontal
# and y vertical.  Looking from −x with view-up = +y puts the inlet (z=0) on the
# left and the outlet (z=9.2) on the right, with the branch pointing up.
def camera_xz_slice():
    return [(-6.0, 0.35, 4.6), (0.0, 0.35, 4.6), (0.0, 1.0, 0.0)]


def camera_iso():
    return [(-5.5, 3.0, -3.5), (0.0, 0.35, 4.6), (0.0, 1.0, 0.0)]


def camera_outlet():
    return [(0.0, 0.0, 12.0), (0.0, 0.0, 9.2), (0.0, 1.0, 0.0)]


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
    internal = get_internal(ds)
    slc = internal.slice(normal="x", origin=(0.001, 0.0, 4.6))
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
    add_text(p, f"Mesh — x=0 slice  ({internal.n_cells:,} cells total)")
    save(p, out)


def _slice_x0(ds):
    internal = get_internal(ds)
    tri = triangulated(ds)
    # Triangulated slice has no polyhedral non-manifold gaps at the junction.
    return internal, tri.slice(normal="x", origin=(0.005, 0.0, 4.6))


# Geometry constants (post-R2 half-domain).  The branch radius is per-case
# but for the gap-free H2 centreline figure we only need a conservative
# upper bound; we default to 0.10 m which covers every DoE case.
R_MAIN_HALF  = 0.23
L_MAIN_HALF  = 6.90
Z_JCT_HALF   = 2.30


def _render_centerline_interp(internal, field: str, out: Path, *,
                              title: str, cmap: str, clim=None,
                              r_branch: float = 0.10, zjct: float = Z_JCT_HALF,
                              l_branch: float = 1.15, x_plane: float = 0.05,
                              alpha_deg: float = 90.0,
                              outlier_pct: float | None = None,
                              outlier_max: float | None = None,
                              outlier_min: float | None = None,
                              label: str | None = None):
    """Render a scalar on the x=0 centreline plane via point-interpolation.

    k=4 inverse-distance-weighted interpolation from cell centres onto a
    regular (y,z) image grid, masked by an analytical pipe-geometry mask.
    Handles a branch that meets the main pipe at an arbitrary angle
    `alpha_deg` (90 deg for the original geometry, 30 deg for forward-tilt,
    150 deg for counter-flow).
    """
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
    vals = np.asarray(internal.cell_data[field], dtype=float).copy()

    # Outlier rejection on the *cell values*.  snappyHexMesh leaves frozen-
    # field "orphan" / dead-zone cells stuck at their initial-condition value
    # (e.g. p_rgh = p_atm sitting ~270 kPa above the bulk fluid; H2 stuck at
    # 1.0 instead of 0 from a left-over initialField).  Without rejection
    # these contaminate the kNN.  Two filter knobs:
    #   - outlier_pct : IQR multiplier k -- keeps [Q1-k*IQR, Q3+k*IQR].
    #     Adapts to the field's natural variability (good for unimodal
    #     fields like p_rgh).  Skipped when IQR == 0.
    #   - outlier_max / outlier_min : hard caps -- drop cells with values
    #     above / below the cap (good for bounded fields like mass fractions
    #     where the orphan value is known a priori).
    if outlier_pct is not None and outlier_pct > 0.0:
        k_iqr = float(outlier_pct)
        q1, q3 = np.nanpercentile(vals, [25.0, 75.0])
        iqr = q3 - q1
        if iqr > 0:
            lo = q1 - k_iqr * iqr
            hi = q3 + k_iqr * iqr
            ok = (vals >= lo) & (vals <= hi)
            ctrs = ctrs[ok]
            vals = vals[ok]
    # Spatial-aware hard caps: orphan cells stuck at the field's initial value
    # need to be filtered, but the BRANCH PIPE legitimately holds extreme
    # values (the branch_inlet sets H2 = 1.0, full hydrogen) so we must spare
    # any cell that is geometrically inside the analytical branch volume.
    if outlier_max is not None or outlier_min is not None:
        a_rad = math.radians(alpha_deg)
        sa_c, ca_c = math.sin(a_rad), math.cos(a_rad)
        nb = np.array([0.0, sa_c, -ca_c])
        base = np.array([0.0, R_MAIN_HALF, zjct])
        dvec = ctrs - base
        s_along = dvec @ nb
        perp = dvec - np.outer(s_along, nb)
        r_perp = np.linalg.norm(perp, axis=1)
        in_branch_cell = (s_along >= -0.05) & (s_along <= l_branch + 0.05) \
                         & (r_perp < r_branch * 1.05)
        ok = np.ones_like(vals, dtype=bool)
        if outlier_max is not None:
            ok &= (vals < outlier_max) | in_branch_cell
        if outlier_min is not None:
            ok &= (vals > outlier_min) | in_branch_cell
        ctrs = ctrs[ok]
        vals = vals[ok]
    tree = cKDTree(ctrs)

    ny, nz = 520, 1400
    y_lo = -R_MAIN_HALF - 0.04
    y_hi =  R_MAIN_HALF + 1.20
    y = np.linspace(y_lo, y_hi, ny)
    z = np.linspace(0.0, L_MAIN_HALF, nz)
    Y, Z = np.meshgrid(y, z, indexing="ij")
    X = np.full_like(Y, x_plane)
    qpts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])

    # k=4 inverse-distance weighting; this smooths over coarse upstream cells
    # and removes the speckled accept/reject pattern that k=1 + tight cap
    # produces on the bulk background mesh.
    dist, idx = tree.query(qpts, k=4)
    eps = 1.0e-6
    w = 1.0 / (dist + eps)
    w_sum = w.sum(axis=1)
    img_raw = (w * vals[idx]).sum(axis=1) / w_sum
    img = img_raw.reshape(Y.shape)
    # Reject points whose nearest neighbour is unreasonably far -- larger cap
    # (12 cm) than before, because the background mesh is coarse upstream.
    nearest = dist[:, 0].reshape(Y.shape)
    img = np.where(nearest > 0.12, np.nan, img)

    # ----- analytic geometry mask --------------------------------------
    # Main pipe: cylinder along z with radius R_MAIN_HALF.  At slice plane
    # x = x_plane, the in-pipe condition is x^2 + y^2 < R^2.
    in_main = (x_plane * x_plane + Y * Y < R_MAIN_HALF * R_MAIN_HALF) \
              & (Z >= 0.0) & (Z <= L_MAIN_HALF)

    # Branch pipe: cylinder whose axis starts at (0, R_main, zjct) and
    # points along  n_hat = (0, sin a, -cos a)  for a forward-tilt branch
    # (a < 90: branch leans downstream;  a = 90: vertical;  a > 90:
    # counter-flow lean upstream).  For each grid point we project onto
    # the axis to get (s, r_perp) and require 0 <= s <= l_branch and
    # r_perp < r_branch.
    a_rad = math.radians(alpha_deg)
    sa, ca = math.sin(a_rad), math.cos(a_rad)
    nb_y, nb_z = sa, -ca
    dY = Y - R_MAIN_HALF
    dZ = Z - zjct
    s = dY * nb_y + dZ * nb_z
    perp_y = dY - s * nb_y
    perp_z = dZ - s * nb_z
    r_perp = np.sqrt(x_plane * x_plane + perp_y * perp_y + perp_z * perp_z)
    in_branch = (s >= 0.0) & (s <= l_branch) & (r_perp < r_branch)

    geom = in_main | in_branch
    img = np.where(geom & np.isfinite(img), img, np.nan)

    # Mask orphan "dead-zone" cells (small pockets snappyHexMesh leaves which
    # stay frozen at their initial field value ~1.0 for H2 / 0 for the rest).
    # Applied to bounded mass-fraction fields only.
    if field in ("H2", "H2Mean"):
        # Branch interior gets to keep its real H2 values; everywhere else
        # values > 0.5 are non-physical orphans (after dilution by main flow
        # the outlet H2 is < 0.05 for every DoE case).
        orphan = (img > 0.5) & (~in_branch)
        img = np.where(orphan, np.nan, img)
        # Hide any leftover non-zero H2 upstream of the junction (z < zjct - 0.3).
        # Physically H2 = 0 upstream of the branch in steady state; tiny
        # residual values there come from numerical noise or initial-condition
        # leftover after restart and only confuse the visualisation.
        upstream_noise = (Z < zjct - 0.3) & (~in_branch) & (img < 0.05)
        img = np.where(upstream_noise, 0.0, img)

    if clim is None:
        valid = geom & (np.abs(Y) < R_MAIN_HALF) & (Z > zjct + 0.3) \
                & np.isfinite(img)
        if valid.sum() > 0:
            vmax = float(np.nanpercentile(img[valid], 99.0))
        else:
            vmax = float(np.nanpercentile(img[np.isfinite(img)], 99.0))
        vmax = max(vmax, 1e-6)
        clim = (0.0, vmax)

    fig, ax = plt.subplots(figsize=(16, 7))
    img_m = np.ma.array(img, mask=~np.isfinite(img))
    pcm = ax.pcolormesh(Z, Y, img_m, cmap=cmap,
                        vmin=clim[0], vmax=clim[1], shading="auto")
    ax.set_aspect("equal")
    ax.set_xlabel("z [m]"); ax.set_ylabel("y [m]")
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


def fig_scalar_xz(ds, field: str, out: Path, *, clim=None, cmap="viridis",
                  title: str, bar_title: str | None = None):
    internal, slc = _slice_x0(ds)
    if field not in slc.cell_data and field not in slc.point_data:
        raise SystemExit(f"field {field!r} not available; have cell={list(slc.cell_data)}")
    p = pv.Plotter(off_screen=True, window_size=WIDE)
    p.set_background("white")
    p.add_mesh(slc, scalars=field, cmap=cmap, clim=clim,
               scalar_bar_args=SBAR, show_edges=False)
    p.camera_position = camera_xz_slice()
    p.camera.zoom(1.25)
    add_text(p, title)
    save(p, out)


def fig_velocity_xz(ds, out: Path, r_branch: float = 0.10,
                    zjct: float = Z_JCT_HALF, alpha_deg: float = 90.0):
    internal = get_internal(ds)
    U = np.asarray(internal.cell_data["U"])
    internal["|U|"] = np.linalg.norm(U, axis=1)
    # 99.5th percentile cap over the interior to pick a reasonable vmax.
    vmax = float(np.nanpercentile(internal["|U|"], 99.5))
    vmax = max(vmax, 1e-3)
    _render_centerline_interp(
        internal, "|U|", out,
        title=f"Velocity magnitude |U| (m/s)  —  x=0 centreline (gap-free)",
        cmap=CMAP_SPEED, clim=(0.0, vmax),
        r_branch=r_branch, zjct=zjct, alpha_deg=alpha_deg,
        label="|U| [m/s]",
    )


def fig_pressure_xz(ds, out: Path, t: float, r_branch: float = 0.10,
                    zjct: float = Z_JCT_HALF, alpha_deg: float = 90.0):
    internal = get_internal(ds)
    p = np.asarray(internal.cell_data["p_rgh"], dtype=float)
    # Bulk fluid identified by a wide IQR band -- snappyHexMesh leaves orphan
    # cells stuck at their initial value (often the operating reference
    # pressure ~270 kPa above bulk).  The bulk-fluid IQR is small (often
    # < 1 kPa) so we use a wide multiplier (k = 50) to keep the entire
    # physical pipe gradient (including the downstream recovery zone, which
    # sits ~30 IQRs above the median) while still rejecting orphans (which
    # are >300 IQRs from the bulk centre).
    q1, q3 = np.nanpercentile(p, [25.0, 75.0])
    iqr = q3 - q1
    if iqr > 0:
        in_band = (p >= q1 - 50.0 * iqr) & (p <= q3 + 50.0 * iqr)
    else:
        in_band = np.ones_like(p, dtype=bool)
    p_mean = float(np.mean(p[in_band])) if in_band.any() else float(np.mean(p))
    internal["p_rgh_gauge"] = p - p_mean
    # Colour-map range tied to the bulk-fluid IQR, NOT to the global gauge
    # extremes -- the downstream recovery zone (a few cells) sits at gauge
    # ~ +20 kPa which would otherwise wash the colourmap out.  rng = 8 IQR
    # makes the wake low-pressure (gauge ~ -3 IQR) and the bulk gradient
    # readable; the recovery cells correctly saturate at the red end.
    rng = max(8.0 * iqr, 1.0e2) if iqr > 0 else 2.0e3
    _render_centerline_interp(
        internal, "p_rgh_gauge", out,
        title=f"p_rgh − {p_mean/1e6:.3f} MPa [Pa]  —  x=0 centreline (t = {t:g} s)",
        cmap=CMAP_PRESS, clim=(-rng, rng),
        r_branch=r_branch, zjct=zjct, alpha_deg=alpha_deg,
        outlier_pct=50.0,
        label="p_rgh gauge [Pa]",
    )


def fig_H2_outlet(ds, out: Path):
    outlet = get_patch(ds, "outlet")
    if outlet is None or outlet.n_cells == 0:
        internal = get_internal(ds)
        outlet = internal.slice(normal="z", origin=(0, 0, 9.19))
    p = pv.Plotter(off_screen=True, window_size=SQUARE)
    p.set_background("white")
    p.add_mesh(outlet, scalars="H2", cmap=CMAP_H2, show_edges=False,
               scalar_bar_args=SBAR)
    p.camera_position = camera_outlet()
    p.camera.zoom(1.5)
    add_text(p, "Y_H2 on outlet face  (the CoV plane)")
    save(p, out)


def fig_streamlines(ds, case: Path, out: Path):
    internal = get_internal(ds)
    pdata = internal.cell_data_to_point_data()

    theta = np.linspace(0.0, 2.0 * np.pi, 16, endpoint=False)
    main = np.column_stack(
        [0.14 * np.cos(theta), 0.14 * np.sin(theta), np.full_like(theta, 0.03)]
    )
    br = np.column_stack(
        [0.035 * np.cos(theta), np.full_like(theta, 1.36), 4.6 + 0.035 * np.sin(theta)]
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
    # H2 orphans are frozen at the initial value (~1.0) in disconnected
    # pockets snappyHexMesh occasionally leaves; the physical max in this
    # campaign is HBR < 0.20.  outlier_max = 0.5 cleanly separates them.
    _render_centerline_interp(
        internal, "H2", out / "fig_H2_xz.png",
        title=f"Y_H2 (H2 mass fraction)  —  x=0 centreline slice  (t = {t:g} s)",
        cmap=CMAP_H2, clim=None,
        r_branch=r_branch, zjct=z_jct, alpha_deg=alpha_deg,
        outlier_max=0.5,
        label="Y_H2 (mass fraction)",
    )

    print("[5/7] fig_H2_outlet")
    fig_H2_outlet(ds, out / "fig_H2_outlet.png")

    print("[6/7] fig_velocity_xz + fig_pressure_xz")
    fig_velocity_xz(ds, out / "fig_velocity_xz.png",
                    r_branch=r_branch, zjct=z_jct, alpha_deg=alpha_deg)
    fig_pressure_xz(ds, out / "fig_pressure_xz.png", t,
                    r_branch=r_branch, zjct=z_jct, alpha_deg=alpha_deg)

    print("[7/7] fig_streamlines")
    fig_streamlines(ds, case, out / "fig_streamlines.png")

    print("DONE.")


if __name__ == "__main__":
    main()
