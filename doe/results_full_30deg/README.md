# `doe/results_full_30deg/` -- 30 deg DoE results

10-case Latin Hypercube DoE of an H$_2$/CH$_4$ T-junction with the branch
inclined at 30 deg to the main pipe.  Solved with `rhoReactingBuoyantFoam`
(variable-density transient, k-$\omega$ SST) on the same fluid model and
hardened numerics as the 90 deg sanity case in `doe/results_full/`.

9 of 10 cases ran to t = 1.2 s.  case_04 was intentionally paused at
t = 0.215 s (saved to allow resumption later) so the rest of the campaign
could finish on schedule -- raw fields are kept on the compute host.

## Layout

```
results_full_30deg/
+-- cases/
|   +-- case_NN/
|       +-- case_info.json          # design parameters (d/D, HBR, VR, ...)
|       +-- case.env                # solver env (ALPHA_DEG, U_BRANCH, ...)
|       +-- metrics_out/
|       |   +-- all_metrics.csv     # 3 snapshots + AVG row, all weights
|       |   \-- ALL_METRICS.md      # human-readable per-case summary
|       \-- figures/                # PyVista (VTK) renders -- equivalent to
|           |                       # ParaView; read directly from the
|           |                       # symmetryPlane patch, no kNN, no mask
|           +-- fig_geometry.png    # STL patches in isometric view
|           +-- fig_mesh_xz.png     # cell faces on the x=0 symmetry plane
|           +-- fig_H2_xz.png       # Y_H2 on the symmetry plane (bulk-pipe
|           |                       #   colour range; branch H2=1 saturates)
|           +-- fig_H2_outlet.png   # Y_H2 on outlet face, mirrored across
|           |                       #   x=0 to show the FULL physical circle
|           +-- fig_velocity_xz.png # |U| (bulk-pipe range; jet saturates)
|           +-- fig_pressure_xz.png # p_rgh gauge (bulk-IQR colour range)
|           \-- fig_streamlines.png # streamtraces from main + branch inlets
+-- summary/
|   +-- doe_summary_30deg.csv       # joined design + metrics, machine-readable
|   +-- DOE_SUMMARY_30DEG.md        # text summary with best/worst cases
|   +-- GALLERY_30DEG.md            # markdown gallery for browsing on GitHub
|   +-- fig_scatter_CoV_mass_vs_dD.png
|   +-- fig_scatter_CoV_mass_vs_VR.png
|   +-- fig_scatter_CoV_mass_vs_HBR.png
|   +-- fig_scatter_dP_vs_HBR.png
|   +-- fig_scatter_dP_vs_VR.png
|   +-- fig_CoV_heatmap_dD_VR.png
|   +-- fig_dP_heatmap_dD_VR.png
|   \-- fig_pareto_dP_vs_CoV.png
+-- tools/
|   +-- all_metrics.py              # the per-case post-processor (numpy only)
|   +-- aggregate_30deg.py          # the DoE-wide aggregator + plotter
|   \-- make_figures.py             # PyVista figure pack (per case, 7 PNG)
\-- doe_design.csv                  # the 10-row LHS design used for stamping
```

## Reproducing the figures locally

```bash
# create a venv with the deps
python3 -m venv .venv
.venv/bin/pip install pyvista numpy matplotlib scipy

# per-case metrics
for n in 01 02 03 05 06 07 08 09 10; do
    .venv/bin/python tools/all_metrics.py cases/case_${n} \
        --outdir cases/case_${n}/metrics_out
done

# DoE-wide pack
.venv/bin/python tools/aggregate_30deg.py \
    --design doe_design.csv \
    --cases  cases \
    --out    summary

# per-case figure packs (needs the reconstructed t=1.2 fields, which are NOT in
# this repo because of size; pull them with rsync from the compute host first)
for n in 01 02 03 05 06 07 08 09 10; do
    .venv/bin/python tools/make_figures.py cases/case_${n} \
        cases/case_${n}/figures --time 1.2
done
```

## Headline numbers

| case | d/D | HBR | VR | CoV (mass) | $\|\Delta p\|$ kPa |
|---:|---:|---:|---:|---:|---:|
| 01 | 0.196 | 0.184 | 5.84 | **0.005** | 3.32 |
| 02 | 0.196 | 0.060 | 1.64 | 0.384 | 2.13 |
| 03 | 0.252 | 0.078 | 1.33 | 0.278 | 1.89 |
| 04 | 0.252 | 0.195 | 3.81 | (paused at t=0.215 s) | -- |
| 05 | 0.296 | 0.098 | 1.24 | 0.296 | 3.31 |
| 06 | 0.296 | 0.187 | 2.61 | 0.087 | **0.68** |
| 07 | 0.382 | 0.142 | 1.14 | 0.238 | 3.21 |
| 08 | 0.382 | 0.092 | 0.69 | 0.326 | 1.94 |
| 09 | 0.396 | 0.130 | 0.95 | 0.306 | 3.61 |
| 10 | 0.396 | 0.112 | 0.81 | 0.343 | 2.75 |

* **Best mixing** : case_01, CoV = 0.5% (well below the 5% industry target).
* **Cheapest pumping** : case_06, $|\Delta p|$ = 0.68 kPa.
* **Pareto winners** : case_01 and case_06 (see `summary/fig_pareto_dP_vs_CoV.png`).

The single dominant effect on mixing is the velocity ratio VR = $u_{branch}/u_{main}$:
the case with VR = 5.8 mixes 70x better than the cases with VR < 1.5 at comparable d/D.

## Notes on the rendering pipeline (`tools/make_figures.py`)

PyVista is used as the rendering library; under the hood it drives the same
VTK pipeline that ParaView uses (same `vtkOpenFOAMReader`, same plane-cutter,
same scalar-bar widget).  The output is pixel-equivalent to a ParaView
screenshot taken with the same camera and colour map.

The centreline figures (`fig_H2_xz`, `fig_velocity_xz`, `fig_pressure_xz`,
`fig_mesh_xz`) read the **symmetryPlane patch (`sym`) directly** -- the patch
IS the 2-D cell mesh at x = 0, so we get face-interpolated values with no
kNN/IDW step and no analytical pipe-shape mask.  If a case is missing the
`sym` patch (legacy or full-domain runs) we fall back to a triangulated VTK
slice on a triangulated copy of the volume mesh, which avoids the polyhedral
non-conformal "white-notch" gaps.

Field colour ranges are set from the **bulk fluid only** (cells outside the
analytical branch volume) so the dilution gradient and wake structure are
visible -- the branch (H2=1.0) and the high-speed jet (60-150 m/s) saturate
at the top of the colour map.  Orphan cells stuck at their initial-condition
value (snappyHexMesh occasionally leaves a few of these) are filtered with a
spatially-aware cell-extract before rendering.

`fig_H2_outlet.png` is mirrored across x = 0 so the outlet plane is shown as
the full physical circle, not the half-disk of the simulated half-domain.
The other 3-D views (geometry, streamlines) are kept on the half-domain to
preserve the symmetry-plane visibility.
