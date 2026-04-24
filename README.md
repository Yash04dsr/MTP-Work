# MTP Work — H₂/CH₄ T-Junction Mixing DoE

This repository is the working archive for my MTP (Master's) CFD study of
hydrogen/methane mixing in a T-junction under pipeline-relevant conditions,
using OpenFOAM v2406 (`rhoReactingBuoyantFoam`) with a Latin Hypercube
Design of Experiments (LHS-DoE) over `(d/D, V_R)` at fixed HBR targets.

## Repository layout

```
.
├── doe/                                # all DoE campaign assets
│   ├── doe_base/                       # local base template
│   ├── remote_snapshot/                # snapshot of the remote base templates
│   │   ├── openfoam_case_rans_doe_base/        # 90° injection base
│   │   └── openfoam_case_rans_doe_30deg_base/  # 30° injection base
│   ├── tools/                          # DoE driver scripts (local copies)
│   ├── 30deg_preview/                  # render previews for 30° setup
│   └── results_full/                   # main DoE artefacts
│       ├── cases/case_01 … case_10/    # per-case configs + figures
│       ├── doe_summary/                # aggregated plots + CSV summary
│       ├── tools/                      # post-processing scripts
│       └── make_doe_summary_local.py
├── report/                             # LaTeX report + residual traces
├── openfoam_case/                      # seed single-case template
├── book.md, paper.md, report.*         # write-ups
├── *.pdf                               # reference papers
└── .gitignore
```

## What is committed

For each case `case_XX`:

| Tracked                        | Not tracked (regenerable)              |
|--------------------------------|-----------------------------------------|
| `0/` initial conditions        | processor decompositions (`processor*`) |
| `system/` (OpenFOAM dicts)     | `constant/polyMesh/` (binary, huge)     |
| `constant/` minus polyMesh     | reconstructed time dirs (`1/`, `1.2/`)  |
| `case_info.json`               | `log.*`, `_stash/`, `SIM_DONE`          |
| `postProcessing/*.dat`         | `dynamicCode/`                          |
| `figures/*.png`                | `*.foam` paraview markers               |
| `_stash/all_metrics.csv`       |                                         |
| `Allrun`, `case.env`, `generateSTL.py` |                                 |

To rebuild a case end-to-end:

```bash
cd doe/results_full/cases/case_07
bash Allrun            # regenerates STLs, mesh, decomposes, solves, reconstructs
```

## DoE design (90° injection)

10-point sliced Latin Hypercube over:

| Parameter | Range                      |
|-----------|----------------------------|
| `d/D`     | 0.10 – 0.22                |
| `V_R`     | 1.0 – 6.0                  |
| HBR       | 5% – 20% (derived)         |
| α (inj.)  | 90° (fixed in this campaign) |

Operating point: `p = 6.87 MPa`, `T = 288 K`, main bulk `U = 10 m/s`,
k–ω SST RANS, 16 processors, `endTime = 1.2 s` (≈ 2 flow-throughs on the
R2-shortened 6.9-m pipe), time-averaging over the second half.

## Key metrics

Per case:
- mixing CoV at z = 3, 4, 5, 6 m (downstream planes)
- pressure drop ΔP = p̄(main_inlet) − p̄(outlet)
- Danckwerts intensity of segregation Iₛ
- Re_branch, jet-to-crossflow momentum ratio J, Froude number Fr_D

Aggregated in `doe/results_full/doe_summary/` as bar charts +
`doe_summary.csv`.

## 30° campaign

A parallel campaign with α = 30° (co-flow injection) is set up in
`doe/remote_snapshot/openfoam_case_rans_doe_30deg_base/` with the same DoE
design. Preview renders are in `doe/30deg_preview/`.

## Buoyancy sanity note

Case 01 was re-purposed as a Fr_D ≪ 1 sanity test
(`U_main = 0.5 m/s`, `V_R = 1.0`) to verify that the buoyant decomposition
(`rhoReactingBuoyantFoam`, `constant/g = (0 -9.81 0)`, `perfectGas` EoS)
correctly lets H₂ rise under its own density deficit. At the nominal
operating point Fr_D ≈ 5, so inertia dominates buoyancy — the plume
penetrates downward along the jet; buoyancy only imparts a slow upward
recovery far downstream.

## Tooling

All driver scripts live in `doe/tools/` and `doe/results_full/tools/`:

- `stamp_cases.py` – stamps case templates with DoE tokens
- `run_doe.sh` / `run_doe_30deg.sh` – full pipeline launcher
- `doe_status.sh`, `doe_watch.sh` – live campaign status
- `all_metrics.py` – per-case CoV + ΔP extraction
- `make_figures.py`, `make_distance_figures.py` – visualisation
  (KD-tree resampling + analytical geometry mask; no slicing gaps)

## Environment

- OpenFOAM v2406 on WSL2 Ubuntu 24.04
- 16-core decomposition (`--use-hwthread-cpus`)
- Python 3.11 locally for post-processing (PyVista, Matplotlib, NumPy,
  SciPy cKDTree)

## Author

Yash (IIT Jodhpur, MTP 2025–2026). Supervisor: Prof. Anand Krishnasamy.
