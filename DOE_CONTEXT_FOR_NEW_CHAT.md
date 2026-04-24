# CFD DoE Context Pack — Hand-off for New Chat / New Angle Campaign

> **Purpose of this document.** This is a **portable, self-contained context pack** you can paste into a fresh AI chat so the assistant immediately understands:
>
> 1. What we're simulating (physics, geometry, BCs, solver) and why.
> 2. How the compute environment is accessed (SSH from Mac → WSL2 on a Windows PC).
> 3. The Design-of-Experiments methodology already validated on the 90° angle.
> 4. Every optimisation, pitfall, and fix that has been baked into the base template.
> 5. How to adapt the validated pipeline to a **different injection angle** on a **different, lower-spec Windows PC**.
>
> Hand this file to the new chat **first**, before asking anything else.

---

## 0. TL;DR for the new AI assistant

We are running a **Design-of-Experiments (DoE) parametric study of hydrogen-into-natural-gas mixing in a T-junction pipeline**, using OpenFOAM v2406 on **Windows 11 + WSL2 Ubuntu**, accessed remotely **via SSH from a Mac**.

The existing validated campaign fixes the **injection angle at 90°** and varies `(d/D, VR)` via **Sliced Latin Hypercube** sampling (10 cases, 5 unique meshes).

The **new chat's job** is to stand up a sibling campaign at a **different injection angle** (e.g. 30°, 45°, 60°) on a **second, lower-spec Windows PC**, without disturbing the running 90° campaign on the primary PC. The base template on the primary PC (`~/openfoam_case_rans_doe_base/`) is the reference implementation — clone it to the new machine and only change the angle-related parameters + spec-related knobs (cell budget, MPI ranks, cases per slice).

---

## 1. Physics and geometry

### 1.1 Problem statement
- H₂ is injected at a 90° branch into a main CH₄ pipeline.
- We measure **mixing quality** (CoV of H₂ on downstream cross-sections, Danckwerts intensity-of-segregation) and **pressure drop** across the junction as functions of the geometric/flow parameters.
- Basis: Eames et al., *Int. J. Hydrogen Energy* 2022 (S0360319922025022), plus Tarabkhah & Ayach 2024 (S0360319924037546).

### 1.2 Fixed base geometry (90° validated case)
| Symbol | Meaning | Value |
| --- | --- | --- |
| D₁ | main pipe diameter | 0.460 m |
| L_main | main pipe length along z | 6.900 m *(after R2 shortening — see §4)* |
| Z_JCT | z-coordinate of junction centre | 2.300 m |
| θ_inj | injection angle | **90°** (branch axis ‖ +y) |
| L_branch | branch pipe length | max(1.380 m, R₁ + 12·D₂) |
| U_main | main bulk velocity | 10 m s⁻¹ |
| P_op | operating pressure | 6.9 MPa |
| T_main, T_branch | temperatures | 284 K / 293 K |
| fluids | main / branch | CH₄ / H₂ |

### 1.3 DoE variables (90° campaign)
- `d/D` ∈ [0.15, 0.45] — branch-to-main diameter ratio, 5 discrete slice values
- `VR = U_branch / U_main` ∈ [≈0.3, ≈12] — velocity ratio, 2 per slice
- `HBR = (d/D)² · VR / (1 + (d/D)² · VR)` is the derived hydrogen blend ratio (constrained to **5 % – 20 %**)
- Total **10 cases**, 5 unique meshes → **5 mesh builds, 10 solves** via mesh reuse.

### 1.4 What changes for a new angle
The **angle** enters in three places:
1. `generateSTL.py` — the branch cylinder axis must be rotated about +x (keeping the junction on z-axis).  Currently the branch axis is `(0, +1, 0)`; for angle θ measured from the +z main axis toward +y, the new branch axis is `(0, sin θ, cos θ)`.
2. `0/U` branch_inlet `codedFixedValue` — the inlet velocity vector must point *into* the main pipe, i.e. negative of the branch axis: `(0, -U_branch sin θ, -U_branch cos θ)`. The power-law radial coordinate on the inlet patch is also rotated.
3. `system/snappyHexMeshDict` → `locationsInMesh` — the second point (inside the branch pipe) must be placed along the rotated branch axis, not straight up at `y = 1.0`.

Everything else (turbulence, thermo, schemes, DoE CSV, scripts) is angle-agnostic.

---

## 2. Compute environment

### 2.1 Primary PC (90° campaign — DO NOT DISTURB)
| Item | Value |
| --- | --- |
| Host | `DESKTOP-922BVMV` (WSL2 inside Windows 11) |
| LAN IP | `10.223.68.120` |
| SSH port | `2222` (Windows port-forward → WSL2 sshd) |
| User | `psl_3` |
| Auth | Mac key `~/.ssh/id_ed25519` → WSL2 `~/.ssh/authorized_keys` (password-less) |
| CPU | Intel i7-14700, 10 cores / 20 threads |
| RAM | 56 GB allocated to WSL2 (host has more) |
| OpenFOAM | **v2406** at `/usr/lib/openfoam/openfoam2406/` |
| MPI | OpenMPI 4.1.6 |
| Python | 3.10+ with `numpy`, `numpy-stl`, `pyvista`, `matplotlib` |

**One-liner to source OpenFOAM on the remote (needed before any OF command):**
```bash
source /usr/lib/openfoam/openfoam2406/etc/bashrc
```

### 2.2 Secondary PC (new angle campaign — what this doc is for)
Fill these in once the new machine is reachable:

| Item | Value |
| --- | --- |
| Host | TBD |
| LAN IP | TBD |
| SSH port | TBD |
| User | TBD |
| CPU / cores / threads | TBD (likely fewer than 20) |
| RAM | TBD (likely < 56 GB) |
| OpenFOAM version | **must be v2406** (match primary — BCs use `codedFixedValue` API which is version-stable, but the `locationsInMesh` syntax varies across forks) |

**Spec-driven adjustments for the new PC** (pick from Section 9 once you know the numbers):
- If cores < 16 → drop `numberOfSubdomains` in `decomposeParDict` accordingly and reduce `maxGlobalCells` in `snappyHexMeshDict` pro-rata.
- If RAM < 32 GB → cap cells at ≈ 300 k (half domain), lower `N_CIRC` from 96 → 64 in `generateSTL.py`, and consider setting `writeFormat  binary;` in `controlDict` to save disk.

### 2.3 How the Mac connects
All edits and commands on the remote go through **SSH from the Mac**. The Mac's local workspace (`/Users/yash/Desktop/CFD Setup instructions/`) is **reference only** — PDFs, papers, reports, and this context doc. No simulation artefacts live on the Mac.

```bash
# single command
ssh -p 2222 psl_3@10.223.68.120 "ls ~/openfoam_case_rans_doe_base/"

# long-running (survives disconnect) — always use tmux on the remote
ssh -p 2222 psl_3@10.223.68.120
tmux new -s doe
cd ~/openfoam_case_rans_doe/doe_base/doe && ./run_doe.sh | tee run_doe.log
# Ctrl-B D to detach; reattach with `tmux attach -t doe`
```

---

## 3. Directory layout

### 3.1 On the primary PC (frozen base + live campaign)
```
/home/psl_3/openfoam_case_rans_doe_base/     ← frozen DoE template (NEVER modified during a campaign)
    0/                   (tokenised BCs; @TOKENS@ replaced per-case)
    constant/            (thermophysics, turbulence, transport)
    system/              (blockMeshDict, snappyHexMeshDict, controlDict, …)
    generateSTL.py       (env-var driven: D1, D2, Z_JCT, L_MAIN, and — new — ANGLE_DEG)
    scripts/
        clip_stls.py     (clips STLs to x ≥ 0 for symmetry — see §4)
        calcCoV.py       (legacy helper, superseded by tools/all_metrics.py)
    tools/
        all_metrics.py   (post-processing: CoV_A, CoV_ṁ, CoV_V, Δp, Danckwerts I_s)
        doe_status.sh    (live ASCII status table)
        doe_watch.sh     (htop-style auto-refresh wrapper)
        make_figures.py      (per-case figure set)
        make_distance_figures.py (z-sampled profiles)
        make_doe_summary.py  (campaign-level comparison plots)
        viz_symmetry.py  (sanity-check the symmetry plane)
    doe/
        lhs_design.py    (produces doe_design.csv; seed 42 reproducible)
        stamp_cases.py   (materialises case_01..NN directories)
        run_doe.sh       (resumable sequential runner)
        doe_design.csv   (the N-point DoE — regenerated per campaign)
        PLAN_DOE.md      (design summary, references, optimisations)

/home/psl_3/openfoam_case_rans_doe/           ← live campaign produced by the workflow
    doe_base/            (working copy of the template; untouched after stamping)
    doe_cases/
        case_01/ ... case_10/   (stamped, ready-to-run)
        doe_design.csv
    doe_results/
        case_NN/                (metrics CSV, log, figures, postProc tarball)
        run_doe.log             (campaign-level log)
```

### 3.2 Recommended layout on the secondary PC (new angle)
Suggestion: prefix everything with the angle so the two campaigns can **coexist** (you may later consolidate results cross-angle):

```
/home/<user>/openfoam_case_rans_doe_base_ANGLE45/   ← frozen template for 45° campaign
/home/<user>/openfoam_case_rans_doe_ANGLE45/        ← live 45° campaign tree
```

---

## 4. Optimisations baked into the validated base

These are **not optional** — they are part of the frozen base and have been validated on the 90° smoke test. The new-angle campaign should inherit all of them unchanged except where noted.

| ID | Change | File(s) | Reason |
| --- | --- | --- | --- |
| **R2** | Upstream main shortened 4.6 m → 2.3 m | `blockMeshDict`, `generateSTL.py`, `snappyHexMeshDict` | Removes inert upstream region; −15 % cells |
| **R1-lite** | Level-1 cylindrical refinement downstream of junction (r = 0.23, z ∈ [2.6, 6.2]) | `snappyHexMeshDict` → `jetRefine` region | Captures mixing without over-refining far field |
| **SYM** | Symmetry plane at **x = 0** (half-domain mesh) | `blockMeshDict` (xMin = 0, `sym` patch), `0/*` (sym BC), STL clipping | **−50 % cells**. Valid for time-mean RANS of a planar-symmetric T-junction; *not* valid for LES. |
| **R3a-lite** | 1/7-th power-law profile on `branch_inlet` via `codedFixedValue` | `0/U` | Developed inlet BC without the complexity of a mapped BC |
| **R4** | `yPlus` function object every 0.1 s | `controlDict` | Validates wall treatment per case |
| **R5** | Plane-sampled H₂ and p_rgh at z ∈ {3, 4, 5, 6} m + `fieldAverage` from t = 0.6 s | `controlDict` | Provides distance-resolved mixing + Δp data |
| **mesh-reuse** | Sliced LHS → 5 unique d/D → 5 mesh builds, not 10 | `run_doe.sh` (`REUSE_MESH_FROM`) | Saves ≈ 3.75 h per 10-case campaign |
| **locationsInMesh** | Two seed points (one per topological region: main + branch) | `snappyHexMeshDict` | Without this, `snappyHexMesh` discards the branch region in the half-domain setup. **This is the single most important fix.** |
| **clip_stls.py** | Sutherland–Hodgman clipping of all STLs against x = 0 | `scripts/clip_stls.py`, called from `Allrun` | Ensures no STL triangles cross the symmetry plane |
| **Coded BC** | `codedFixedValue` 1/7-th power-law on `main_inlet` AND `branch_inlet` | `0/U` | Consistent developed-flow inlets on both patches |

### 4.1 Symmetry-plane justification (if reviewer asks)
- Chen, Li & Yao 2017, *Ann. Nucl. Energy* 111: half-domain SST of a 90° T gives time-mean fields within 1 % of full-domain reference.
- Frank, Lifante, Prasser, Menter 2010, *Nucl. Eng. Des.* 240: validates half-domain BSL/SST on the OECD/NEA Vattenfall T benchmark.
- Walker, Manera, Niceno, Simiano, Prasser 2010, *Nucl. Eng. Des.* 240: confirms symmetry of the time-averaged solution for Re > 3 × 10⁵.
- Forney & Kwon 1979, *AIChE J.* 25: industrial tee-mixer correlations derived on a half-section.

**This justification extends to any angle** where the geometry has a mirror plane through the main pipe axis and the branch axis — which is **every symmetric angle** with a single branch. So SYM is retained for the new-angle campaign.

---

## 5. DoE methodology

### 5.1 Sliced Latin Hypercube (Ye, Li & Sudjianto 2000)
- `lhs_design.py --seed 42 --outdir .` produces `doe_design.csv`.
- 5 slices × 2 points per slice = 10 cases.
- Slice index = unique `d/D`. Mesh reuse is keyed on slice_id.
- Reproducible: **same seed → same design**.

### 5.2 HBR constraint
`HBR = (d/D)² · VR / (1 + (d/D)² · VR)` is kept in **[0.05, 0.20]**. The LHS sampler rejects candidates outside this band and also imposes `VR ≤ 12` (structural safety cap on the injector).

### 5.3 Derived quantities stored per case
`D₂`, `U_main`, `U_branch`, `Re_branch`, loss coefficients, mixing lengths, `Z_JCT`, `L_main`, `slice_id`.

### 5.4 For the new-angle campaign
- **Keep the same `(d/D, VR)` design** (same seed 42 → identical CSV) so the two angles can be compared **point-by-point**. This is a paired-design strategy and is the correct way to isolate the angle effect.
- **OR** re-roll the LHS with a new seed if you want independent exploration at the new angle.

---

## 6. Key files — what they do

### 6.1 `generateSTL.py` (≈ 350 lines)
- Env-var driven: `D1`, `D2`, `Z_JCT`, `L_MAIN`, `L_BRANCH`, `N_CIRC`, `N_AXIAL_MAIN`, `N_AXIAL_BRANCH`.
- Emits 4 water-tight STLs: `wall.stl`, `main_inlet.stl`, `outlet.stl`, `branch_inlet.stl`.
- Does a signed-volume sanity check; **aborts if the ratio deviates > 3 %** from the analytic volume.
- **For the new angle**: add `ANGLE_DEG` env var. Rotate the branch-cylinder points and the intersection curve about the +x axis by `90° − ANGLE_DEG` (so ANGLE_DEG = 90 recovers the current geometry).

### 6.2 `scripts/clip_stls.py`
- Reads binary STLs, clips all triangles against `x = 0` using Sutherland–Hodgman, writes clipped binary STLs in-place.
- Called from each case's `Allrun` immediately after `generateSTL.py` and before `surfaceFeatureExtract`.

### 6.3 `system/blockMeshDict`
- Half-domain hex: x ∈ [0, 0.30], y ∈ [−0.30, 1.50], z ∈ [−0.05, 6.95].
- `sym` patch on the x = 0 face, typed `symmetryPlane`.

### 6.4 `system/snappyHexMeshDict`
Critical blocks:
- `refinementSurfaces`: `wall` level (1 1); `main_inlet`/`outlet` level (0 0); `branch_inlet` level (1 1).
- `refinementRegions`: `junctionRefine` sphere at `(0, 0, Z_JCT)` level 2; `jetRefine` cylinder downstream level 1.
- `locationsInMesh` with **two** points: one in the main pipe, one in the branch pipe. The branch point must be inside the branch for the current angle — **this needs to be recomputed when the angle changes** (the base template uses `(0.010 1.000 Z_JCT)` which is correct only at 90°).
- `maxGlobalCells  1500000;` cap.

### 6.5 `system/controlDict`
- `rhoReactingBuoyantFoam` transient, k-ω SST, `adjustTimeStep yes`, `maxCo 3.5`, `endTime 1.2 s`, `writeInterval 0.1 s`.
- Function objects: `yPlusAudit` (R4), mass-flux sums on all three patches (every 20 steps), area-averages of H₂ and p_rgh on z = {3, 4, 5, 6} m planes, `fieldAverage` of `U, H2, CH4, p_rgh, k` starting at t = 0.6 s.
- `runTimeModifiable true` — you can edit endTime live.

### 6.6 `0/U`, `0/H2`, `0/CH4`, `0/T`, `0/p`, `0/p_rgh`, `0/k`, `0/omega`, `0/nut`, `0/alphat`
All carry a `sym { type symmetryPlane; }` entry. `0/U` has `codedFixedValue` 1/7-th power-law on both inlets, driven by `@UMAIN@`, `@UBRANCH@`, `@D1@`, `@D2@`, `@ZJCT@` tokens.

### 6.7 `doe/lhs_design.py` (228 lines)
- Produces `doe_design.csv` with columns: case, d_over_D, HBR, VR, D2_m, U_main, U_branch, Re_branch, K_main, K_branch, Ω_main, Ω_branch, mix_branch, ZJCT, LMAIN, slice_id.

### 6.8 `doe/stamp_cases.py` (281 lines)
- For each row in `doe_design.csv`:
  - Clone `doe_base/` → `doe_cases/case_NN/`.
  - Substitute tokens in `0/U` and `snappyHexMeshDict` (Z_JCT).
  - Copy `generateSTL.py` and `scripts/` into the case.
  - Write a self-contained `Allrun` that runs: `generateSTL.py → clip_stls.py → surfaceFeatureExtract → blockMesh → snappyHexMesh → checkMesh → decomposePar → potentialFoam → rhoReactingBuoyantFoam → reconstructPar → post-processing`.
  - Writes `case_info.json` with exact parameters.

### 6.9 `doe/run_doe.sh` (288 lines)
- Iterates over stamped cases in order.
- For the first case in each slice: full `Allrun`. For the second: reuses `constant/polyMesh` from the first via `REUSE_MESH_FROM`.
- Writes `SIM_DONE` sentinel on success, `SIM_FAILED` + last 200 log lines on failure. **Never aborts the campaign**.
- After each case, copies `all_metrics.csv`, `PROVENANCE.txt`, figures, and a tarball of `postProcessing/` to `doe_results/case_NN/`.

### 6.10 `tools/doe_status.sh` / `doe_watch.sh`
- Snapshot or htop-style live view. Columns: case, state, t_sim, progress %, U_res, p_res, wall_elapsed.
- **Use `doe_status.sh` once** to get a snapshot; use `doe_watch.sh` in a second tmux window to watch live.

### 6.11 `tools/all_metrics.py` (724 lines)
- Loads reconstructed mean fields, samples planes, computes:
  - **CoV_A** (area-weighted), **CoV_ṁ** (mass-flux-weighted), **CoV_V** (volume-flux-weighted) — **all three stored**, not just one.
  - **Δp** in three variants: static, gauge, total — **all three stored**.
  - **Danckwerts intensity of segregation** analytically from mean H₂.
  - Mass-flow closure check across all patches.
- Writes `all_metrics.csv` per case.

---

## 7. Run-book (primary PC, 90° — already working)

```bash
# one-time: build the campaign tree
ssh -p 2222 psl_3@10.223.68.120
mkdir -p ~/openfoam_case_rans_doe
cp -r ~/openfoam_case_rans_doe_base ~/openfoam_case_rans_doe/doe_base
cd ~/openfoam_case_rans_doe/doe_base/doe

# generate design + stamp cases
python3 lhs_design.py --seed 42 --outdir .
python3 stamp_cases.py \
    --design doe_design.csv \
    --base   .. \
    --cases  ~/openfoam_case_rans_doe/doe_cases \
    --overwrite

# launch inside tmux
tmux new -s doe
source /usr/lib/openfoam/openfoam2406/etc/bashrc
./run_doe.sh 2>&1 | tee run_doe.log
# Ctrl-B D to detach

# monitor (second tmux or separate SSH)
bash ~/openfoam_case_rans_doe_base/tools/doe_status.sh   # snapshot
bash ~/openfoam_case_rans_doe_base/tools/doe_watch.sh    # live

# resume after crash/reboot
tmux new -s doe
./run_doe.sh 2>&1 | tee -a run_doe.log    # skips SIM_DONE cases
```

**Current live status (snapshot at time of handoff — primary PC only):**
- case_01 RUNNING at t_sim ≈ 0.93 / 1.20 s (≈ 78 %), residuals U ≈ 2×10⁻⁹, p_rgh ≈ 8×10⁻⁸.
- Cases 02–10 pending.
- `endTime = 1.2 s` confirmed on all 10 cases.
- Projected completion: ~3.5 h for case_01 (hardest case); remaining 9 cases ≈ 45 min – 1.5 h each.

---

## 8. Standing up the new-angle campaign on the secondary PC

### 8.1 Prereqs on the new machine
```bash
# WSL2 Ubuntu 22.04 recommended
sudo apt update
sudo apt install -y build-essential python3 python3-pip tmux openssh-server
pip3 install numpy numpy-stl pyvista matplotlib

# OpenFOAM v2406 — match primary exactly
# (follow official openfoam.com Ubuntu instructions for 2406)
echo 'source /usr/lib/openfoam/openfoam2406/etc/bashrc' >> ~/.bashrc
```

### 8.2 Transfer the base template from primary → secondary
From the **Mac** (not the primary WSL2, to avoid cross-WSL oddities):
```bash
# pull base to Mac
scp -P 2222 -r psl_3@10.223.68.120:~/openfoam_case_rans_doe_base \
    /tmp/of_base_primary

# push to secondary (fill in secondary IP/port/user)
scp -P <PORT_SEC> -r /tmp/of_base_primary <USER_SEC>@<IP_SEC>:~/openfoam_case_rans_doe_base_ANGLEXX
```

### 8.3 Adapt base for the new angle
On the **secondary** PC, inside `~/openfoam_case_rans_doe_base_ANGLEXX/`:

1. **`generateSTL.py`**: introduce `ANGLE_DEG` env var; rotate branch-axis and intersection curve by `90° − ANGLE_DEG` about +x.
2. **`0/U`** branch_inlet `codedFixedValue`:
   - Change velocity vector to `(0, -U_branch sin θ, -U_branch cos θ)`.
   - Change power-law radial coordinate to be measured perpendicular to the rotated axis.
3. **`system/snappyHexMeshDict`** `locationsInMesh`: second point must be inside the rotated branch. A safe choice is `(0.01, 0.5·L_branch·sin θ, Z_JCT + 0.5·L_branch·cos θ)`. Verify with `checkMesh` after first build.
4. **`doe/stamp_cases.py`**: extend the `ANGLE_DEG` token handling; substitute into `0/U` and the STL env vars.
5. **Spec tuning** (see §9): adjust `decomposeParDict`, `maxGlobalCells`, `N_CIRC`.

### 8.4 Validate the new angle before launching the full DoE
```bash
# smoke-test case (d/D = 0.25, VR = 1.5, angle = NEW)
ssh -p <PORT_SEC> <USER_SEC>@<IP_SEC>
source /usr/lib/openfoam/openfoam2406/etc/bashrc
cd ~/openfoam_case_rans_doe_ANGLEXX/doe_base
ANGLE_DEG=45 D2=0.115 python3 generateSTL.py
python3 scripts/clip_stls.py constant/triSurface
surfaceFeatureExtract
blockMesh
snappyHexMesh -overwrite
checkMesh      # must show 5 patches including branch_inlet; layers > 90 %
```

If `branch_inlet` has 0 faces after `snappyHexMesh`, the second `locationsInMesh` seed is wrong — **that's the #1 pitfall at any new angle**.

### 8.5 Launch the new-angle DoE
Same as §7 but with the new paths. Keep the **same `--seed 42`** so paired comparison with the primary campaign is valid.

---

## 9. Performance tuning for lower-spec hardware

These are the knobs you change based on the secondary PC's specs. Numbers below are illustrative for a **6-core / 12-thread, 16 GB** target; scale from there.

| Knob | File | Primary value | Lower-spec target |
| --- | --- | --- | --- |
| `numberOfSubdomains` | `system/decomposeParDict` | 16 | **N_cores** (e.g. 6) |
| `maxGlobalCells` | `system/snappyHexMeshDict` | 1 500 000 | **≈ 75 000 × N_cores** (e.g. 450 k) |
| `N_CIRC` (STL) | `generateSTL.py` env | 96 | 64 |
| `maxLocalCells` | `snappyHexMeshDict` | 200 000 | `maxGlobalCells / N_cores × 2` |
| block-mesh cells (z) | `blockMeshDict` | 232 | scale with `L_main / 0.03` |
| `writeFormat` | `controlDict` | `ascii` | `binary` (if disk is tight) |
| `writeCompression` | `controlDict` | `off` | `on` (≈ 50 % disk savings) |
| cases per tmux | — | 1 runner | 1 runner (always sequential) |
| `maxCo` | `controlDict` | 3.5 | 2.0 (smaller CFL → less bounding on tight meshes) |

**Rule of thumb:** aim for **≤ 100 k cells per MPI rank** on a Core-i7; below that, solver wall time is I/O-dominated; above that, you'll hit RAM limits during `snappyHexMesh` layer addition.

---

## 10. Known pitfalls and how they're already fixed in the base

| Symptom | Root cause | Fix in base |
| --- | --- | --- |
| `branch_inlet` patch missing after `snappyHexMesh` | Half-domain + symmetry created a *second* topological region (the branch); single `locationInMesh` kept only the main region | `locationsInMesh` (plural) with two seed points |
| `FOAM Warning: branchInletFlux No matching patches` | Same as above | Same fix |
| STL triangles crossing x = 0 | Original STL is full-domain | `scripts/clip_stls.py` called from `Allrun` |
| `doe_status.sh` shows DONE while still running | `grep ExecutionTime` matches every step | Changed to `grep '^End$'` only |
| `doe_status.sh` shows `wall_elapsed = 00:00:00` | Used mtime of `log.solver` which keeps bumping | Use birth-time (`stat %W`) of log file with ctime fallback |
| k-ω bounding storms → CFL spikes → tiny deltaT | Transient spin-up with 1/7-th power-law inlets | Accept — residuals converge anyway; deltaT recovers after t ≈ 1.0 s |
| Volume ratio ≠ 1 from `generateSTL.py` | Non-watertight junction (old bug) | Zipper triangulation between hole boundary and branch base |
| `allBoundary` patch with many faces | STL gaps | Watertight STL + clip script |

**If the new-angle chat hits `branch_inlet` missing: it is 99 % the `locationsInMesh` seed pointing outside the rotated branch.** Fix that first.

---

## 11. Deliverables the pipeline produces per case

For each `case_NN/`, `doe_results/case_NN/` ends up containing:

- `all_metrics.csv` — CoV_A, CoV_ṁ, CoV_V, Δp_static, Δp_gauge, Δp_total, Danckwerts I_s, mass-flow closure.
- `case_info.json` — exact (d/D, HBR, VR, D₂, U_main, U_branch, Z_JCT, seed, angle, host, git SHA if under VCS).
- `log.solver`, `log.snappyHexMesh`, `log.blockMesh`, `log.checkMesh`, `log.generateSTL`.
- `PROVENANCE.txt` — timestamps and software versions.
- `figures/` — `fig_geometry.png`, `fig_mesh_xz.png`, `fig_H2_xz.png`, `fig_H2_outlet.png`, `fig_pressure_xz.png`, `fig_velocity_xz.png`, `fig_streamlines.png`, `fig_symmetry.png`, plus `fig_distance_CoV.png`.
- `postProcessing.tar.gz` — the raw function-object outputs for re-analysis.

Campaign-level: `doe_results/all_metrics.csv` (concatenated), `doe_results/figures/` (cross-case comparison plots from `make_doe_summary.py`).

---

## 12. Things the new chat should NOT do

1. **Do not modify files on the Mac**. The Mac is read-only for simulation files.
2. **Do not touch the primary PC** while its 90° campaign is running. Everything new goes on the secondary PC under a separate path.
3. **Do not change the LHS seed** unless you explicitly want an un-paired design. Default = 42.
4. **Do not remove the symmetry plane** unless you're switching to LES (out of scope).
5. **Do not add comments inside OpenFOAM dict files** that narrate the code — reviewers see these and it looks junior. Only comment non-obvious physics/tuning choices.

---

## 13. Quick commands for the new chat to verify the environment

```bash
# sanity check on the secondary PC
ssh -p <PORT_SEC> <USER_SEC>@<IP_SEC> bash -lc "
  source /usr/lib/openfoam/openfoam2406/etc/bashrc &&
  echo OF=\$WM_PROJECT_VERSION &&
  which rhoReactingBuoyantFoam &&
  mpirun --version | head -1 &&
  nproc &&
  free -h | head -2 &&
  python3 -c 'import numpy, stl, pyvista, matplotlib; print(\"py OK\")'
"
```

Expected: `OF=v2406`, solver path non-empty, MPI 4.x, cores ≥ 4, RAM ≥ 16 GB free, Python import OK.

---

## 14. References (cite these when writing results)

- Eames, McCarthy & Azapagic, *Int. J. Hydrogen Energy* 2022 — problem definition, base geometry.
- Tarabkhah & Ayach 2024, *Int. J. Hydrogen Energy* — T-junction hydrogen blending data.
- Ye, Li & Sudjianto 2000, *J. Stat. Plan. Inference* — sliced LHS design.
- Forney & Kwon 1979, *AIChE J.* 25 — tee-mixer correlations.
- Chen, Li & Yao 2017, *Ann. Nucl. Energy* 111 — half-domain SST validation.
- Frank, Lifante, Prasser & Menter 2010, *Nucl. Eng. Des.* 240 — Vattenfall T benchmark.
- Walker, Manera, Niceno, Simiano & Prasser 2010, *Nucl. Eng. Des.* 240 — same benchmark.
- Danckwerts 1952, *Appl. Sci. Res. A* 3 — intensity of segregation.

---

## 15. One-paragraph summary to prepend to the new chat

> "I'm running a parametric CFD DoE of H₂-into-CH₄ T-junction mixing in OpenFOAM v2406 on WSL2 Ubuntu inside Windows 11, accessed remotely via SSH from a Mac. A validated 10-case Sliced-LHS campaign at **90°** injection angle is already running on a primary PC (`10.223.68.120:2222`, user `psl_3`). I want to run a **sibling campaign at a different injection angle** on a second, lower-spec Windows PC without disturbing the primary. Please read `DOE_CONTEXT_FOR_NEW_CHAT.md` for the full design rationale, directory layout, optimisations (symmetry plane, R1-lite, R2, R3a-lite, R4, R5, mesh-reuse, `locationsInMesh`, `clip_stls.py`), spec-tuning knobs, and known pitfalls. Help me clone the base template to the secondary PC, adapt it for the new angle, validate a smoke-test, then launch the full DoE."

---

*End of context pack. Keep this file at project root; update §2.2 and §7 once the secondary PC is online.*
