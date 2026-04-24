# 30 deg DoE — setup status (ready to run)

## What was done

All `@XXX@`-token substitution and snappyHexMesh refinement settings are now
truly angle-agnostic. The exact same template stamps a clean working case
for any `ALPHA_DEG` in roughly `[25, 90]` deg.

### Code generalisation (works for any angle)

| File | What was generalised |
| --- | --- |
| `generateSTL.py` | Expected volume check now uses `R1 / sin(alpha)` as the branch-cap height estimate (was hard-coded `R1`). Water-tightness ratio stays in `[0.90, 1.10]` from 25° up to 90°. |
| `0/U` | `branch_inlet` coded BC builds the 1/7th power-law profile in the tilted branch frame using `(SIN_ALPHA, COS_ALPHA)` tokens. Flow direction is `-S_HAT = (0, -sin a, cos a)` regardless of angle. |
| `system/snappyHexMeshDict` | Junction sphere centre uses `@ZJCT@`; `locationsInMesh` branch seed uses `@XBRANCH_INT@ / @YBRANCH_INT@ / @ZBRANCH_INT@` tokens. `branch_inlet` bumped to refinement level 2 so tilted inlet discs still resolve 40+ faces. |
| `system/blockMeshDict` | yMax widened `1.50 → 1.80` and zMin widened `-0.05 → -0.15` so the background box contains the branch STL for any α in `[25, 90]` deg (background = 10 × 70 × 237 = 165 900 cells). |
| `doe/stamp_cases.py` | Single `TOKENS` list covers every angle-dependent / D2-dependent placeholder. No regex surgery. Per-row `alpha_deg` column in the CSV takes precedence over env var. Leftover-token guard trips if anything is unsubstituted. |
| `doe/lhs_design.py` | Writes `alpha_deg` column (new; default read from `ALPHA_DEG` env) so the CSV self-documents the campaign. |
| `doe/sanity_check.py` | End-to-end pre-flight: design audit, STL water-tightness for smallest/largest D2, dry-stamp with leftover-token check, optional mesh smoke test with `blockMesh + snappyHexMesh + checkMesh`. Works for any `--alpha` value. |

### Pre-flight sanity results (just now)

Run: `python3 sanity_check.py --alpha 30 --design doe_design.csv --base .. --case 1`

| Check | Result |
| --- | --- |
| DoE design audit | 10 rows, d/D ∈ [0.196, 0.396], HBR ∈ [5.96%, 19.45%], VR ∈ [0.69, 5.84] (under cap 12). 5 unique d/D slices × 2 points/slice. PASS |
| STL water-tightness at D2_min | ratio = 0.9826 — PASS |
| STL water-tightness at D2_max | ratio = 0.9037 — PASS |
| Dry-stamp case 01 (leftover-token check) | no unresolved `@XXX@` — PASS |
| `blockMesh + snappyHexMesh + checkMesh` | 508 k cells, max non-ortho 64.5, max skewness 1.42, aspect ratio 10.8, `Mesh OK.`, 51 branch_inlet faces — PASS |

Run: `python3 sanity_check.py --alpha 45` (angle-agnosticism test at a brand-new angle)

| Check | Result |
| --- | --- |
| Mesh smoke test at α=45° | max non-ortho 61.7, max skewness 0.86, 69 branch_inlet faces, `Mesh OK.` — PASS |

### LHS constraint coverage (doe_design.csv)

| Constraint | Target | Actual |
| --- | --- | --- |
| Total cases | 10 | 10 |
| Unique d/D slices | 5 | 5 |
| HBR band | [5%, 20%] | [5.96%, 19.45%] |
| d/D band | [0.15, 0.45] | [0.196, 0.396] |
| VR cap | ≤ 12 | max = 5.84 |

## How to run the campaign

```bash
# on the remote, inside a tmux session
cd ~/openfoam_case_rans_doe_30deg_base/doe
./run_doe_30deg.sh            # all 10 cases, mesh reuse across slices
# or
./run_doe_30deg.sh --only 03,07
```

Results land in `~/openfoam_case_rans_doe_30deg/doe_results/` with
`STATUS.md` refreshed every ~60 s for live tracking.

## How to spin up a campaign at any other angle

No code changes needed.

```bash
cd ~/openfoam_case_rans_doe_30deg_base/doe

# 1. regenerate the design CSV with the new angle column
python3 lhs_design.py --seed 42 --alpha-deg 60

# 2. sanity-check at the new angle (STL + dry-stamp + mesh smoke)
python3 sanity_check.py --alpha 60 --design doe_design.csv --base ..

# 3. stamp and run
python3 stamp_cases.py --design doe_design.csv --base .. \
        --cases ~/openfoam_case_rans_doe_60deg/doe_cases --overwrite
CASES_DIR=~/openfoam_case_rans_doe_60deg/doe_cases \
  RESULTS_DIR=~/openfoam_case_rans_doe_60deg/doe_results \
  ./run_doe.sh
```
