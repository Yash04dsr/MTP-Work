#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  run_doe_30deg.sh  --  thin wrapper over run_doe.sh for the 30 deg campaign
#
#  Sets the right CASES_DIR / RESULTS_DIR / TOOLS_DIR for the 30 deg fork,
#  then delegates to run_doe.sh.  Use this from a tmux session.
#
#  Usage:
#      cd ~/openfoam_case_rans_doe_30deg_base/doe
#      ./run_doe_30deg.sh                  # all 10 cases in order
#      ./run_doe_30deg.sh --only 03,07     # specific cases
#      ./run_doe_30deg.sh --from 05        # resume
# ---------------------------------------------------------------------------
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export CASES_DIR="${CASES_DIR:-$HOME/openfoam_case_rans_doe_30deg/doe_cases}"
export RESULTS_DIR="${RESULTS_DIR:-$HOME/openfoam_case_rans_doe_30deg/doe_results}"
export TOOLS_DIR="${TOOLS_DIR:-$HOME/openfoam_case_rans_doe_30deg_base/tools}"

echo "[run_doe_30deg] CASES_DIR  = $CASES_DIR"
echo "[run_doe_30deg] RESULTS_DIR= $RESULTS_DIR"
echo "[run_doe_30deg] TOOLS_DIR  = $TOOLS_DIR"

mkdir -p "$RESULTS_DIR"

exec "$HERE/run_doe.sh" "$@"
