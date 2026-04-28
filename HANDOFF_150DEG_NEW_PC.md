# Handoff: 150° injection-angle DoE on the new PC

> Hand this file to a fresh chat session that has SSH access to the new PC.
> The previous chat is busy babysitting the **30° campaign on the original
> compute host**. Do **NOT** touch the original host or the 30° campaign from
> this new chat — they are completely independent jobs.

---

## 1. What you are setting up

A 10-case Design-of-Experiments (DoE) for a hydrogen-into-natural-gas pipeline
T-junction at injection angle **α = 150°** (counter-flow). It mirrors the
existing 90° (done) and 30° (in progress on a separate machine) campaigns and
uses an already-angle-agnostic codebase. You will:

1. Bootstrap OpenFOAM 2406 on the new PC.
2. Clone `Yash04dsr/MTP-Work` (which contains the 30° base case as the
   template).
3. Make a 150° base by cloning the 30° base and just setting `ALPHA_DEG=150`
   — the codebase already reads angle from an env var, no source edits
   needed.
4. Generate the DoE design, stamp 10 cases, run them sequentially with the
   resilient orchestrator.
5. Sanity-check the very first mesh before launching the full campaign.
6. Push results back to `MTP-Work` under a `doe_results_150deg/` directory
   so the original chat can pull them down for cross-angle synthesis.

The whole campaign is ~10–14 hours of wall time on a 16-thread machine
(based on the 30° timing).

---

## 2. The new PC

| Item        | Value                                |
|-------------|--------------------------------------|
| SSH command | `ssh -p 2222 psl_3@100.92.224.39`    |
| User        | `psl_3`                              |
| Hostname    | (run `hostname` after first login)   |
| OS          | Linux (verify with `uname -a`)       |
| Compute     | unknown — check `nproc`, `free -g`   |
| GPU         | not used by OpenFOAM                 |

First-login checks to run:

```bash
ssh -p 2222 psl_3@100.92.224.39
uname -a
nproc                    # we want >= 8 for parallel solver
free -g                  # we want >= 16 GB RAM
df -h ~                  # we want >= 50 GB free for the campaign
which mpirun foamRun rhoReactingBuoyantFoam   # is OpenFOAM already there?
ls /usr/lib/openfoam 2>/dev/null               # version check
```

---

## 3. Source of truth

| Layer        | Where it lives                                                       |
|--------------|----------------------------------------------------------------------|
| Code         | `https://github.com/Yash04dsr/MTP-Work` (branch: `main`)             |
| 30° base     | `openfoam_case_rans_doe_30deg_base/` inside that repo                |
| Already-fixed mesh defect | committed under `b9adb14` (verify the fix is present, see §6) |
| Maths/report (separate)   | `https://github.com/Yash04dsr/CFD-Setup-instructions` — DO NOT clone this on the new PC, it's a different repo for analysis only. |

> **Critical:** Before you do anything, confirm the 30° base in `MTP-Work`
> contains the **fixed** `generateSTL.py`. The fix tightens the rectangular
> hole in the main pipe to the bbox of the intersection curve plus a buffer.
> If you see a heuristic involving `z_stretch = R2 + 0.5*L_BRANCH*|cos(alpha)|`
> in `generateSTL.py`, the fix is **not** there and you must pull the latest
> `main` branch first. See §6.

---

## 4. Why this is straightforward — the codebase is already angle-aware

You do **not** need to fork the case directory. The 30° base reads
`ALPHA_DEG` from the environment in two places:

1. **`generateSTL.py`** (line ~51):
   ```python
   ALPHA_DEG = _envf("ALPHA_DEG", 90.0)
   ALPHA = ALPHA_DEG * math.pi / 180.0
   SIN_A = math.sin(ALPHA)
   COS_A = math.cos(ALPHA)
   ```

2. **`doe/stamp_cases.py`** (line ~78):
   ```python
   ALPHA_DEG_DEFAULT = 30.0
   ALPHA_DEG = float(os.environ.get("ALPHA_DEG", ALPHA_DEG_DEFAULT))
   SIN_ALPHA = math.sin(math.radians(ALPHA_DEG))
   COS_ALPHA = math.cos(math.radians(ALPHA_DEG))
   ```

   And it substitutes `@ALPHA_DEG@`, `@SIN_ALPHA@`, `@COS_ALPHA@` into the
   case templates (`0/U`, etc.).

3. **`Allrun`** sources `case.env`, which `stamp_cases.py` writes with
   `export ALPHA_DEG=...` baked in.

So the *only* thing you need to do to flip from 30° to 150° is set
`ALPHA_DEG=150.0` in your shell before running `stamp_cases.py`. No code
edits.

---

## 5. The full bootstrap recipe (run on the new PC)

```bash
# ---- 0. Sanity ---------------------------------------------------------
ssh -p 2222 psl_3@100.92.224.39
mkdir -p ~/work && cd ~/work

# ---- 1. Install OpenFOAM 2406 if not present ---------------------------
if ! command -v rhoReactingBuoyantFoam >/dev/null; then
    sudo sh -c "wget -O - https://dl.openfoam.com/add-debian-repo.sh | bash"
    sudo apt-get update
    sudo apt-get install -y openfoam2406-default
fi
echo 'source /usr/lib/openfoam/openfoam2406/etc/bashrc' >> ~/.bashrc
source /usr/lib/openfoam/openfoam2406/etc/bashrc
which rhoReactingBuoyantFoam   # must print a path now

# ---- 2. Python deps ---------------------------------------------------
sudo apt-get install -y python3 python3-pip python3-numpy python3-scipy \
                       python3-matplotlib python3-pandas git tmux rsync
pip3 install --user pyDOE2 pyvista==0.43.10  # pyvista is for post-processing

# ---- 3. Clone the canonical repo ---------------------------------------
cd ~/work
git clone https://github.com/Yash04dsr/MTP-Work.git
cd MTP-Work

# ---- 4. Build a 150deg base by copying the 30deg one -------------------
cp -r openfoam_case_rans_doe_30deg_base openfoam_case_rans_doe_150deg_base
cd openfoam_case_rans_doe_150deg_base

# ---- 5. Verify the angle-agnostic env-var hook is present --------------
grep "ALPHA_DEG" generateSTL.py | head -3
grep "ALPHA_DEG" doe/stamp_cases.py | head -3
# both should show the env-var read; if not, you have an outdated checkout

# ---- 6. Verify the mesh-defect fix is present (CRITICAL) ---------------
grep -n "z_stretch" generateSTL.py
# expected output: zero or one match inside a comment that EXPLAINS why we
# DON'T use that heuristic anymore. If you see code that ASSIGNS to z_stretch
# and uses it to size the hole, the fix is missing -- abort and 'git pull'.
grep -n "P_theta\|P_z\|j_lo, j_hi" generateSTL.py | head -6
# expected: lines with bbox-from-P calculation. Their presence = fix is in.
```

### 5a. First mesh sanity check at α = 150° (do this BEFORE the full DoE)

```bash
cd ~/work/MTP-Work/openfoam_case_rans_doe_150deg_base

export ALPHA_DEG=150.0
python3 generateSTL.py
# Output should print:
#   ALPHA_DEG = 150.00 deg  (branch axis -> -z axis angle)
# and write 4 STL files under constant/triSurface/

# Confirm the STL is watertight and a single connected component
python3 - <<'PY'
import pyvista as pv
m = pv.read("constant/triSurface/wall.stl")
print("triangles:", m.n_cells, "  bbox:", m.bounds)
print("manifold:", m.is_manifold)
print("regions:", m.connectivity().split_bodies().__len__())
PY
# Expect: manifold = True (or close), regions = 1.

# (Optional) quick mesh test on a single dummy case to make sure
# snappyHexMesh produces ONE region, not two.
source /usr/lib/openfoam/openfoam2406/etc/bashrc
mkdir -p /tmp/sanity_150 && cp -r . /tmp/sanity_150/
cd /tmp/sanity_150
# stamp a single case_01 just to populate templates:
ALPHA_DEG=150.0 python3 doe/stamp_cases.py --design doe/sample_design_smoke.csv \
    --base . --cases /tmp/sanity_cases || true
cd /tmp/sanity_cases/case_01 || cd .   # depending on stamp output
surfaceFeatureExtract; blockMesh; snappyHexMesh -overwrite
checkMesh -allTopology -allGeometry | grep -E "regions|non-orth|skewness"
# Expect: 'Number of regions: 1 (OK)', non-ortho < 65, skewness < 4.
```

If `Number of regions: 2` shows up, **stop**. The mesh-defect fix is
either not present or did not generalize to 150°. Diagnose by running
a `pyvista.connectivity()` on the cell-zone output and report back.

### 5b. Generate DoE design + stamp the 10 cases

```bash
cd ~/work/MTP-Work/openfoam_case_rans_doe_150deg_base/doe

# Re-use the same DoE design as 30deg (same seed, same factor box) so the
# three angles are directly comparable.
python3 lhs_design.py --seed 42 --outdir .   # writes doe_design.csv

# Stamp 10 cases at 150 deg.
export ALPHA_DEG=150.0
python3 stamp_cases.py \
    --design doe_design.csv \
    --base ~/work/MTP-Work/openfoam_case_rans_doe_150deg_base \
    --cases ~/work/openfoam_case_rans_doe_150deg/doe_cases

# Check that each case.env has the right angle:
for f in ~/work/openfoam_case_rans_doe_150deg/doe_cases/case_*/case.env; do
    grep -H ALPHA_DEG "$f"
done
# Every line should print "...ALPHA_DEG=150.0000".
```

### 5c. Launch the campaign in tmux

```bash
tmux new -s doe150
cd ~/work/MTP-Work/openfoam_case_rans_doe_150deg_base/doe

CASES_DIR=~/work/openfoam_case_rans_doe_150deg/doe_cases \
RESULTS_DIR=~/work/openfoam_case_rans_doe_150deg/doe_results \
./run_doe.sh 2>&1 | tee ~/work/openfoam_case_rans_doe_150deg/run_150deg_$(date +%F).log

# Detach with: Ctrl-b d
# Reattach with: tmux attach -t doe150
```

To monitor progress later (without re-attaching):

```bash
cat ~/work/openfoam_case_rans_doe_150deg/doe_results/STATUS.md
tail -n 40 ~/work/openfoam_case_rans_doe_150deg/run_150deg_*.log
```

---

## 6. The mesh-defect fix — why it matters at 150°

The original `generateSTL.py` had a heuristic for sizing the rectangular
hole in the main pipe where the branch joins:

```python
# OLD, BROKEN heuristic
z_stretch = R2 + 0.5 * L_BRANCH * abs(math.cos(alpha))
```

At `α = 90°` `cos(α) = 0` so the hole is small and correct. At `α = 30°`
the hole became ~7× too big, the zipper triangulation spanned ~1 m of
empty annular space, snappyHexMesh interpreted those skewed triangles as a
wall, and the fluid domain split into TWO disconnected regions — H₂
appeared to never reach the outlet because there was a "wall" in the way.

The fix (commit `b9adb14`) replaces the heuristic with a tight bbox derived
directly from the actual intersection curve in `(θ, z)` parameter space,
plus a few grid cells of buffer:

```python
# NEW, CORRECT
P_theta = np.array([math.atan2(p[1], p[0]) for p in P])
P_theta = np.where(P_theta < 0.0, P_theta + 2.0 * math.pi, P_theta)
P_z = P[:, 2]
j_lo = max(int(math.floor(P_theta.min() / dth)) - BUFFER_CELLS, 0)
j_hi = min(int(math.ceil(P_theta.max() / dth)) + BUFFER_CELLS, N_CIRC - 1)
i_lo = max(int(math.floor(P_z.min() / dz)) - BUFFER_CELLS, 0)
i_hi = min(int(math.ceil(P_z.max() / dz)) + BUFFER_CELLS, N_AXIAL_MAIN)
```

Plus a safety expansion loop that grows the rectangle if any in-hole
vertex is outside it. This is geometry-agnostic, so it works for **any**
angle including 150°. But you must verify it is in your checkout (§5,
step 6).

At 150° the hole is on the **opposite side** in θ from where it was at
30° (because the intersection curve bbox flips), so this is the first
time the fix is being exercised on counter-flow geometry. **The §5a
sanity check is not optional.**

---

## 7. Parameter set at 150° — what's identical, what changes

**Same as 30° / 90° (kept identical for cross-angle comparability):**

- DoE design (`doe_design.csv`) — same seed, same `(d/D, HBR, VR)` triplets
- All thermophysics, turbulence, schemes, solver settings
- Operating pressure 6.9 MPa, isothermal 300 K (now 284 K — see note below)
- Main pipe Ø 0.46 m, length post-R2 = 6.95 m, half-domain symmetry
- Mesh quality targets: `maxNonOrtho 65`, `maxSkewness 4`, layer coverage > 99%
- `maxCo = 8.0`, `endTime = 1.2 s`, `writeInterval = 0.1 s`

**Changes automatically because of `ALPHA_DEG=150`:**

- `sin(α) = 0.5`, `cos(α) = -0.866025` (vs. `0.5, +0.866` at 30°)
- Branch axis vector → `(0, 0.5, +0.866)` (was `(0, 0.5, -0.866)` at 30°)
- Branch inlet sits *downstream* of the junction (was upstream at 30°)
- Branch flow direction is `(0, -0.5, -0.866)` — counter to main flow
- Junction-rectangle hole moves to the opposite θ-side of the main pipe

**Things to NOT change** (preserves cross-angle factorial):

- Don't touch `lhs_design.py` arguments — same seed 42.
- Don't change cell sizes or refinement levels.
- Don't change `Sct`, intensity, mixing length.

---

## 8. Known pitfalls — DO NOT repeat these

| Pitfall                                  | What it looks like                            | Fix                                                                                           |
|------------------------------------------|-----------------------------------------------|-----------------------------------------------------------------------------------------------|
| Mesh-defect bug (the big one)            | `H₂` outlet stays at 0 across all cases       | Use the fixed `generateSTL.py`. §5 step 6 verifies. §5a sanity-checks for 150°.              |
| FPE in `yPlus` function object on first step | Solver crashes with NaN inside FPE handler | The `yPlusAudit` block in `system/controlDict` is already commented out in the 30° base.      |
| `pyvista` not on the remote              | `make_figures.py` fails with `ModuleNotFoundError` | Install via `pip3 install --user pyvista==0.43.10`. Already in §5.                          |
| SCP randomly closes mid-transfer         | `scp` exits with "Connection closed"          | Use `rsync -e "ssh -p 2222" ...` instead, or `scp -O -P 2222` (legacy protocol).             |
| Solver runs but cumulative continuity blows up | `Time = ...  contErr = 6e+0`              | Check `maxCo` is 8.0 (not higher). For 150° if it persists, drop to 4.5 and report back.     |
| Out-of-disk in middle of campaign        | Solver writes fail, processor* dirs grow huge | `purgeWrite 3` in `controlDict` should keep this in check. Confirm before launch.            |

---

## 9. What to push back to GitHub

When the campaign finishes (or after each case if you want to play it safe),
push results to `MTP-Work` under a clearly-named directory:

```bash
cd ~/work/MTP-Work
mkdir -p doe_results_150deg
rsync -av ~/work/openfoam_case_rans_doe_150deg/doe_results/ doe_results_150deg/

# Strip processor* and time directories before committing — only metrics,
# logs, figures, and case_info.json should go to git.
find doe_results_150deg -name 'processor*' -prune -exec rm -rf {} +
find doe_results_150deg -regex '.*/[0-9]+\.[0-9]+' -prune -exec rm -rf {} +

git checkout -b feat/doe-150deg-results
git add doe_results_150deg openfoam_case_rans_doe_150deg_base
git status              # SANITY CHECK before commit
git commit -m "feat(150deg): bootstrap base + 10-case DoE results

- copies 30deg base, runs at ALPHA_DEG=150
- mesh defect fix verified on 150deg geometry
- all 10 cases completed (or list which crashed in PROVENANCE.md)
- maxCo 8.0, endTime 1.2s, half-domain k-omega SST
"
git push -u origin feat/doe-150deg-results
# Open a PR — do NOT push to main directly.
```

> The original chat / 30° campaign uses `MTP-Work:main` for its own pushes,
> so isolate yours on a feature branch. Tell the user (Yash) when the PR is
> ready so he can merge.

---

## 10. Deliverables expected from the new PC

1. `doe_results_150deg/` populated with 10 `case_NN/` subdirs containing:
   - `case_info.json` (parameters + wall time + status)
   - `metrics.json` (CoV mass-flux + area + volume, |Δp|, Danckwerts I_s)
   - `log.solver` (truncated tail OK, full one in tarball)
   - `figures/` (geometry, contours, planes — auto-generated via
     `tools/all_metrics.py` and `tools/make_figures.py`)
   - `SIM_DONE` sentinel on success or `SIM_FAILED` on crash
2. `STATUS.md` final snapshot in `doe_results_150deg/`.
3. A `PROVENANCE.md` listing:
   - Which commit of `MTP-Work` was used
   - Hostname + uname of the new PC
   - Wall time per case
   - Any crashed cases and what happened
4. A `git tag` `doe-150deg-v1` on the merge commit.

---

## 11. If something goes wrong

The orchestrator is crash-resilient by design — a failed case writes
`SIM_FAILED` and the campaign moves to the next case. So:

- **One case fails:** carry on. Note it in `PROVENANCE.md`. Yash will
  decide if it needs to be re-run after the campaign.
- **Multiple cases fail with the same symptom:** stop the orchestrator
  (`tmux attach -t doe150`, then Ctrl-C the bash loop), and write a
  diagnostic summary including the last 200 lines of `log.solver` from
  one failed case. Do not try to "fix" the solver settings — they were
  validated on 90° and 30°. The most likely cause is a meshing issue
  specific to 150°, and the right fix lives in `generateSTL.py`.
- **First case fails at meshing time:** the §5a sanity check should have
  caught this. Re-run the connectivity check and report what
  `pyvista.connectivity().split_bodies()` returns. Don't attempt to
  hack `snappyHexMeshDict` blindly.
- **You can't reach the new PC:** that's a network/SSH issue, not a CFD
  issue. Tell Yash; this handoff doesn't cover it.

---

## 12. Out of scope for this handoff

- Do not touch the 30° campaign, the 30° base, or the original compute
  host. They live elsewhere and the previous chat is babysitting them.
- Do not modify the `lhs_design.py` factor box, `fvSchemes`, `fvSolution`,
  thermo, or turbulence settings without checking with Yash first.
  Cross-angle comparability depends on these being identical.
- Do not modify `report.tex` or `study_notes.tex`. Those are owned by the
  original chat and live in the `CFD-Setup-instructions` repo, not in
  `MTP-Work`.
- Do not run the validation case (`case_01` — the buoyancy sanity case).
  It's already done at 90° and not part of the 150° deliverable.

---

## 13. TL;DR for the new chat

1. SSH in, install OpenFOAM 2406 + Python deps.
2. Clone `Yash04dsr/MTP-Work`.
3. `cp -r openfoam_case_rans_doe_30deg_base openfoam_case_rans_doe_150deg_base`.
4. Verify the mesh fix is present in `generateSTL.py` (§5).
5. `export ALPHA_DEG=150.0`, then run sanity check (§5a) — STOP if
   `regions != 1`.
6. Stamp 10 cases (§5b). Verify each `case.env` has `ALPHA_DEG=150.0000`.
7. Launch in tmux (§5c). Monitor via `STATUS.md`.
8. Push results on a feature branch (§9). Open a PR.

Total wall time estimate: ~10–14 hours on a 16-thread machine.

— end of handoff —
