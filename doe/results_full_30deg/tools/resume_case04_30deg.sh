#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  resume_case04_30deg.sh
#
#  Resume the 30 deg case_04 transient from its last decomposed write
#  (t = 0.2 s) without going through run_doe.sh, so the existing
#  processor*/0.2 data is preserved (run_doe's Allrun would wipe it via
#  `rm -rf processor*/0.*` and re-decompose from 0/).
#
#  Run this on the compute host AFTER case_10 of the main 30 deg
#  campaign completes.
#
#  Usage:
#      ./resume_case04_30deg.sh
# ---------------------------------------------------------------------------
set -eo pipefail

CASE="${CASE:-$HOME/openfoam_case_rans_doe_30deg/doe_cases/case_04}"
RESULTS="${RESULTS:-$HOME/openfoam_case_rans_doe_30deg/doe_results/case_04}"
OPENFOAM_BASHRC="${OPENFOAM_BASHRC:-/usr/lib/openfoam/openfoam2406/etc/bashrc}"

cd "$CASE"

echo "[resume_case04] case dir : $CASE"
echo "[resume_case04] starting at $(date +%FT%T)"

# --- 0. sanity checks -----------------------------------------------------
if [[ ! -d processor0/0.2 ]]; then
    echo "[resume_case04] ERROR: processor0/0.2 not found -- nothing to resume"
    exit 1
fi
if grep -q "startFrom\s\+startTime" system/controlDict; then
    echo "[resume_case04] patching controlDict: startFrom startTime -> latestTime"
    sed -i 's/^\(\s*startFrom\s\+\)startTime;/\1latestTime;/' system/controlDict
fi

# --- 1. clear failed sentinel + old log ----------------------------------
rm -f SIM_FAILED
mv -f log.solver "log.solver.t0_to_0.2" 2>/dev/null || true

# --- 2. source OpenFOAM (silently) ---------------------------------------
set +eu
# shellcheck disable=SC1090
source "$OPENFOAM_BASHRC" 2>/dev/null
set -e

# --- 3. solver run (parallel, from existing decomposed state) ------------
echo "[resume_case04] launching solver from t = $(ls -d processor0/0.* 2>/dev/null | sort -V | tail -1 | xargs basename)"
mpirun --use-hwthread-cpus -n 16 rhoReactingBuoyantFoam -parallel 2>&1 | tee log.solver_resume

# --- 4. reconstruct latestTime ------------------------------------------
reconstructPar -latestTime 2>&1 | tee log.reconstructPar_resume

# --- 5. mark done and stash ---------------------------------------------
touch SIM_DONE
mkdir -p "$RESULTS"
cp -f log.solver_resume log.reconstructPar_resume "$RESULTS"/ 2>/dev/null || true
{
    echo "case       : case_04 (resumed)"
    echo "completed  : $(date +%FT%T)"
    echo "case_dir   : $CASE"
    echo "hostname   : $(hostname)"
    echo "note       : resumed from t=0.2 after manual SIGTERM during initial run"
} > "$RESULTS/PROVENANCE_resume.txt"

# --- 6. post-process metrics + figures (best-effort) --------------------
TOOLS=~/openfoam_case_rans_doe_30deg_base/tools
for tool in all_metrics.py make_figures.py make_distance_figures.py; do
    if [[ -x "$TOOLS/$tool" ]]; then
        echo "[resume_case04] running $tool"
        python3 "$TOOLS/$tool" --case "$CASE" --outdir "$RESULTS" \
            > "$RESULTS/$(basename "$tool" .py)_resume.log" 2>&1 \
            || echo "[resume_case04] [warn] $tool failed (see $RESULTS/$(basename "$tool" .py)_resume.log)"
    fi
done

echo "[resume_case04] DONE at $(date +%FT%T)"
