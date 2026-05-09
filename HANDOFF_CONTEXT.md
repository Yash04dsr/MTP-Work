# CFD Simulation Handoff Context

## Project Overview
Setting up OpenFOAM CFD simulations of a **hydrogen-into-methane T-junction mixing study** (based on Eames et al., Int. J. Hydrogen Energy, 2022). Running on **Windows 11 WSL2 Ubuntu** with OpenFOAM 2406, accessed remotely from a Mac via SSH.

## How Everything Is Accessed — IMPORTANT

I'm working on a **Mac** (macOS). The simulations run on a **Windows 11 machine** with **WSL2 Ubuntu**. All file editing and command execution happens **remotely via SSH from the Mac into the Windows WSL2 Ubuntu**.

### SSH Connection (from Mac terminal)
```bash
ssh -p 2222 psl_3@10.223.68.120
```
- **IP**: `10.223.68.120` (Windows machine on local network)
- **Port**: `2222` (forwarded from Windows to WSL2's SSH server on port 22)
- **User**: `psl_3`
- **Auth**: Password-less SSH key authentication (already configured, key in `~/.ssh/id_ed25519` on Mac, public key in `~/.ssh/authorized_keys` on WSL2)
- No password needed — just run the ssh command above

### How to run commands on the remote machine
Every command that modifies files or runs OpenFOAM must be executed **via SSH**. Example patterns:

**Single command:**
```bash
ssh -p 2222 psl_3@10.223.68.120 "ls ~/openfoam_case_rans/"
```

**Multi-line / heredoc file writes:**
```bash
ssh -p 2222 psl_3@10.223.68.120 'cat > ~/openfoam_case_rans/somefile << '"'"'EOF'"'"'
file content here
EOF'
```

**OpenFOAM commands (must source environment first):**
```bash
ssh -p 2222 psl_3@10.223.68.120 "cd ~/openfoam_case_rans && source /usr/lib/openfoam/openfoam2406/etc/bashrc && blockMesh"
```

**Long-running commands (use nohup so they survive SSH disconnect):**
```bash
ssh -p 2222 psl_3@10.223.68.120 "cd ~/openfoam_case_rans && source /usr/lib/openfoam/openfoam2406/etc/bashrc && nohup snappyHexMesh -overwrite > log.snappyHexMesh 2>&1 &"
```

### System Specs (Windows WSL2)
- **OpenFOAM version**: 2406 (installed at `/usr/lib/openfoam/openfoam2406/`)
- **Environment**: `source /usr/lib/openfoam/openfoam2406/etc/bashrc` (must run before any OpenFOAM command)
- **CPUs**: 20 cores available
- **RAM**: 56 GB allocated to WSL2
- **Python**: python3 with `numpy` and `numpy-stl` installed
- **MPI**: OpenMPI (use `--oversubscribe` flag with mpirun)
- **Build tools**: `build-essential` installed (needed for OpenFOAM dynamicCode compilation)

### Key Point
**You are NOT editing local files on the Mac.** All project files live on the Windows WSL2 system at `/home/psl_3/`. Every file read, write, and command execution goes through SSH. The Mac's workspace folder (`/Users/yash/Desktop/CFD Setup instructions/`) only has reference documents (papers, PDFs) — not the simulation files.

## Geometry
- **Main pipe**: D1 = 0.460 m, length = 9.200 m, axis along Z
- **Branch pipe**: D2 = 0.115 m (β = 0.25), 90° injection at Z = 4.600 m, axis along +Y, length = 1.380 m
- **Operating conditions**: 6.9 MPa, CH4 main flow at 284 K, H2 branch injection at 293 K
- Main inlet velocity: ~10 m/s (power law profile, n=7)
- Branch inlet velocity: ~32 m/s (fixed value, downward into main pipe)

## Directory Structure on WSL2
```
/home/psl_3/openfoam_case/        ← Original DDES case (STOPPED - was running on broken mesh)
/home/psl_3/openfoam_case_rans/   ← New RANS case (WORK IN PROGRESS)
```

## Critical Problem Found & Current Status

### The Root Cause Bug
The `generateSTL.py` script was generating the main pipe as a **complete, unbroken cylinder** with NO hole at the T-junction. The branch pipe STL was placed outside the main pipe wall. When `snappyHexMesh` ran, the flood-fill from `locationInMesh` stayed inside the sealed main pipe — **the branch pipe was never meshed**. Both the DDES and RANS cases had this problem.

Evidence:
- Mesh boundary file showed only 3 patches: `wall`, `main_inlet`, `outlet` — NO `branch_inlet`
- Mesh bounding box Y range: only -0.23 to 0.23 (main pipe radius, no branch extension)
- `setFields` only patched 2504 cells in a thin sliver at the top of the pipe near the junction
- The DDES simulation was running for days on this broken mesh (now killed)

### What I've Done So Far
1. **Killed the DDES solver** (was wasting CPU on broken mesh)
2. **Created `openfoam_case_rans/`** — copied from DDES, then modified all config files for steady-state RANS k-ω SST
3. **All RANS config files are correctly set up** (audited against literature):
   - `constant/turbulenceProperties`: RAS → kOmegaSST
   - `system/controlDict`: pseudo-steady with `localEuler`, 5000 iterations, deltaT=1
   - `system/fvSchemes`: `localEuler` ddt, `bounded Gauss linearUpwind` divSchemes, cell-limited gradients
   - `system/fvSolution`: PIMPLE (nOuter=1), relaxation factors (U:0.7, k:0.5, omega:0.5, p_rgh:0.3)
   - `0/k`, `0/omega`: turbulentIntensityKineticEnergyInlet / turbulentMixingLengthFrequencyInlet at inlets, wall functions at walls
   - `0/nut`: nutUSpaldingWallFunction at walls
   - `0/U`, `0/H2`, `0/CH4`, `0/T`, `0/p_rgh`, `0/p`, `0/alphat`: all in ASCII with correct BCs for 4 patches (main_inlet, branch_inlet, outlet, wall)
   - Removed `0/nuTilda` (not needed for k-ω SST)
   - `constant/thermophysicalProperties`: heRhoThermo, reactingMixture, sutherland transport, JANAF thermo, perfectGas EOS
   - `constant/reactions`: empty (no combustion, pure mixing study)
4. **Attempted to fix the STL generator twice**:
   - **Attempt 1**: Cut hole in main pipe, started branch from inside → NOT water-tight (gap at junction). snappyHexMesh kept cells outside the pipe too (total volume = 10.15 m³ vs expected ~1.54 m³). Had `allBoundary` patch with 140k faces.
   - **Attempt 2**: Added a "saddle patch" of triangles connecting the intersection curve on the main pipe to the branch pipe base at y=R1. Volume ratio check showed 0.321 (should be ~1.0) — **normals are likely inconsistent or the saddle patch geometry isn't correct**.

### What Needs To Be Done
1. **Fix `generateSTL.py`** to produce a water-tight T-junction STL:
   - The cylinder-cylinder intersection curve: for branch angle θ, x = R2·cos(θ), z = Z_JCT + R2·sin(θ), y = √(R1² - R2²·cos²(θ))
   - Main pipe wall must have a hole bounded by this intersection curve
   - Saddle patch triangles must connect the intersection curve to the branch pipe base
   - All triangle normals must point OUTWARD (away from pipe interior)
   - The signed volume check should give ratio ~1.0

2. **Regenerate mesh** (in `openfoam_case_rans/`):
   ```bash
   cd ~/openfoam_case_rans
   source /usr/lib/openfoam/openfoam2406/etc/bashrc
   rm -rf constant/polyMesh dynamicCode processor* log.*
   python3 generateSTL.py
   surfaceFeatureExtract
   blockMesh
   snappyHexMesh -overwrite
   checkMesh
   ```
   Verify:
   - `branch_inlet` patch exists in `constant/polyMesh/boundary`
   - Mesh bounding box Y extends to ~1.38 (branch pipe top)
   - Total volume ~1.54 m³ (not 10+ m³)
   - NO `allBoundary` patch (or 0 faces on it)
   - Target: 3-5M cells

3. **Run RANS simulation**:
   ```bash
   setFields
   decomposePar
   nohup mpirun --oversubscribe -np 16 rhoReactingBuoyantFoam -parallel > log.rhoReactingBuoyantFoam 2>&1 &
   ```

4. **After RANS works, also fix the DDES mesh** (same STL fix needed for `openfoam_case/`)

## Key Files Reference

### `system/blockMeshDict` — Background mesh
- Domain: x[-0.30, 0.30], y[-0.30, 1.50], z[-0.10, 9.30]
- Cells: (24 72 376) — sufficient for branch pipe region

### `system/snappyHexMeshDict` — Surface meshing
- STL files: `wall.stl`, `main_inlet.stl`, `outlet.stl`, `branch_inlet.stl` in `constant/triSurface/`
- `locationInMesh (0 0 2.0)` — inside main pipe
- Junction refinement: searchableSphere at (0,0,4.6) radius 0.690, level 2
- Wall refinement: level (2 2), inlet/outlet/branch: level (1 1)
- Layer addition enabled on wall

### `system/setFieldsDict` — Initial conditions
- Default: H2=0, CH4=1, U=(0,0,10)
- Branch region (cylinderToCell from y=0.20 to y=1.40, radius=0.06 at z=4.6): H2=1, CH4=0, U=(0,-32,0)

### `system/decomposeParDict`
- 16 subdomains, scotch method

## Files That Are Already Correct (don't modify)
- `constant/thermophysicalProperties` — verified
- `constant/reactions` — verified (empty, no combustion)
- `constant/thermo.compressibleGas` — JANAF data for H2, CH4
- `system/controlDict` — verified for RANS
- `system/fvSchemes` — verified for RANS with localEuler
- `system/fvSolution` — verified for RANS
- All `0/` files (k, omega, nut, U, H2, CH4, T, p, p_rgh, alphat) — verified

## The ONLY thing that needs fixing is `generateSTL.py` to produce a water-tight T-junction, then remesh and run.
