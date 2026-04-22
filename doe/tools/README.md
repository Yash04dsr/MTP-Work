# doe/tools

Reusable post-processing for every OpenFOAM case in the DoE campaign.

## Contents

| Script | Purpose | Run time |
|---|---|---|
| `all_metrics.py` | Multi-weighting CoV (area / mass-flux / volume-flux × time-averaged-field / per-snapshot / time-series), Δp variants (static / gauge / total), mass balance. Writes `ALL_METRICS.md` + `all_metrics.csv`. | ~10 s/case |
| `make_figures.py` | Standard figure pack (geometry, mesh slice, H₂ field, outlet face, velocity, pressure, streamlines) via PyVista. Writes 7 PNGs. | ~5 s/case |

## Environment

`all_metrics.py` — pure Python, stdlib only. No extra dependencies.

`make_figures.py` — needs PyVista + VTK:

```bash
python3 -m venv ~/.venvs/pv
~/.venvs/pv/bin/pip install pyvista numpy matplotlib
```

On headless machines, PyVista uses VTK's OSMesa backend automatically when
`PYVISTA_OFF_SCREEN=true` (the script sets this).

## Usage (per case)

```bash
CASE=~/openfoam_case_rans_medium
OUT=doe/results/medium

# metrics
python3 doe/tools/all_metrics.py "$CASE" "$OUT"

# figures
~/.venvs/pv/bin/python doe/tools/make_figures.py "$CASE" "$OUT/figures"
```

## DoE integration

The DoE case runner should call both scripts as the last step of each case,
so that results are archived *before* the runner moves on to the next case
(crash resilience — see `PLAN_DOE.md` §5). A per-case directory layout:

```
doe/results/case_<NN>/
  ALL_METRICS.md         # written by all_metrics.py
  all_metrics.csv        # written by all_metrics.py
  figures/
    fig_geometry.png
    fig_mesh_xz.png
    fig_H2_xz.png
    fig_H2_outlet.png
    fig_velocity_xz.png
    fig_pressure_xz.png
    fig_streamlines.png
  parameters.json        # d/D, VR, HBR, injection angle (from LHS design)
```

The master aggregation script (to be added) will pull the `all_metrics.csv`
from every case and join it with `parameters.json` to produce the DoE response
surface dataset.
