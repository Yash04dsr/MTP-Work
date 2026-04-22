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

    # Compute field range from the last slice (usually most diffuse) if no
    # clim provided.  Shared across all 5 panels so contours are comparable.
    if clim is None:
        last = internal.slice(normal="z", origin=(0, 0, stations[-1]))
        if field not in last.array_names:
            raise SystemExit(f"field {field} not in slice; have {last.array_names}")
        v = last[field]
        clim = (float(v.min()), float(v.max()))

    for k, (z, t) in enumerate(zip(stations, titles)):
        p.subplot(0, k)
        sl = internal.slice(normal="z", origin=(0, 0, z))
        if field not in sl.array_names:
            add_text(p, f"no {field} at z={z:.1f}")
            continue
        sl_full = _mirror(sl)
        p.add_mesh(sl_full, scalars=field, cmap=cmap, clim=clim,
                   show_edges=False, show_scalar_bar=False)
        # Camera looking +z, centred on the plane.
        cam_pos = (0.0,  0.35, z - 1.6)
        p.camera_position = [cam_pos, (0, 0.35, z), (0, 1, 0)]
        p.camera.zoom(1.35)
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


def long_slice_figure(internal, out: Path):
    p = pv.Plotter(off_screen=True, window_size=HALF_HEIGHT)
    p.set_background("white")
    sl = internal.slice(normal="x", origin=(0, 0, 0))   # whole y-z slice
    if "H2" not in sl.array_names and "H2Mean" not in sl.array_names:
        raise SystemExit("no H2 / H2Mean on the x-slice")
    fld = "H2Mean" if "H2Mean" in sl.array_names else "H2"
    p.add_mesh(sl, scalars=fld, cmap=CMAP_H2, clim=(0, 1),
               show_edges=False, show_scalar_bar=True,
               scalar_bar_args=dict(
                   title=fld, color="black", n_labels=5,
                   label_font_size=11, title_font_size=12,
                   vertical=False, position_x=0.22, position_y=0.04,
                   width=0.56, height=0.032, fmt="%.2g"))
    # Sampling-plane overlay (yellow lines at each z).
    for z in Z_STATIONS + [L_MAIN - 0.01]:
        line = pv.Line((0, -R_MAIN - 0.02, z), (0,  R_MAIN + 0.02, z))
        p.add_mesh(line, color="#f1c40f", line_width=3.5, lighting=False)
    p.camera_position = [(-5.0, 0.35, 3.45), (0.0, 0.35, 3.45), (0, 1, 0)]
    p.camera.zoom(1.1)
    add_text(p, f"Longitudinal slice, {fld}; yellow = R5 sampling stations")
    p.screenshot(str(out))
    print(f"  wrote {out.name}")


def outlet_face_figure(ds, out: Path):
    outlet = get_patch(ds, "outlet")
    if outlet is None:
        print("  [warn] no outlet patch -- skipping fig_H2_outlet")
        return
    fld = "H2Mean" if "H2Mean" in outlet.array_names else "H2"
    full = _mirror(outlet)
    p = pv.Plotter(off_screen=True, window_size=SQUARE)
    p.set_background("white")
    p.add_mesh(full, scalars=fld, cmap=CMAP_H2, clim=(0, 1),
               show_edges=False,
               scalar_bar_args=dict(
                   title=fld, color="black", n_labels=5,
                   label_font_size=11, title_font_size=12,
                   vertical=False, position_x=0.20, position_y=0.04,
                   width=0.60, height=0.032, fmt="%.3g"))
    p.camera_position = [(0, 0.35, L_MAIN + 1.5), (0, 0.35, L_MAIN), (0, 1, 0)]
    p.camera.zoom(1.4)
    add_text(p, f"Outlet face, {fld}  (CoV reporting plane)")
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
    long_slice_figure(internal, outdir / "fig_H2_long.png")
    outlet_face_figure(ds, outdir / "fig_H2_outlet.png")

    print(f"Wrote 4 figures under {outdir}")


if __name__ == "__main__":
    main()
