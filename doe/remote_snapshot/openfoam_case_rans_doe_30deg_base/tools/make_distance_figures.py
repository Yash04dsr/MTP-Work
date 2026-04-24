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


_CTR_CACHE = {}

def _cell_centers_cached(internal):
    key = id(internal)
    if key not in _CTR_CACHE:
        _CTR_CACHE[key] = np.asarray(internal.cell_centers().points)
    return _CTR_CACHE[key]


def _interp_centerline(internal, field: str, x_plane: float = 0.015,
                       ny: int = 520, nz: int = 1400,
                       max_dist: float = 0.04):
    """Nearest-cell resample of a scalar field onto a regular (y,z) grid.

    Why not VTK slice?  snappyHexMesh polyhedral cells at the T-junction are
    often non-manifold, which causes VTK's slice() to drop them and leave a
    visible "white notch" gap.  Why not pyvista's kernel interpolate()?  The
    closest-point strategy is O(N*M) on our mesh and takes minutes.  A
    scipy KDTree query gives the nearest cell per sample point in ~1 s.
    """
    if field not in internal.cell_data:
        raise SystemExit(f"field {field!r} not in internal cell data")
    from scipy.spatial import cKDTree

    ctrs = _cell_centers_cached(internal)
    vals = np.asarray(internal.cell_data[field])

    tree = cKDTree(ctrs)

    y = np.linspace(-R_MAIN - 0.02,  R_MAIN + 1.20, ny)
    z = np.linspace(0.0,             L_MAIN,         nz)
    Y, Z = np.meshgrid(y, z, indexing="ij")
    X = np.full_like(Y, x_plane)
    qpts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    dist, idx = tree.query(qpts, k=1)
    img = vals[idx].reshape(Y.shape)
    # Invalidate sample points whose nearest cell is further than max_dist:
    # those are outside the actual fluid volume (e.g. just past a pipe wall).
    too_far = dist.reshape(Y.shape) > max_dist
    img = np.where(too_far, np.nan, img)
    return Y, Z, img


def _geometry_mask_xz(Y, Z, x_plane: float, r_branch: float,
                      l_branch: float = 1.15, zjct: float = Z_JCT):
    """True wherever (x_plane, Y, Z) lies inside the fluid (main pipe OR branch)."""
    in_main   = (x_plane**2 + Y**2 < R_MAIN**2) & (Y <= R_MAIN)
    in_branch = (x_plane**2 + (Z - zjct)**2 < r_branch**2) \
              & (Y >= R_MAIN) & (Y <= R_MAIN + l_branch)
    return in_main | in_branch


def long_slice_figure(internal, out: Path,
                      r_branch: float = 0.05, zjct: float = Z_JCT):
    """Longitudinal centerline slice rendered via matplotlib from a probed grid.

    Avoids VTK polyhedral non-manifold slicing gaps.  Yellow vertical bars
    mark the R5 sampling stations.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x_plane = 0.015
    fld = "H2Mean" if "H2Mean" in internal.cell_data else "H2"
    Y, Z, img = _interp_centerline(internal, fld, x_plane=x_plane)

    geom = _geometry_mask_xz(Y, Z, x_plane, r_branch, zjct=zjct)
    img = np.where(geom & np.isfinite(img), img, np.nan)

    # Mask tiny isolated "dead-zone" orphan cells that snappyHexMesh can leave
    # behind, which stay at their initial-condition H2 ~= 1.0 forever.  These
    # are always small pockets far from the injection footprint and have no
    # physical meaning; visually they look like speckled yellow dots.
    orphan = (img > 0.5) & (Y < R_MAIN) & (np.abs(Z - zjct) > r_branch + 0.05)
    img = np.where(orphan, np.nan, img)

    # Colormap range: 99.5th percentile of H2 inside the main pipe downstream
    valid = geom & (np.abs(Y) < R_MAIN) & (Z > Z_JCT + 0.3) & np.isfinite(img)
    vmax = float(np.nanpercentile(img[valid], 99.5)) if valid.sum() > 0 else 0.1
    vmax = max(vmax, 1.0e-6)

    fig, ax = plt.subplots(figsize=(14, 7))
    img_m = np.ma.array(img, mask=~np.isfinite(img))
    pcm = ax.pcolormesh(Z, Y, img_m, cmap=CMAP_H2, vmin=0.0, vmax=vmax,
                        shading="auto")
    for zs in Z_STATIONS + [L_MAIN - 0.01]:
        ax.axvline(zs, color="#f1c40f", lw=2.0, alpha=0.9)
    ax.set_aspect("equal")
    ax.set_xlabel("z [m]"); ax.set_ylabel("y [m]")
    ax.set_xlim(0.0, L_MAIN)
    ax.set_ylim(-R_MAIN - 0.02, R_MAIN + 1.20)
    ax.set_title(
        f"Longitudinal centreline slice — {fld} "
        f"(vmax={vmax:.3g}); yellow = R5 sampling stations"
    )
    cbar = fig.colorbar(pcm, ax=ax, orientation="horizontal",
                        fraction=0.035, pad=0.08)
    cbar.set_label(f"{fld}  [mass fraction]")
    fig.tight_layout()
    fig.savefig(str(out), dpi=140)
    plt.close(fig)
    print(f"  wrote {out.name}")


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

    # Pick up the per-case branch radius from case_info.json so the geometry
    # mask for the longitudinal slice matches this specific DoE case.
    import json
    info = {}
    info_path = args.case / "case_info.json"
    if info_path.exists():
        try:
            info = json.loads(info_path.read_text())
        except Exception:
            info = {}
    r_branch = float(info.get("D2_m", 0.10)) / 2.0
    z_jct    = float(info.get("ZJCT",  Z_JCT))

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

    print(f"Wrote 4 figures under {outdir}")


if __name__ == "__main__":
    main()
