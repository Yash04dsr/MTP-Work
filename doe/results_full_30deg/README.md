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
|       \-- figures/                # matplotlib + kNN renders (same look as
|           |                       # the 90 deg pack), angle-aware analytical
|           |                       # branch mask + spatially-aware orphan filter
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
|   \-- make_figures.py             # angle-aware figure pack (per case, 7 PNG)
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

Same matplotlib + kNN look as the 90 deg pack so the two campaigns can be
compared figure-for-figure.  The centreline figures (`fig_H2_xz`,
`fig_velocity_xz`, `fig_pressure_xz`) sample the OpenFOAM volume fields at
their cell centres and interpolate them onto a 520 x 1400 (Y, Z) image grid,
then apply an analytical pipe-shape mask:

* `in_main`   -- the disc `x_plane^2 + Y^2 < R_main^2`
* `in_branch` -- the tilted tube around axis
                 `nb = (0, sin(alpha), -cos(alpha))` starting at
                 `(0, R_main, zjct)` and running for `l_branch`,
                 with a `r_branch / tan(alpha)` slack on the
                 negative-`s` side so the perpendicular base of the
                 branch tube is fully drawn at the wall (this removes
                 the visual "gap" between the tilted branch and the
                 plume entering the main pipe).

Reading `alpha_deg` from `case_info.json` makes the same script render 30,
90 and 150 deg cases identically, with the branch tube drawn at the right
angle for each case.

### Why the 30 deg meshes need a tighter orphan filter than 90 deg

The 30 deg `snappyHexMesh` runs leave roughly 1.4 % "orphan" cells -- 10x
more than the 90 deg meshes.  These come in two flavours:

1.  **Frozen-IC cells**: `H2 > 0.5`, `|U| ~ 1000+ m/s`, scattered through
    the upstream pipe (the meshing pipeline never visited them and they
    still carry the initial-condition values).
2.  **Upstream noise cells**: `H2 ~ 0.005-0.05` more than 0.5 m upstream
    of the junction, where physically the plume cannot have reached in
    1.2 s of simulated flow.  These are mesh-refinement boundary
    diffusion / solver overshoot artifacts.

The orphan mask flags both kinds (cells inside the analytical branch
tube are exempt) and is computed once per case.  Crucially, the orphan
cells are excluded from the kNN tree itself rather than NaN'd
post-query: that way every grid point in the rendered image gets a
clean nearest-neighbour answer, and the figures show no white speckles
or stripes.  k = 4 inverse-distance-weighting then produces the smooth
gradient look across the tilted T-junction.

### Colour ranges and the H2 outlet view

Field colour ranges are set from the **bulk fluid only** (main pipe cells
downstream of the junction) so the dilution gradient and wake structure
are the visual focus.  The branch (H2 = 1) and the high-speed jet
saturate at the top of the colour map -- that's expected behaviour and
matches the 90 deg figures.

`fig_H2_outlet` is mirrored across `x = 0` (PyVista `merge` of the original
patch with an x-reflected copy) and rendered with point-data interpolation
(`interpolate_before_map=True`) so the gradient is smooth instead of
flat-shaded cells.
