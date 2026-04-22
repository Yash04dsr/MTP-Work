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
    slc = internal.slice(normal="x", origin=(0.0, 0.0, 4.6))
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
    return internal, internal.slice(normal="x", origin=(0.0, 0.0, 4.6))


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


def fig_velocity_xz(ds, out: Path):
    internal = get_internal(ds)
    U = np.asarray(internal.cell_data["U"])
    internal["|U|"] = np.linalg.norm(U, axis=1)
    slc = internal.slice(normal="x", origin=(0.0, 0.0, 4.6))
    sbar = dict(SBAR, title="|U|  [m/s]")
    p = pv.Plotter(off_screen=True, window_size=WIDE)
    p.set_background("white")
    # Clip to 99th percentile to avoid a single stray near-wall spike swallowing
    # the whole colormap.
    arr = np.asarray(slc.cell_data.get("|U|", slc.point_data.get("|U|")))
    if arr is None or arr.size == 0:
        slc["|U|"] = np.linalg.norm(np.asarray(slc.cell_data["U"]), axis=1)
        arr = np.asarray(slc.cell_data["|U|"])
    vmax = float(np.nanpercentile(arr, 99.5))
    p.add_mesh(slc, scalars="|U|", cmap=CMAP_SPEED, clim=[0.0, vmax],
               scalar_bar_args=SBAR, show_edges=False)
    p.camera_position = camera_xz_slice()
    p.camera.zoom(1.25)
    add_text(p, "Velocity magnitude  U  (m/s)  —  x=0 slice")
    save(p, out)


def fig_pressure_xz(ds, out: Path, t: float):
    internal, slc = _slice_x0(ds)
    p_mean = float(np.mean(np.asarray(internal.cell_data["p_rgh"])))
    slc["p_rgh_gauge"] = np.asarray(slc.cell_data["p_rgh"]) - p_mean
    rng = float(np.nanpercentile(np.abs(np.asarray(slc.cell_data["p_rgh_gauge"])), 99.0))
    rng = max(rng, 1.0e2)
    p = pv.Plotter(off_screen=True, window_size=WIDE)
    p.set_background("white")
    p.add_mesh(slc, scalars="p_rgh_gauge", cmap=CMAP_PRESS, clim=[-rng, rng],
               scalar_bar_args=SBAR, show_edges=False)
    p.camera_position = camera_xz_slice()
    p.camera.zoom(1.25)
    add_text(p, f"p_rgh − {p_mean/1e6:.3f} MPa  [Pa]   —  x=0 slice  (t = {t:g} s)")
    save(p, out)


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

    print("[4/7] fig_H2_xz")
    fig_scalar_xz(ds, "H2", out / "fig_H2_xz.png",
                  clim=[0.0, 0.5], cmap=CMAP_H2,
                  title=f"Y_H2 (H2 mass fraction, 0–0.5)  —  x=0 slice  (t = {t:g} s)")

    print("[5/7] fig_H2_outlet")
    fig_H2_outlet(ds, out / "fig_H2_outlet.png")

    print("[6/7] fig_velocity_xz + fig_pressure_xz")
    fig_velocity_xz(ds, out / "fig_velocity_xz.png")
    fig_pressure_xz(ds, out / "fig_pressure_xz.png", t)

    print("[7/7] fig_streamlines")
    fig_streamlines(ds, case, out / "fig_streamlines.png")

    print("DONE.")


if __name__ == "__main__":
    main()
