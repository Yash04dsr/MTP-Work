# `doe/results_full_120deg/` - 120 deg DoE scaffold

10-case Latin Hypercube DoE of an H$_2$/CH$_4$ T-junction with the branch
inclined at **120 deg** to the main pipe (i.e. the branch leans 30 deg into
the upstream side relative to the wall normal). Solved with
`rhoReactingBuoyantFoam` (variable-density transient, k-$\omega$ SST) on the
same fluid model and hardened numerics as the 90 deg sanity case in
`doe/results_full/` and the 30 deg campaign in `doe/results_full_30deg/`.

> **Status:** scaffold only. The (d/D, VR, HBR) seed has been stamped from
> the matched-pair design, but the simulations themselves are queued to run
> on the Windows compute host. Per-case `metrics_out/`, `figures/`, and the
> reconstructed time directory (`1.2/`) will land here once each case
> finishes and is rsync'd back from the host.

## Why "matched pair"

The injection-angle sweep (30 deg, 90 deg, 120 deg, 150 deg) reuses the
**same Latin Hypercube design points** in (d/D, VR, HBR) so any difference
between two campaigns is attributable to the angle alone, not to a
re-randomised seed. That makes the cross-campaign analysis in
`doe/cross_campaign/` a clean controlled study. The 120 deg
`doe_design.csv` here was derived row-for-row from
`results_full_30deg/doe_design.csv` with only the `alpha_deg` column
changed to 120.0.

## Layout

```
results_full_120deg/
+-- cases/
|   +-- case_NN/
|       +-- case_info.json     # design parameters (d/D, HBR, VR, alpha=120)
|       +-- case.env           # solver env (ALPHA_DEG=120.0, U_BRANCH, ...)
|       +-- case.foam          # empty marker for ParaView
|       +-- metrics_out/       # filled by tools/all_metrics.py once the case runs
|       \-- figures/           # filled by tools/make_figures.py once the case runs
+-- summary/                   # filled by tools/aggregate_120deg.py
+-- diagnostic/                # ad-hoc inspection plots, mesh-quality dumps, etc.
+-- doe_results/               # remote rsync drop-zone (mirrors compute host)
+-- tools/
|   \-- aggregate_120deg.py    # DoE-wide aggregator + plot pack
+-- doe_design.csv             # the 10-row LHS design (matched-pair seed, alpha=120)
\-- README.md                  # this file
```

`tools/all_metrics.py` and `tools/make_figures.py` are not duplicated in
this folder - they are generic across angles (the figure script reads
`alpha_deg` from `case_info.json` and adapts the analytical branch mask
accordingly), so the 30 deg copies in
`doe/results_full_30deg/tools/` are the canonical versions and can be
invoked directly against the 120 deg cases below.

## Reproducing once the simulations land

```bash
cd "doe"

# 1) per-case post-processing (numpy-only metrics, then figures via PyVista)
for n in 01 02 03 04 05 06 07 08 09 10; do
    python3 results_full_30deg/tools/all_metrics.py \
        results_full_120deg/cases/case_${n} \
        --outdir results_full_120deg/cases/case_${n}/metrics_out
    python3 results_full_30deg/tools/make_figures.py \
        results_full_120deg/cases/case_${n} \
        results_full_120deg/cases/case_${n}/figures \
        --time 1.2
done

# 2) DoE-wide aggregation + summary plots
python3 results_full_120deg/tools/aggregate_120deg.py \
    --design results_full_120deg/doe_design.csv \
    --cases  results_full_120deg/cases \
    --out    results_full_120deg/summary
```

After the 120 deg summary is built, the cross-campaign script can be
extended to load it alongside the 30 deg and 90 deg campaigns - see
`doe/cross_campaign/cross_analysis.py` (`load_30deg`, `load_90deg`; add a
`load_120deg` modelled on `load_30deg`).

## Design points (matched seed, alpha = 120 deg)

| case | slice | d/D | HBR | VR | D2 (m) | U_branch (m/s) |
|---:|---:|---:|---:|---:|---:|---:|
| 01 | 1 | 0.196 | 0.184 | 5.84 | 0.0904 | 58.42 |
| 02 | 1 | 0.196 | 0.060 | 1.64 | 0.0904 | 16.43 |
| 03 | 2 | 0.252 | 0.078 | 1.33 | 0.1159 | 13.30 |
| 04 | 2 | 0.252 | 0.195 | 3.81 | 0.1159 | 38.07 |
| 05 | 3 | 0.296 | 0.098 | 1.24 | 0.1363 | 12.41 |
| 06 | 3 | 0.296 | 0.187 | 2.61 | 0.1363 | 26.14 |
| 07 | 4 | 0.382 | 0.142 | 1.14 | 0.1755 | 11.37 |
| 08 | 4 | 0.382 | 0.092 | 0.69 | 0.1755 | 6.93 |
| 09 | 5 | 0.396 | 0.130 | 0.95 | 0.1820 | 9.53 |
| 10 | 5 | 0.396 | 0.112 | 0.81 | 0.1820 | 8.06 |

`U_main` is fixed at 10 m/s; `Z_JCT = 2.3 m`, `L_MAIN = 6.9 m`,
`D_main = 0.460 m` are inherited from the 30 deg / 90 deg geometry so
the only physical difference between the campaigns is the branch
tilt.

## Notes for the Windows compute host

* On the host, `stamp_cases.py` (under `doe/doe_base/doe/`) reads the
  same `doe_design.csv` shape and stamps the OpenFOAM case templates
  (`0/`, `constant/`, `system/`, `Allrun`, `generateSTL.py`) into each
  `case_NN/`. The `case.env` files written here already carry
  `ALPHA_DEG=120.0`, so `generateSTL.py` will produce the right
  branch tilt without any further edits.
* Mesh-reuse across same-`d/D` cases (the `REUSE_MESH_FROM` env in
  `Allrun`) still applies: cases 01-02, 03-04, 05-06, 07-08, 09-10
  share a `polyMesh` per slice.
