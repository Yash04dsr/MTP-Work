#!/usr/bin/env python3
"""make_distance_figures.py -- cross-section snapshots at every R5 station.

For a given OpenFOAM case (reconstructed mean field available) this produces
per-case PNGs that show how the injected H2 blend evolves as it convects
downstream, at the four R5 sampling planes (z = 3, 4, 5, 6 m, corresponding
to 0.7, 1.7, 2.7, 3.7 m downstream of the junction at z_jct = 2.3 m) plus
the outlet at z = L_MAIN.

Output (under <outdir>):

    fig_H2_strip.png        row of H2 contours at z = 3, 4, 5, 6, outlet
    fig_U_strip.png         row of |U| contours at the same stations
    fig_H2_long.png         longitudinal (x = 0 centerline) H2 slice with
                            the sampling planes drawn as yellow lines
    fig_H2_outlet.png       H2 on the outlet face (the CoV reporting plane)

The strip figures use a single, consistent colour scale so you can line up
any two cases and visually tell which mixes better / faster.

Usage
-----
    python3 make_distance_figures.py --case <case_dir> --outdir <out_dir> \
        [--time T]                [--field-suffix "Mean"]

Tip : after a case finishes with fieldAverage on, you typically want
      --field-suffix Mean so the snapshot uses the time-averaged H2Mean
      and UMean rather than a noisy instantaneous snapshot.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np

os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
import pyvista as pv  # noqa: E402

pv.OFF_SCREEN = True


# --- constants (post-R2 geometry) -------------------------------------

Z_JCT       = 2.30
L_MAIN      = 6.90
R_MAIN      = 0.23

# Sampling stations (matches R5 in system/controlDict).
Z_STATIONS  = [3.0, 4.0, 5.0, 6.0]
STATIONS_DS = [z - Z_JCT for z in Z_STATIONS]

WIDE        = (2400, 600)      # strip figure
HALF_HEIGHT = (1400, 700)      # longitudinal
SQUARE      = (800, 800)

CMAP_H2     = "viridis"
CMAP_U      = "plasma"


# --- helpers ----------------------------------------------------------

def load_case(case_dir: Path, target_time: float | None):
    foam = case_dir / "case.foam"
    foam.touch()
    reader = pv.POpenFOAMReader(str(foam))
    reader.enable_all_cell_arrays()
    times = list(reader.time_values)
    if not times:
        raise SystemExit(f"No time steps in {case_dir}")
    t = target_time if target_time is not None else times[-1]
    if t not in times:
        raise SystemExit(f"time {t} not among {times}")
    reader.set_active_time_value(t)
    print(f"  reading t = {t} s")
    return reader.read(), t


def get_internal(ds):
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


_TRI_CACHE = {}

def triangulated(internal):
    """Return a triangulated (tetrahedral) copy of the internal grid.

    OpenFOAM polyhedral cells can be non-manifold at sharp junction edges,
    which causes VTK's slice() to drop those cells and leave visible "white
    notch" gaps in centreline contour figures.  Converting the whole volume
    to tetrahedra (cheap, ~1-2 s) eliminates the gaps."""
    key = id(internal)
    if key not in _TRI_CACHE:
        _TRI_CACHE[key] = internal.triangulate()
    return _TRI_CACHE[key]


def add_text(p, txt, pos=(0.01, 0.92)):
    p.add_text(txt, font_size=13, color="black", position=pos, viewport=True)


# --- figures ----------------------------------------------------------

def _mirror(half: pv.DataSet) -> pv.PolyData | pv.UnstructuredGrid:
    """Mirror a half-domain slice about x = 0 so the visualisation shows
    the recovered full pipe cross-section rather than just the +x half.
    Scalars carry over.  Uses reflect() which preserves point data."""
    try:
        mirrored = half.reflect(normal=(1, 0, 0), point=(0, 0, 0))
        return half.merge(mirrored)
    except Exception:
        return half


def strip_figure(
    field: str,
    cmap: str,
    clim: tuple[float, float] | None,
    internal: pv.UnstructuredGrid,
    out: Path,
    title_fmt: str,
):
    """Render 5 cross-sections (z = 3, 4, 5, 6, L_MAIN) in a horizontal row."""
    p = pv.Plotter(off_screen=True, shape=(1, 5),
                   window_size=WIDE, border=True, border_color="#888888")
    p.set_background("white")

    stations = Z_STATIONS + [L_MAIN - 0.01]   # outlet just upstream of end
    titles   = [f"z = {z:.1f} m" for z in Z_STATIONS] + ["outlet"]

    tri = triangulated(internal)

    # Compute a SHARED range across all 5 panels so contours are comparable.
    # Use the 99.5th percentile over all stations so a single upstream spike
    # does not flatten the downstream mixed regions to dark purple.
    if clim is None or clim == (0, 1):
        vmax_candidates = []
        for z in stations:
            sl0 = tri.slice(normal="z", origin=(0, 0, z))
            if field in sl0.array_names and sl0.n_points > 0:
                vmax_candidates.append(float(np.nanpercentile(
                    np.asarray(sl0[field]), 99.5)))
        if not vmax_candidates:
            raise SystemExit(f"field {field} not available on any station slice")
        vmax = max(vmax_candidates)
        vmax = max(vmax, 1.0e-6)
        clim = (0.0, vmax)

    for k, (z, t) in enumerate(zip(stations, titles)):
        p.subplot(0, k)
        sl = tri.slice(normal="z", origin=(0, 0, z))
        if field not in sl.array_names:
            add_text(p, f"no {field} at z={z:.1f}")
            continue
        sl_full = _mirror(sl)
        p.add_mesh(sl_full, scalars=field, cmap=cmap, clim=clim,
                   show_edges=False, show_scalar_bar=False)
        # Camera looking +z, centred on the pipe axis (y = 0).
        cam_pos = (0.0, 0.0, z - 1.2)
        p.camera_position = [cam_pos, (0.0, 0.0, z), (0, 1, 0)]
        p.camera.zoom(1.4)
        add_text(p, t, pos=(0.05, 0.90))
        if k == 0:
            add_text(p, title_fmt.format(lo=clim[0], hi=clim[1]),
                     pos=(0.05, 0.08))
    # Put a single colour bar across the bottom of the last panel.
    p.subplot(0, 4)
    p.add_scalar_bar(title=field, color="black", vertical=False,
                     n_labels=5, label_font_size=11, title_font_size=12,
                     position_x=0.05, position_y=0.02,
                     width=0.90, height=0.035,
                     fmt="%.3g")
    p.screenshot(str(out), transparent_background=False)
    print(f"  wrote {out.name}   clim=({clim[0]:.4g}, {clim[1]:.4g})")


def long_slice_figure(internal, out: Path, r_branch: float = 0.10,
                      zjct: float = Z_JCT):
    """Longitudinal H2 centreline via point-interpolation (gap-free).

    Uses scipy.cKDTree to interpolate cell-centre values onto a regular
    (y, z) image grid, then masks with the analytical pipe geometry.
    Eliminates the white-speckle artifacts that VTK's slice() produces
    at polyhedral non-manifold faces near the junction and inlet."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.spatial import cKDTree

    fld = "H2Mean" if "H2Mean" in internal.array_names else "H2"
    if fld not in internal.array_names:
        raise SystemExit("no H2 / H2Mean in internal cell data")

    ctrs = np.asarray(internal.cell_centers().points)
    vals = np.asarray(internal[fld])
    tree = cKDTree(ctrs)

    l_branch = max(1.38, R_MAIN + 12.0 * r_branch * 2.0)
    x_plane = 0.015

    ny, nz = 520, 1400
    y = np.linspace(-R_MAIN - 0.02, R_MAIN + l_branch + 0.05, ny)
    z = np.linspace(0.0, L_MAIN, nz)
    Y, Z = np.meshgrid(y, z, indexing="ij")
    X = np.full_like(Y, x_plane)
    qpts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    dist, idx = tree.query(qpts, k=1)
    img = vals[idx].reshape(Y.shape)
    img = np.where(dist.reshape(Y.shape) > 0.04, np.nan, img)

    in_main = (x_plane**2 + Y**2 < R_MAIN**2) & (Y <= R_MAIN)
    in_branch = (x_plane**2 + (Z - zjct)**2 < r_branch**2) \
                & (Y >= R_MAIN) & (Y <= R_MAIN + l_branch)
    geom = in_main | in_branch
    img = np.where(geom & np.isfinite(img), img, np.nan)

    if fld in ("H2", "H2Mean"):
        orphan = (img > 0.5) & (Y < R_MAIN) \
                 & (np.abs(Z - zjct) > r_branch + 0.05)
        img = np.where(orphan, np.nan, img)

    valid = geom & (np.abs(Y) < R_MAIN) & (Z > zjct + 0.3) & np.isfinite(img)
    if valid.sum() > 0:
        vmax = float(np.nanpercentile(img[valid], 99.0))
    else:
        vmax = float(np.nanpercentile(img[np.isfinite(img)], 99.0))
    vmax = max(vmax, 1e-6)

    fig, ax = plt.subplots(figsize=(16, 7))
    img_m = np.ma.array(img, mask=~np.isfinite(img))
    pcm = ax.pcolormesh(Z, Y, img_m, cmap=CMAP_H2,
                        vmin=0.0, vmax=vmax, shading="auto")
    for zs in Z_STATIONS + [L_MAIN - 0.01]:
        ax.axvline(zs, color="#f1c40f", linewidth=2.5, alpha=0.85)
    ax.set_aspect("equal")
    ax.set_xlabel("z [m]")
    ax.set_ylabel("y [m]")
    ax.set_xlim(0.0, L_MAIN)
    ax.set_ylim(-R_MAIN - 0.02, R_MAIN + l_branch + 0.05)
    ax.set_title(f"Longitudinal centreline slice — {fld} (vmax={vmax:.4g}); "
                 f"yellow = R5 sampling stations")
    cbar = fig.colorbar(pcm, ax=ax, orientation="horizontal",
                        fraction=0.035, pad=0.08)
    cbar.set_label(f"{fld}  [mass fraction]")
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out), dpi=140)
    plt.close(fig)
    print(f"  wrote {out.name}  ({out.stat().st_size/1024:.1f} KB)")


def outlet_face_figure(ds, out: Path):
    outlet = get_patch(ds, "outlet")
    if outlet is None:
        print("  [warn] no outlet patch -- skipping fig_H2_outlet")
        return
    fld = "H2Mean" if "H2Mean" in outlet.array_names else "H2"
    full = _mirror(outlet)
    arr = np.asarray(full[fld])
    vmean = float(np.nanmean(arr))
    vmax_99 = float(np.nanpercentile(arr, 99.0))
    # Use a scale that spans the actual data: 99th percentile, floored at
    # 2 * mean so the mean is always in the middle of the colormap.
    vmax = max(vmax_99, 2.0 * vmax_99 if vmax_99 < 1.0e-6 else vmax_99, 2.0 * vmean)
    vmax = max(vmax, 1.0e-6)
    p = pv.Plotter(off_screen=True, window_size=SQUARE)
    p.set_background("white")
    p.add_mesh(full, scalars=fld, cmap=CMAP_H2, clim=(0.0, vmax),
               show_edges=False,
               scalar_bar_args=dict(
                   title=f"{fld}   [0..{vmax:.3g}]", color="black", n_labels=5,
                   label_font_size=11, title_font_size=12,
                   vertical=False, position_x=0.20, position_y=0.04,
                   width=0.60, height=0.032, fmt="%.3g"))
    # Camera focal point at pipe axis (y = 0 for this geometry), looking from +z.
    p.camera_position = [(0, 0.0, L_MAIN + 1.2),
                         (0, 0.0, L_MAIN), (0, 1, 0)]
    p.camera.zoom(1.35)
    add_text(p, f"Outlet face, {fld}  (CoV reporting plane)   "
                f"mean={vmean:.4g}, 99%ile={vmax_99:.4g}")
    p.screenshot(str(out))
    print(f"  wrote {out.name}")


def fig_H2_isosurface(ds, case_dir: Path, out: Path,
                      iso_values: list[float] | None = None):
    """3D H2 isosurface(s) with translucent pipe walls.

    Renders one or more isocontours of H2 (or H2Mean) inside a ghost
    outline of the pipe geometry.  This is the most unambiguous way to
    show plume shape and injection direction — no slicing artifacts."""
    internal = get_internal(ds)
    fld = "H2Mean" if "H2Mean" in internal.array_names else "H2"

    if iso_values is None:
        arr = np.asarray(internal[fld])
        arr_pos = arr[arr > 1e-6]
        if arr_pos.size == 0:
            print("  [warn] no positive H2 values — skipping isosurface")
            return
        p50 = float(np.nanpercentile(arr_pos, 50))
        iso_values = [p50 * 0.25, p50, p50 * 2.5]
        iso_values = [v for v in iso_values if 1e-6 < v < 0.95]
        if not iso_values:
            iso_values = [0.005]

    iso_colors = ["#2ecc71", "#f39c12", "#e74c3c"]

    p = pv.Plotter(off_screen=True, window_size=(1600, 900))
    p.set_background("white")

    tri_surf = case_dir / "constant" / "triSurface" / "wall.stl"
    if tri_surf.exists():
        wall = pv.read(str(tri_surf))
        p.add_mesh(wall, color="#95a5a6", opacity=0.08, show_edges=False)

    labels = []
    for k, val in enumerate(sorted(iso_values)):
        try:
            iso = internal.contour([val], scalars=fld)
        except Exception:
            continue
        if iso is None or iso.n_points == 0:
            continue
        iso_full = _mirror(iso)
        color = iso_colors[k % len(iso_colors)]
        opacity = 0.7 if k == 0 else 0.5
        p.add_mesh(iso_full, color=color, opacity=opacity,
                   show_edges=False, smooth_shading=True)
        labels.append([f"{fld} = {val:.4g}", color])

    if labels:
        p.add_legend(labels=labels, bcolor="white", border=True,
                     size=(0.20, 0.06 * len(labels)),
                     loc="upper right", face="rectangle")

    p.add_axes(color="black", line_width=2)
    p.camera_position = [(-4.5, 3.5, -2.0), (0.0, 0.35, 3.45), (0, 1, 0)]
    p.camera.zoom(1.15)
    add_text(p, f"H₂ plume isosurfaces ({fld}) — 3D view")
    out.parent.mkdir(parents=True, exist_ok=True)
    p.screenshot(str(out), transparent_background=False)
    p.close()
    print(f"  wrote {out.name}  ({out.stat().st_size/1024:.1f} KB)")


def fig_H2_topdown(ds, case_dir: Path, out: Path,
                   iso_values: list[float] | None = None):
    """Top-down (Y-normal) view of H2 isosurfaces showing lateral spread."""
    internal = get_internal(ds)
    fld = "H2Mean" if "H2Mean" in internal.array_names else "H2"

    if iso_values is None:
        arr = np.asarray(internal[fld])
        arr_pos = arr[arr > 1e-6]
        if arr_pos.size == 0:
            print("  [warn] no positive H2 values — skipping topdown")
            return
        p50 = float(np.nanpercentile(arr_pos, 50))
        iso_values = [p50 * 0.25, p50, p50 * 2.5]
        iso_values = [v for v in iso_values if 1e-6 < v < 0.95]
        if not iso_values:
            iso_values = [0.005]

    iso_colors = ["#2ecc71", "#f39c12", "#e74c3c"]

    p = pv.Plotter(off_screen=True, window_size=(1800, 600))
    p.set_background("white")

    tri_surf = case_dir / "constant" / "triSurface" / "wall.stl"
    if tri_surf.exists():
        wall = pv.read(str(tri_surf))
        p.add_mesh(wall, color="#95a5a6", opacity=0.06, show_edges=False)

    labels = []
    for k, val in enumerate(sorted(iso_values)):
        try:
            iso = internal.contour([val], scalars=fld)
        except Exception:
            continue
        if iso is None or iso.n_points == 0:
            continue
        iso_full = _mirror(iso)
        color = iso_colors[k % len(iso_colors)]
        p.add_mesh(iso_full, color=color, opacity=0.65,
                   show_edges=False, smooth_shading=True)
        labels.append([f"{fld} = {val:.4g}", color])

    if labels:
        p.add_legend(labels=labels, bcolor="white", border=True,
                     size=(0.14, 0.05 * len(labels)),
                     loc="upper right", face="rectangle")

    p.camera_position = [(0.0, 6.0, 3.45), (0.0, 0.0, 3.45), (0, 0, 1)]
    p.camera.zoom(1.3)
    p.add_axes(color="black", line_width=2)
    add_text(p, f"Top-down view: H₂ lateral spread ({fld})")
    out.parent.mkdir(parents=True, exist_ok=True)
    p.screenshot(str(out), transparent_background=False)
    p.close()
    print(f"  wrote {out.name}  ({out.stat().st_size/1024:.1f} KB)")


def fig_H2_cross_sections_3d(ds, case_dir: Path, out: Path):
    """3D stacked cross-sections at R5 stations showing H2 diffusion decay."""
    internal = get_internal(ds)
    fld = "H2Mean" if "H2Mean" in internal.array_names else "H2"
    tri = triangulated(internal)

    stations = [Z_JCT + 0.15] + Z_STATIONS + [L_MAIN - 0.01]
    station_labels = ["jct+0.15"] + [f"z={z:.0f}m" for z in Z_STATIONS] + ["outlet"]

    vmax_candidates = []
    for z in stations:
        sl0 = tri.slice(normal="z", origin=(0, 0, z))
        if fld in sl0.array_names and sl0.n_points > 0:
            vmax_candidates.append(float(np.nanpercentile(
                np.asarray(sl0[fld]), 99.5)))
    if not vmax_candidates:
        print("  [warn] no H2 data on any station — skipping 3D cross-sections")
        return
    vmax = max(max(vmax_candidates), 1e-6)
    vmax = min(vmax, 0.06)
    clim = (0.0, vmax)

    p = pv.Plotter(off_screen=True, window_size=(1800, 800))
    p.set_background("white")

    tri_surf = case_dir / "constant" / "triSurface" / "wall.stl"
    if tri_surf.exists():
        wall = pv.read(str(tri_surf))
        p.add_mesh(wall, color="#95a5a6", opacity=0.06, show_edges=False)

    sbar_args = dict(
        title=f"{fld} [0..{vmax:.3g}]", color="black", n_labels=5,
        label_font_size=11, title_font_size=12,
        vertical=False, position_x=0.25, position_y=0.03,
        width=0.50, height=0.03, fmt="%.3g",
    )
    first = True
    for z, label in zip(stations, station_labels):
        sl = tri.slice(normal="z", origin=(0, 0, z))
        if fld not in sl.array_names:
            continue
        sl_full = _mirror(sl)
        p.add_mesh(sl_full, scalars=fld, cmap=CMAP_H2, clim=clim,
                   show_edges=False,
                   show_scalar_bar=first,
                   scalar_bar_args=sbar_args if first else None)
        first = False

        edge = sl_full.extract_feature_edges(boundary_edges=True,
                                              feature_edges=False,
                                              manifold_edges=False)
        p.add_mesh(edge, color="#333333", line_width=1.5)

    p.camera_position = [(-5.0, 3.0, -1.0), (0.0, 0.0, 3.45), (0, 1, 0)]
    p.camera.zoom(1.15)
    p.add_axes(color="black", line_width=2)
    add_text(p, f"Downstream H₂ diffusion — cross-sections at R5 stations ({fld})")
    out.parent.mkdir(parents=True, exist_ok=True)
    p.screenshot(str(out), transparent_background=False)
    p.close()
    print(f"  wrote {out.name}  ({out.stat().st_size/1024:.1f} KB)")


def fig_cov_vs_zD(internal, out: Path, r_branch: float = 0.10,
                  zjct: float = Z_JCT):
    """Line plot of CoV vs downstream distance z/D.

    Samples H2 at many cross-sections from just after the junction to
    the outlet, computes area-weighted CoV at each, and plots the decay
    curve with a shaded band marking CoV < 0.05 (95% mixed)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fld = "H2Mean" if "H2Mean" in internal.array_names else "H2"
    if fld not in internal.array_names:
        print("  [warn] no H2/H2Mean — skipping CoV vs z/D")
        return

    D = 2.0 * R_MAIN  # main pipe diameter

    # Sample at many z-stations from junction to outlet
    z_start = zjct + 0.2
    z_end = L_MAIN - 0.02
    n_stations = 30
    z_vals = np.linspace(z_start, z_end, n_stations)

    tri = triangulated(internal)
    zD_list = []
    cov_list = []

    for z in z_vals:
        sl = tri.slice(normal="z", origin=(0, 0, z))
        if sl.n_points == 0 or fld not in sl.array_names:
            continue

        h2 = np.asarray(sl[fld])
        if h2.size == 0:
            continue

        # Area-weighted CoV: use cell areas if available, else uniform
        try:
            sl_surf = sl.compute_cell_sizes(length=False, volume=False, area=True)
            areas = np.asarray(sl_surf["Area"])
            if areas.sum() < 1e-12:
                areas = np.ones(h2.size)
        except Exception:
            areas = np.ones(h2.size)

        # For point data, convert to cell data first
        if h2.size != areas.size:
            areas = np.ones(h2.size)

        mean_h2 = np.average(h2, weights=areas)
        if mean_h2 < 1e-10:
            continue

        var_h2 = np.average((h2 - mean_h2) ** 2, weights=areas)
        cov = np.sqrt(var_h2) / mean_h2

        zD_list.append((z - zjct) / D)
        cov_list.append(cov)

    if len(zD_list) < 3:
        print("  [warn] too few valid stations for CoV plot — skipping")
        return

    zD_arr = np.array(zD_list)
    cov_arr = np.array(cov_list)

    fig, ax = plt.subplots(figsize=(10, 5))

    # Shaded band for "well-mixed" threshold
    ax.axhspan(0, 0.05, color="#2ecc71", alpha=0.15, label="CoV < 0.05 (well-mixed)")
    ax.axhline(0.05, color="#2ecc71", ls="--", lw=1.5, alpha=0.7)

    ax.plot(zD_arr, cov_arr, "o-", color="#1f77b4", lw=2.5, ms=5,
            markeredgecolor="k", markeredgewidth=0.5, label="CoV(z)")

    # Mark the R5 sampling stations
    for z_st in Z_STATIONS:
        zD_st = (z_st - zjct) / D
        ax.axvline(zD_st, color="#f39c12", ls=":", lw=1.5, alpha=0.6)

    # Annotate outlet CoV
    ax.annotate(f"Outlet CoV = {cov_arr[-1]:.4f}",
                xy=(zD_arr[-1], cov_arr[-1]),
                xytext=(zD_arr[-1] - 2, cov_arr[-1] + max(cov_arr) * 0.15),
                arrowprops=dict(arrowstyle="->", color="black"),
                fontsize=10, ha="center",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow",
                          edgecolor="gray"))

    ax.set_xlabel("Downstream distance  z/D", fontsize=12)
    ax.set_ylabel("Coefficient of Variation (CoV)", fontsize=12)
    ax.set_title(f"Mixing Uniformity Decay — {fld}", fontsize=13)
    ax.set_xlim(0, zD_arr[-1] * 1.05)
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out), dpi=150)
    plt.close(fig)
    print(f"  wrote {out.name}  ({out.stat().st_size/1024:.1f} KB)")


# --- main -------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case",   required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--time",   type=float, default=None)
    ap.add_argument("--field-suffix", default="Mean",
                    help="Try {H2,U}+{suffix} first; fall back to raw "
                         "instantaneous fields if the averaged ones are "
                         "not in the case.  Pass '' to always use raw.")
    args = ap.parse_args()

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    ds, t = load_case(args.case, args.time)
    internal = get_internal(ds)

    # Pick H2 / U fields, preferring fieldAverage output if available.
    suffix = args.field_suffix
    h2_field = f"H2{suffix}" if f"H2{suffix}" in internal.array_names else "H2"
    u_field  = f"U{suffix}"  if f"U{suffix}"  in internal.array_names else "U"
    print(f"  using h2={h2_field}, u={u_field}")

    # |U| magnitude derived from the vector field.
    if u_field in internal.array_names:
        u = internal[u_field]
        internal["U_mag"] = np.linalg.norm(np.asarray(u), axis=1)
    else:
        internal["U_mag"] = np.zeros(internal.n_cells)

    # Alias H2-field for simpler downstream code.
    if h2_field != "H2":
        internal["H2"] = internal[h2_field]

    # Per-case branch radius for geometry mask in centreline figures.
    import json
    info_path = args.case / "case_info.json"
    try:
        info = json.loads(info_path.read_text()) if info_path.exists() else {}
    except Exception:
        info = {}
    r_branch = float(info.get("D2_m", 0.10)) / 2.0
    z_jct = float(info.get("ZJCT", Z_JCT))

    strip_figure(
        field="H2", cmap=CMAP_H2, clim=(0, 1),
        internal=internal, out=outdir / "fig_H2_strip.png",
        title_fmt=f"H2 {h2_field}  [{{lo:.3f}}, {{hi:.3f}}]",
    )
    strip_figure(
        field="U_mag", cmap=CMAP_U, clim=None,
        internal=internal, out=outdir / "fig_U_strip.png",
        title_fmt=f"|U| {u_field}  [{{lo:.3f}}, {{hi:.3f}}] m/s",
    )
    long_slice_figure(internal, outdir / "fig_H2_long.png",
                      r_branch=r_branch, zjct=z_jct)
    outlet_face_figure(ds, outdir / "fig_H2_outlet.png")
    fig_H2_isosurface(ds, args.case, outdir / "fig_H2_isosurface.png")
    fig_H2_topdown(ds, args.case, outdir / "fig_H2_topdown.png")
    fig_H2_cross_sections_3d(ds, args.case, outdir / "fig_H2_cross_sections.png")
    fig_cov_vs_zD(internal, outdir / "fig_CoV_vs_zD.png",
                  r_branch=r_branch, zjct=z_jct)

    print(f"Wrote 8 figures under {outdir}")


if __name__ == "__main__":
    main()
