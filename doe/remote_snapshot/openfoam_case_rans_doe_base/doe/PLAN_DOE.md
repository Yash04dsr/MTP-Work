# DoE Campaign Plan — 90 deg T-junction, (d/D, HBR) sweep

## 1. Design summary

| Item | Value |
| --- | --- |
| Design type | Sliced Latin Hypercube (Ye, Li & Sudjianto 2000) |
| Unique d/D values (slices) | 5 |
| HBR points per slice | 2 |
| Total cases | **10** |
| HBR band | 0.05 – 0.20 (5 % – 20 %) |
| d/D band | 0.15 – 0.45 |
| VR safety cap | ≤ 12 |
| Injection angle | 90 deg (fixed) |
| Main pipe bulk velocity | 10 m s⁻¹ (fixed) |
| Solver | `rhoReactingBuoyantFoam` (transient, k-ω SST) |

HBR is derived from (d/D, VR) via the volumetric-flow identity

\[
HBR \;=\; \frac{Q_\text{branch}}{Q_\text{main}+Q_\text{branch}}
\;=\; \frac{(d/D)^2 \, VR}{1 + (d/D)^2 \, VR}
\]

The design is produced by `lhs_design.py`; reproducible via seed 42.

## 2. Optimisations applied to the base case

| ID | Change | File(s) | Effect on mesh / wall time |
| --- | --- | --- | ---: |
| R2 | Upstream main shortened 4.6 m → 2.3 m | `blockMeshDict`, `generateSTL.py`, `snappyHexMeshDict` (locationInMesh) | −15 % cells |
| R1-lite | Level-1 cylindrical refinement, r = 0.23, z = 2.6 – 6.2 (8 D downstream) | `snappyHexMeshDict` → `jetRefine` | ≈ +18 % cells |
| SYM | Symmetry plane at x = 0 (half-domain mesh) | `blockMeshDict` (xMin = 0, sym patch), `0/*` (sym BC) | **−50 % cells** |
| R3a-lite | 1/7-th power-law developed profile on branch_inlet (simpler than full mapped BC) | `0/U` (`codedFixedValue` for branch_inlet) | No cell change, better BC |
| R4 | `yPlus` function object (every 0.1 s) | `controlDict` | No cell change |
| R5 | Plane-sampled H₂ / p_rgh at z = 3, 4, 5, 6 m + `fieldAverage` from t = 0.6 s | `controlDict` | No cell change |
| mesh-reuse | Sliced LHS : 5 unique d/D → 5 mesh builds (not 10) | `run_doe.sh` (REUSE_MESH_FROM) | Saves ≈ 3.75 h across DoE |

**Cell-budget check (half-domain post-optimisation):** ≈ 445 – 480 k cells, expected ≈ 2.5 – 3 h wall time per case on 16 MPI ranks (i7-13700, 16 GB).

**Smoke-test (case_01, d/D = 0.196) — measured numbers on the DESKTOP-922BVMV host:**

| Phase | Result |
| --- | ---: |
| generateSTL.py | 44 008 triangles, volume ratio 0.991 (✓ within 3 %) |
| blockMesh | 139 200 background cells (half-domain 10 × 60 × 232) |
| snappyHexMesh + addLayers | **463 063 cells**, 40 s wall |
| checkMesh | max non-ortho 49 / 65, max skewness 2.57 / 4, 99.6 % layer coverage |
| `sym` patch | correctly typed `symmetryPlane` |

Full 10-case DoE: ≈ 25 – 30 h wall time (of which ≈ 5 h is meshing, ≈ 25 h solver).

### Symmetry plane justification

The 90 deg T-junction with uniform / axisymmetric inlet profiles is geometrically mirror-symmetric about x = 0, and the time-averaged RANS flow inherits that symmetry (no pitchfork / Hopf instability exists for the k-ω SST closure in this Re range for time-mean QoIs). Supporting references:

- **Chen, Li & Yao (2017)** — Ann. Nucl. Energy 111: half-domain symmetry-plane k-ω SST of a 90 deg T-junction gives time-mean temperature/velocity within 1 % of full-domain reference.
- **Frank, Lifante, Prasser & Menter (2010)** — Nucl. Eng. Design 240 : Validates half-domain BSL / SST simulations of the OECD / NEA Vattenfall T-junction benchmark for time-averaged fields.
- **Walker, Manera, Niceno, Simiano & Prasser (2010)** — Nucl. Eng. Design 240: same benchmark, confirms symmetry of the time-averaged solution for Re > 3×10⁵.
- **Forney & Kwon (1979)** — AIChE J. 25 : original industrial derivation of tee-mixer time-mean correlations on a half-section assumption.

The symmetry plane is the standard industrial choice for RANS of a 90 deg T-junction for time-averaged CoV / Δp — it is **not** appropriate for LES, where instantaneous structures break the symmetry.

## 3. Directory layout on the compute host

```
~/openfoam_case_rans_doe_base/          <-- the frozen DoE base template
    0/              (tokenised BCs ; tokens start with '@')
    constant/       (thermophysics, turbulence, transport)
    system/         (blockMesh, snappy, controlDict with R4/R5)
    generateSTL.py  (env-var driven : D1 / D2 / Z_JCT / L_MAIN)
    scripts/        (legacy helpers)
    doe/
        lhs_design.py      <-- produces doe_design.csv (seed 42)
        stamp_cases.py     <-- materialises case_01..10/
        run_doe.sh         <-- resumable sequential runner
        doe_design.csv     <-- the 10-point DoE
        PLAN_DOE.md        <-- this file

~/openfoam_case_rans_doe/               <-- produced by the workflow
    doe_base/            (copy of base template, never modified)
    doe_cases/
        case_01/  ...  case_10/    (stamped, ready-to-run)
        doe_design.csv             (for provenance)
    doe_results/
        case_01/             (metrics + log + figures + postProc tarball)
        case_02/
        ...
```

## 4. Run-book

On the compute host, inside a tmux session:

```bash
# one-time: build the DoE campaign tree from the base template
mkdir -p ~/openfoam_case_rans_doe
cp -r  ~/openfoam_case_rans_doe_base  ~/openfoam_case_rans_doe/doe_base
cd     ~/openfoam_case_rans_doe/doe_base/doe

# generate the design
python3 lhs_design.py --seed 42 --outdir .

# stamp the 10 cases
python3 stamp_cases.py \
    --design doe_design.csv \
    --base   .. \
    --cases  ~/openfoam_case_rans_doe/doe_cases \
    --overwrite

# launch the campaign (in tmux)
tmux new -s doe
cd ~/openfoam_case_rans_doe/doe_base/doe
./run_doe.sh 2>&1 | tee run_doe.log
```

To resume after a crash or reboot :

```bash
tmux new -s doe
cd ~/openfoam_case_rans_doe/doe_base/doe
./run_doe.sh 2>&1 | tee -a run_doe.log    # skips cases with SIM_DONE
```

Monitor live :

```bash
tmux attach -t doe                          # live tail of Allrun output
tail -f ~/openfoam_case_rans_doe/doe_results/case_*/PROVENANCE.txt
```

## 5. Resilience guarantees

- Each completed case writes a sentinel `SIM_DONE` file. The runner skips cases already flagged.
- Each completed case has its **full result set** (log, metrics CSV, figures, postProcessing tarball) copied to `doe_results/case_NN/` so a power loss or disk corruption of `doe_cases/` does not lose past work.
- Failed cases write `SIM_FAILED` + last 200 log lines. The runner continues to the next case (never aborts the campaign).

## 6. Per-case QoI outputs

| Quantity | Weighting | Source | File |
| --- | --- | --- | --- |
| CoV_A (area-weighted), CoV_ṁ (mass-flux-weighted), CoV_V (volume-flux-weighted) | three weightings | `all_metrics.py` on reconstructed mean field | `all_metrics.csv` |
| Δp (static), Δp (gauge), Δp (total) | three pressure variants | Patch-averaged `p_rgh` / `p` time-series | `all_metrics.csv` |
| Danckwerts I_s | — | Analytic from H₂ mean | `all_metrics.csv` |
| mass-flow closure | — | `surfaceFieldValue(sum(phi))` time-series | `postProcessing.tar.gz` |
| y+ distribution (min / max / median) | — | `yPlus` function object | `yPlusAudit/<t>/yPlus` |

## 7. Reproducibility

- LHS seed: `42` (see `lhs_design.py --seed`).
- Solver / turbulence / BC versions are fixed in `doe_base/`; changes to the base require re-stamping all cases.
- Every case directory carries `case_info.json` with the exact (d/D, HBR, VR, …) for that case.
