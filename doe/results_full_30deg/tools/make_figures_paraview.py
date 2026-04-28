#!/usr/bin/env pvpython
"""make_figures_paraview.py -- 7-figure pack rendered via ParaView 6 / pvpython.

Drop-in replacement for the PyVista make_figures.py.  Same data sources, same
camera framing -- but rendered through ParaView's native pipeline (multi-
sample anti-aliasing, FXAA, ParaView light kit, the standard "Cool to Warm",
"Viridis", "Plasma" colour-table presets and the ParaView scalar-bar widget)
so the output has the publication look that supervisors recognise.

Run with:

    /Applications/ParaView-6.1.0.app/Contents/bin/pvpython \\
        tools/make_figures_paraview.py <case_dir> <out_dir> [--time T]

Produces (PNG, 1600x800 / 900x900 unless noted):
    fig_geometry.png        STL patches in isometric view
    fig_mesh_xz.png         sym-patch faces (the x=0 cell footprint)
    fig_H2_xz.png           Y_H2 on the sym patch, viridis, bulk-pipe range
    fig_H2_outlet.png       Y_H2 on outlet patch, reflected to full circle
    fig_velocity_xz.png     |U| on the sym patch, plasma, bulk-pipe range
    fig_pressure_xz.png     gauge p_rgh on the sym patch, cool-to-warm
    fig_streamlines.png     streamtraces seeded from both inlets

The centreline figures read the symmetryPlane patch ("sym") directly via
ExtractBlock on /Root/patch/sym -- the patch IS the 2-D cell mesh at x = 0,
so face values are face-interpolated, no kNN, no analytical mask.  Colour
ranges are set from the bulk fluid only (numpy fetched up front), so the
branch (H2=1) and the high-speed jet saturate at the top of the colourmap
and the main-pipe gradient is the focus.
"""
from __future__ import annotations

import argparse
import builtins
import json
import math
import sys
from pathlib import Path

# pvpython injects numpy_interface algorithms into the globals so a bare
# min(a, b) / max(a, b) ends up calling vtkmodules.numpy_interface algorithms
# which expect (array, axis).  Keep explicit references to the real builtins.
_min = builtins.min
_max = builtins.max
_clip = lambda v, lo, hi: _max(lo, _min(hi, v))  # noqa: E731

import numpy as np  # noqa: E402

from paraview.simple import (  # noqa: E402
    Calculator,
    ColorBy,
    CreateView,
    Delete,
    ExtractBlock,
    GetColorTransferFunction,
    GetOpacityTransferFunction,
    GetScalarBar,
    Hide,
    OpenDataFile,
    PointSource,
    Reflect,
    Render,
    ResetCamera,
    SaveScreenshot,
    Show,
    STLReader,
    StreamTracer,
    UpdatePipeline,
    servermanager,
)


# ---------------------------------------------------------------------------
# Geometry / window constants -- same as the PyVista version so the two
# pipelines can be compared figure-for-figure.
# ---------------------------------------------------------------------------
R_MAIN_HALF = 0.23
L_MAIN_HALF = 6.90
Z_JCT_HALF  = 2.30

WIDE   = [1600, 800]
SQUARE = [900, 900]
ASPECT_WIDE = WIDE[0] / WIDE[1]   # = 2.0

PATCH_COLORS = {
    "wall":         [0.71, 0.71, 0.71],
    "main_inlet":   [0.16, 0.65, 0.27],
    "branch_inlet": [0.90, 0.49, 0.13],
    "outlet":       [0.75, 0.22, 0.17],
}


# ---------------------------------------------------------------------------
# View / scalar-bar / camera helpers
# ---------------------------------------------------------------------------
def setup_view(size=WIDE):
    """Create a render view with ParaView's standard quality settings.

    Note: MultiSamples > 0 in ParaView 6.1 on macOS triggers a renderer bug
    that drops the background to black.  We rely on FXAA only -- which is a
    post-process pass and therefore unaffected.
    """
    view = CreateView("RenderView")
    view.ViewSize = list(size)
    view.UseFXAA = 1
    view.MultiSamples = 0
    try:
        view.UseToneMapping = 0
    except Exception:
        pass
    try:
        view.OrientationAxesVisibility = 0
    except Exception:
        pass
    try:
        view.BackgroundColorMode = "Single Color"
    except Exception:
        pass
    view.UseColorPaletteForBackground = 0
    view.Background  = [1.0, 1.0, 1.0]
    try:
        view.Background2 = [1.0, 1.0, 1.0]
    except Exception:
        pass
    return view


def configure_lut(field: str, preset: str, value_range, *, log_scale=False):
    """Apply a colour-table preset and clamp the LUT to value_range."""
    lut = GetColorTransferFunction(field)
    lut.ApplyPreset(preset, True)
    if log_scale:
        lut.UseLogScale = 1
    lut.RescaleTransferFunction(value_range[0], value_range[1])
    pwf = GetOpacityTransferFunction(field)
    pwf.RescaleTransferFunction(value_range[0], value_range[1])
    return lut


def show_scalar_bar(view, lut, title: str):
    sbar = GetScalarBar(lut, view)
    sbar.Visibility = 1
    sbar.Title = title
    sbar.ComponentTitle = ""
    sbar.Orientation = "Horizontal"
    sbar.WindowLocation = "Lower Center"
    sbar.ScalarBarLength = 0.55
    sbar.ScalarBarThickness = 16
    sbar.LabelColor = [0.0, 0.0, 0.0]
    sbar.TitleColor = [0.0, 0.0, 0.0]
    sbar.LabelFontSize = 14
    sbar.TitleFontSize = 14
    sbar.AutomaticLabelFormat = 1   # PV picks a sensible default
    sbar.DrawTickLabels = 1
    sbar.DrawTickMarks = 1
    return sbar


def setup_xz_camera(view, source, *, margin: float = 1.05):
    """Parallel projection looking along -x at the x = 0 plane."""
    UpdatePipeline(proxy=source)
    bounds = source.GetDataInformation().GetBounds()
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    yc = 0.5 * (ymin + ymax)
    zc = 0.5 * (zmin + zmax)
    z_range = zmax - zmin
    y_range = ymax - ymin
    scale = _max(z_range / ASPECT_WIDE, y_range) * 0.5 * margin

    view.CameraPosition    = [-2.0, yc, zc]
    view.CameraFocalPoint  = [0.0, yc, zc]
    view.CameraViewUp      = [0.0, 1.0, 0.0]
    view.CameraParallelProjection = 1
    view.CameraParallelScale = scale


def setup_iso_camera(view):
    view.CameraParallelProjection = 0
    view.CameraPosition   = [-5.5, 3.0, -3.5]
    view.CameraFocalPoint = [0.0, 0.35, 3.45]
    view.CameraViewUp     = [0.0, 1.0, 0.0]
    # Wide clipping range so the whole pipe is inside the frustum.
    view.CameraParallelScale = 4.0
    view.CenterOfRotation = [0.0, 0.35, 3.45]


def setup_outlet_camera(view):
    cam_z = L_MAIN_HALF + 1.5
    view.CameraPosition   = [0.0, 0.0, cam_z]
    view.CameraFocalPoint = [0.0, 0.0, L_MAIN_HALF]
    view.CameraViewUp     = [0.0, 1.0, 0.0]
    view.CameraParallelProjection = 0


def save_view(view, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Render(view)
    SaveScreenshot(str(path), view,
                   ImageResolution=view.ViewSize,
                   TransparentBackground=0,
                   CompressionLevel="2")
    sz_kb = path.stat().st_size / 1024.0
    print(f"  wrote {path.name}  ({sz_kb:.1f} KB)")


# ---------------------------------------------------------------------------
# Multiblock helpers: ExtractBlock returns a vtkMultiBlockDataSet containing
# a single leaf -- pull cell-data out of the leaf as a numpy array for our
# numerical statistics (vmax, IQR, p_mean).
# ---------------------------------------------------------------------------
def _is_leaf(o) -> bool:
    """Return True if `o` is a real dataset with cells (not a MultiBlock)."""
    return hasattr(o, "GetCell") and not hasattr(o, "GetNumberOfBlocks")


def _walk_leaves(o):
    """Yield every PolyData/UnstructuredGrid leaf inside a MultiBlock tree."""
    if _is_leaf(o):
        yield o
        return
    if hasattr(o, "GetNumberOfBlocks"):
        for i in range(o.GetNumberOfBlocks()):
            child = o.GetBlock(i)
            if child is None:
                continue
            yield from _walk_leaves(child)


def fetch_leaf_cell_array(source, name: str):
    """Return the cell-data array `name` from the first non-empty leaf."""
    from vtkmodules.util.numpy_support import vtk_to_numpy as v2n
    obj = servermanager.Fetch(source)
    for leaf in _walk_leaves(obj):
        arr = leaf.GetCellData().GetArray(name)
        if arr is None:
            continue
        a = v2n(arr).astype(float)
        if a.size:
            return a
    return None


def fetch_leaf_cell_centers(source):
    """Return cell-centre coordinates from the first non-empty leaf as (N, 3)."""
    obj = servermanager.Fetch(source)
    for leaf in _walk_leaves(obj):
        nc = leaf.GetNumberOfCells()
        if nc == 0:
            continue
        ctrs = np.zeros((nc, 3), dtype=float)
        for i in range(nc):
            bb = [0.0] * 6
            leaf.GetCell(i).GetBounds(bb)
            ctrs[i] = ((bb[0] + bb[1]) * 0.5,
                       (bb[2] + bb[3]) * 0.5,
                       (bb[4] + bb[5]) * 0.5)
        return ctrs
    return None


def in_branch_mask(centers, *, alpha_deg, r_branch, zjct,
                   l_branch=1.40, slack=0.05):
    a_rad = math.radians(alpha_deg)
    nb = np.array([0.0, math.sin(a_rad), -math.cos(a_rad)])
    base = np.array([0.0, R_MAIN_HALF, zjct])
    d = centers - base
    s = d @ nb
    perp = d - np.outer(s, nb)
    rperp = np.linalg.norm(perp, axis=1)
    return ((s >= -slack) & (s <= l_branch + slack)
            & (rperp < r_branch * 1.05))


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def fig_geometry(case_dir: Path, out: Path):
    view = setup_view(WIDE)
    try:
        view.OrientationAxesVisibility = 1
        view.OrientationAxesLabelColor = [0.0, 0.0, 0.0]
    except Exception:
        pass
    tri_dir = case_dir / "constant" / "triSurface"
    for name, color in PATCH_COLORS.items():
        stl = tri_dir / f"{name}.stl"
        if not stl.exists():
            continue
        reader = STLReader(FileNames=[str(stl)])
        UpdatePipeline(proxy=reader)
        d = Show(reader, view)
        d.Representation = "Surface"
        d.AmbientColor = color
        d.DiffuseColor = color
        d.Specular = 0.15
        d.SpecularPower = 30.0
        d.Opacity = 0.40 if name == "wall" else 0.95

    setup_iso_camera(view)
    save_view(view, out)
    Delete(view)


def fig_mesh_xz(reader, out: Path):
    view = setup_view(WIDE)
    sym = ExtractBlock(Input=reader, Selectors=["//sym"])
    UpdatePipeline(proxy=sym)
    d = Show(sym, view)
    d.Representation = "Surface With Edges"
    d.DiffuseColor = [1.0, 1.0, 1.0]
    d.AmbientColor = [1.0, 1.0, 1.0]
    d.EdgeColor    = [0.20, 0.20, 0.20]
    d.LineWidth    = 0.5
    d.Specular     = 0.0
    setup_xz_camera(view, sym)
    save_view(view, out)
    Hide(sym, view)
    Delete(view)


def fig_H2_xz(reader, out: Path, *, alpha_deg, r_branch, zjct):
    view = setup_view(WIDE)
    sym = ExtractBlock(Input=reader, Selectors=["//sym"])
    UpdatePipeline(proxy=sym)

    h2 = fetch_leaf_cell_array(sym, "H2")
    ctrs = fetch_leaf_cell_centers(sym)
    if h2 is not None and ctrs is not None:
        in_br = in_branch_mask(ctrs, alpha_deg=alpha_deg,
                               r_branch=r_branch, zjct=zjct)
        bulk = h2[(~in_br) & (h2 < 0.5)]
        if bulk.size:
            vmax_bulk = float(np.nanpercentile(bulk, 99.0))
        else:
            vmax_bulk = 0.05
        vmax = float(_clip(_max(vmax_bulk * 2.5, 0.05), 0.05, 0.5))
    else:
        vmax = 0.30

    d = Show(sym, view)
    d.Representation = "Surface"
    ColorBy(d, ("CELLS", "H2"))
    d.SetScalarBarVisibility(view, True)
    lut = configure_lut("H2", "Viridis", (0.0, vmax))
    show_scalar_bar(view, lut,
                    "Y_H2 (mass fraction) -- bulk range; branch H2=1 saturates")

    setup_xz_camera(view, sym)
    save_view(view, out)
    Hide(sym, view)
    Delete(view)


def fig_H2_outlet(reader, out: Path):
    view = setup_view(SQUARE)
    outlet = ExtractBlock(Input=reader, Selectors=["//outlet"])
    UpdatePipeline(proxy=outlet)

    mirror = Reflect(Input=outlet, Plane="X Min", Center=0.0, CopyInput=1)
    UpdatePipeline(proxy=mirror)

    h2 = fetch_leaf_cell_array(mirror, "H2")
    if h2 is not None and h2.size:
        vmin = float(np.nanmin(h2))
        vmax = float(np.nanmax(h2))
        if vmax - vmin < 1e-6:
            vmax = vmin + 1e-3
    else:
        vmin, vmax = 0.0, 0.05

    d = Show(mirror, view)
    d.Representation = "Surface"
    ColorBy(d, ("CELLS", "H2"))
    d.SetScalarBarVisibility(view, True)
    lut = configure_lut("H2", "Viridis", (vmin, vmax))
    show_scalar_bar(view, lut, "Y_H2 (mass fraction)")
    setup_outlet_camera(view)
    save_view(view, out)
    Hide(mirror, view)
    Delete(view)


def fig_velocity_xz(reader, out: Path, *, alpha_deg, r_branch, zjct):
    view = setup_view(WIDE)
    sym = ExtractBlock(Input=reader, Selectors=["//sym"])
    UpdatePipeline(proxy=sym)

    speed = Calculator(Input=sym)
    speed.AttributeType = "Cell Data"
    speed.ResultArrayName = "U_mag"
    speed.Function = "mag(U)"
    UpdatePipeline(proxy=speed)

    u_arr = fetch_leaf_cell_array(speed, "U_mag")
    ctrs = fetch_leaf_cell_centers(speed)
    if u_arr is not None and ctrs is not None:
        in_br = in_branch_mask(ctrs, alpha_deg=alpha_deg,
                               r_branch=r_branch, zjct=zjct)
        bulk = u_arr[~in_br]
        if bulk.size:
            q1, q3 = np.nanpercentile(bulk, [25.0, 75.0])
            iqr = q3 - q1
            if iqr > 0:
                bulk = bulk[bulk <= q3 + 50.0 * iqr]
            vmax = float(np.nanpercentile(bulk, 99.0))
            vmax = _max(vmax, 1.0)
        else:
            vmax = 30.0
    else:
        vmax = 30.0

    d = Show(speed, view)
    d.Representation = "Surface"
    ColorBy(d, ("CELLS", "U_mag"))
    d.SetScalarBarVisibility(view, True)
    lut = configure_lut("U_mag", "Plasma", (0.0, vmax))
    show_scalar_bar(view, lut,
                    "|U| [m/s] -- bulk range; branch jet saturates")
    setup_xz_camera(view, sym)
    save_view(view, out)
    Hide(speed, view)
    Delete(view)


def fig_pressure_xz(reader, out: Path, *, alpha_deg, r_branch, zjct, t):
    view = setup_view(WIDE)
    sym = ExtractBlock(Input=reader, Selectors=["//sym"])
    UpdatePipeline(proxy=sym)

    p_arr = fetch_leaf_cell_array(sym, "p_rgh")
    if p_arr is not None and p_arr.size:
        q1, q3 = np.nanpercentile(p_arr, [25.0, 75.0])
        iqr = q3 - q1
        if iqr > 0:
            in_band = (p_arr >= q1 - 50.0 * iqr) & (p_arr <= q3 + 50.0 * iqr)
        else:
            in_band = np.ones_like(p_arr, dtype=bool)
        p_mean = float(np.mean(p_arr[in_band])) if in_band.any() else float(np.mean(p_arr))
        rng = _max(8.0 * iqr, 1.0e2) if iqr > 0 else 2.0e3
    else:
        p_mean = 7.0e6
        rng = 5.0e4

    gauge = Calculator(Input=sym)
    gauge.AttributeType = "Cell Data"
    gauge.ResultArrayName = "p_rgh_gauge"
    gauge.Function = f"p_rgh - {p_mean}"
    UpdatePipeline(proxy=gauge)

    d = Show(gauge, view)
    d.Representation = "Surface"
    ColorBy(d, ("CELLS", "p_rgh_gauge"))
    d.SetScalarBarVisibility(view, True)
    lut = configure_lut("p_rgh_gauge", "Cool to Warm", (-rng, rng))
    show_scalar_bar(view, lut,
                    f"p_rgh - {p_mean/1e6:.3f} MPa  [Pa]   (bulk-IQR range)")
    setup_xz_camera(view, sym)
    save_view(view, out)
    Hide(gauge, view)
    Delete(view)


def fig_streamlines(reader, case_dir: Path, out: Path,
                    *, alpha_deg, r_branch, zjct):
    view = setup_view(WIDE)
    try:
        view.OrientationAxesVisibility = 1
        view.OrientationAxesLabelColor = [0.0, 0.0, 0.0]
    except Exception:
        pass
    internal = ExtractBlock(Input=reader, Selectors=["//internalMesh"])
    UpdatePipeline(proxy=internal)

    wall_stl = case_dir / "constant" / "triSurface" / "wall.stl"
    if wall_stl.exists():
        wall = STLReader(FileNames=[str(wall_stl)])
        UpdatePipeline(proxy=wall)
        wd = Show(wall, view)
        wd.Representation = "Surface"
        wd.AmbientColor = PATCH_COLORS["wall"]
        wd.DiffuseColor = PATCH_COLORS["wall"]
        wd.Opacity = 0.10

    a_rad = math.radians(alpha_deg)
    nb = [0.0, math.sin(a_rad), -math.cos(a_rad)]
    base = [0.0, R_MAIN_HALF, zjct]
    L_b  = 1.40 if alpha_deg < 90 else 1.20
    branch_centre = [base[i] + (L_b - 0.05) * nb[i] for i in range(3)]

    main_src = PointSource(Center=[0.0, 0.0, 0.03], NumberOfPoints=24,
                           Radius=0.7 * R_MAIN_HALF)
    UpdatePipeline(proxy=main_src)
    main_stream = StreamTracer(Input=internal, SeedType=main_src)
    main_stream.Vectors = ["CELLS", "U"]
    main_stream.IntegrationDirection = "FORWARD"
    main_stream.MaximumStreamlineLength = 80.0
    main_stream.IntegratorType = "Runge-Kutta 4-5"
    UpdatePipeline(proxy=main_stream)

    br_src = PointSource(Center=branch_centre, NumberOfPoints=16,
                         Radius=0.7 * r_branch)
    UpdatePipeline(proxy=br_src)
    br_stream = StreamTracer(Input=internal, SeedType=br_src)
    br_stream.Vectors = ["CELLS", "U"]
    br_stream.IntegrationDirection = "FORWARD"
    br_stream.MaximumStreamlineLength = 80.0
    br_stream.IntegratorType = "Runge-Kutta 4-5"
    UpdatePipeline(proxy=br_stream)

    main_calc = Calculator(Input=main_stream)
    main_calc.AttributeType = "Point Data"
    main_calc.ResultArrayName = "U_mag"
    main_calc.Function = "mag(U)"
    UpdatePipeline(proxy=main_calc)

    br_calc = Calculator(Input=br_stream)
    br_calc.AttributeType = "Point Data"
    br_calc.ResultArrayName = "U_mag"
    br_calc.Function = "mag(U)"
    UpdatePipeline(proxy=br_calc)

    try:
        from vtkmodules.util.numpy_support import vtk_to_numpy as v2n
        m_obj = servermanager.Fetch(main_calc)
        b_obj = servermanager.Fetch(br_calc)
        speeds = []
        for o in (m_obj, b_obj):
            if hasattr(o, "GetPointData") and o.GetPointData().GetArray("U_mag"):
                speeds.append(v2n(o.GetPointData().GetArray("U_mag")))
        if speeds:
            speeds = np.concatenate(speeds)
            q1, q3 = np.nanpercentile(speeds, [25.0, 75.0])
            iqr = q3 - q1
            bulk = speeds[speeds <= q3 + 50.0 * iqr] if iqr > 0 else speeds
            vmax = float(np.nanpercentile(bulk, 99.0))
            vmax = _max(vmax, 1.0)
        else:
            vmax = 50.0
    except Exception:
        vmax = 50.0

    for stream in (main_calc, br_calc):
        d = Show(stream, view)
        d.Representation = "Surface"
        ColorBy(d, ("POINTS", "U_mag"))
        d.LineWidth = 1.4
    lut = configure_lut("U_mag", "Plasma", (0.0, vmax))
    # Show scalar bar on the LAST display only.
    d.SetScalarBarVisibility(view, True)
    show_scalar_bar(view, lut, "|U| [m/s]")

    setup_iso_camera(view)
    save_view(view, out)
    Delete(view)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", type=Path)
    ap.add_argument("out_dir",  type=Path)
    ap.add_argument("--time", type=float, default=None)
    args = ap.parse_args()

    case = args.case_dir.resolve()
    out  = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    print(f"Case: {case}")
    print(f"Out:  {out}")

    info_path = case / "case_info.json"
    info = {}
    try:
        if info_path.exists():
            info = json.loads(info_path.read_text())
    except Exception:
        info = {}
    alpha_deg = float(info.get("alpha_deg", 90.0))
    z_jct     = float(info.get("ZJCT", Z_JCT_HALF))
    d2        = float(info.get("D2_m",  0.10))
    r_branch  = d2 / 2.0
    print(f"  per-case mask: r_branch={r_branch:.4f} m  "
          f"z_jct={z_jct:.3f} m  alpha={alpha_deg:.1f} deg")

    print("[1/7] fig_geometry")
    fig_geometry(case, out / "fig_geometry.png")

    print("[2/7] loading volume mesh...")
    foam = case / "case.foam"
    foam.touch()
    reader = OpenDataFile(str(foam))
    reader.MeshRegions = [
        "internalMesh",
        "patch/sym",
        "patch/outlet",
    ]
    reader.CellArrays = ["H2", "U", "p_rgh"]
    UpdatePipeline(proxy=reader)

    times = list(reader.TimestepValues)
    t = args.time if args.time is not None else times[-1]
    if t not in times:
        print(f"  warning: t = {t} not in {times}; using last time.")
        t = times[-1]
    reader.UpdatePipeline(time=t)
    print(f"  reading t = {t} s  (all times: {times})")

    print("[3/7] fig_mesh_xz")
    fig_mesh_xz(reader, out / "fig_mesh_xz.png")
    print("[4/7] fig_H2_xz")
    fig_H2_xz(reader, out / "fig_H2_xz.png",
              alpha_deg=alpha_deg, r_branch=r_branch, zjct=z_jct)
    print("[5/7] fig_H2_outlet")
    fig_H2_outlet(reader, out / "fig_H2_outlet.png")
    print("[6/7] fig_velocity_xz + fig_pressure_xz")
    fig_velocity_xz(reader, out / "fig_velocity_xz.png",
                    alpha_deg=alpha_deg, r_branch=r_branch, zjct=z_jct)
    fig_pressure_xz(reader, out / "fig_pressure_xz.png",
                    alpha_deg=alpha_deg, r_branch=r_branch, zjct=z_jct, t=t)
    print("[7/7] fig_streamlines")
    fig_streamlines(reader, case, out / "fig_streamlines.png",
                    alpha_deg=alpha_deg, r_branch=r_branch, zjct=z_jct)

    print("DONE.")


if __name__ == "__main__":
    sys.exit(main())
