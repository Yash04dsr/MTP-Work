# DoE Campaign Plan — 60 deg T-junction (top injection), (d/D, HBR) sweep

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
| Injection angle | **60 deg** (tilted upstream, top injection) |
| Main pipe bulk velocity | 10 m s⁻¹ (fixed) |
| Solver | `rhoReactingBuoyantFoam` (transient, k-ω SST) |

HBR is derived from (d/D, VR) via the volumetric-flow identity

\[
HBR \;=\; \frac{Q_\text{branch}}{Q_\text{main}+Q_\text{branch}}
\;=\; \frac{(d/D)^2 \, VR}{1 + (d/D)^2 \, VR}
\]

The design is produced by `lhs_design.py`; reproducible via **seed 60**.

## 2. Base case origin

This 60-degree base is derived from the validated **30-degree top-injection** base
(`openfoam_case_rans_doe_30deg_base`).  The `generateSTL.py` and `stamp_cases.py`
are fully parameterised by `ALPHA_DEG`; the only change is the default angle
from 30 → 60 in `stamp_cases.py`.

All mesh, solver, and post-processing settings are identical to the 30-degree
and 90-degree campaigns.

## 3. Directory layout on the compute host

```
~/openfoam_case_rans_doe_60deg_base/     <-- the frozen DoE base template
    0/              (tokenised BCs ; tokens start with '@')
    constant/       (thermophysics, turbulence, transport)
    system/         (blockMesh, snappy, controlDict with R4/R5)
    generateSTL.py  (env-var driven : D1 / D2 / Z_JCT / L_MAIN / ALPHA_DEG)
    scripts/        (clip_stls.py for half-domain STLs)
    doe/
        lhs_design.py      <-- produces doe_design.csv (seed 60)
        stamp_cases.py     <-- materialises case_01..10/
        run_doe.sh         <-- resumable sequential runner
        doe_design.csv     <-- the 10-point DoE
        PLAN_DOE.md        <-- this file

~/openfoam_case_rans_doe_60deg/          <-- produced by the workflow
    doe_cases/
        case_01/  ...  case_10/    (stamped, ready-to-run)
        doe_design.csv             (for provenance)
    doe_results/
        case_01/             (metrics + log + figures + postProc tarball)
        ...
```

## 4. Run-book

On the compute host, inside a tmux session:

```bash
# one-time: copy the 60-degree base template to the compute host
rsync -avz  doe_base_60deg/  doe-pri:~/openfoam_case_rans_doe_60deg_base/

# on the compute host:
ssh doe-pri
mkdir -p ~/openfoam_case_rans_doe_60deg
cd ~/openfoam_case_rans_doe_60deg_base/doe

# generate the design (already done, but reproducible)
python3 lhs_design.py --seed 60 --outdir .

# stamp the 10 cases
python3 stamp_cases.py \
    --design doe_design.csv \
    --base   .. \
    --cases  ~/openfoam_case_rans_doe_60deg/doe_cases \
    --overwrite

# launch the campaign (in tmux)
tmux new -s doe60
cd ~/openfoam_case_rans_doe_60deg_base/doe
./run_doe.sh 2>&1 | tee run_doe.log
```

To resume after a crash or reboot:

```bash
tmux attach -t doe60
# or if detached:
cd ~/openfoam_case_rans_doe_60deg_base/doe
./run_doe.sh 2>&1 | tee -a run_doe.log    # skips cases with SIM_DONE
```

## 5. Resilience guarantees

- Each completed case writes a sentinel `SIM_DONE` file. The runner skips cases already flagged.
- Each completed case has its **full result set** (log, metrics CSV, figures, postProcessing tarball) copied to `doe_results/case_NN/`.
- Failed cases write `SIM_FAILED` + last 200 log lines. The runner continues to the next case.

## 6. Reproducibility

- LHS seed: `60` (see `lhs_design.py --seed`).
- Solver / turbulence / BC versions are fixed in `doe_base/`; changes to the base require re-stamping all cases.
- Every case directory carries `case_info.json` with the exact (d/D, HBR, VR, …) for that case.
