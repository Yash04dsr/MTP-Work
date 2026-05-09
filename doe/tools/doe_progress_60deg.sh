#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  doe_progress_60deg.sh -- live progress for the 60 deg DoE on doe-pri
#
#  Usage:
#      ./doe_progress_60deg.sh                # snapshot (default)
#      ./doe_progress_60deg.sh watch          # live refresh every 30 s
#      ./doe_progress_60deg.sh tail           # tail the running case's log.solver
#      ./doe_progress_60deg.sh attach         # attach to the orchestrator tmux
#      ./doe_progress_60deg.sh pull N         # rsync case N results to local Mac
# ---------------------------------------------------------------------------
set -euo pipefail

REMOTE="${REMOTE:-doe-pri}"
STATUS="\$HOME/openfoam_case_rans_doe_60deg/doe_results/STATUS.md"
LOG_DIR="\$HOME/openfoam_case_rans_doe_60deg_base/doe/logs"
MAC_BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/results_full_60deg"

cmd="${1:-snap}"

snapshot() {
    printf "\033[2J\033[H"
    ssh -o ConnectTimeout=8 "$REMOTE" "bash -lc '
        date;
        echo;
        cat $STATUS 2>/dev/null || echo \"(no STATUS.md yet)\";
        echo;
        echo \"--- last 6 orchestrator lines ---\";
        tail -n 6 $LOG_DIR/run_60deg_latest.log 2>/dev/null || true;
        echo;
        echo \"--- active solver / mesh procs ---\";
        n=\$(ps -eo comm | awk \"/^rhoReactingBuoy/\" | wc -l);
        ms=\$(ps -eo comm | awk \"/^snappyHexMesh|^blockMesh/\" | wc -l);
        ps -eo etime,pcpu,comm | awk \"/^[ ]*[0-9].*(rhoReactingBuoy|snappyHexMesh|blockMesh)/\" | head -2 || true;
        echo \"  rhoReactingBuoyantFoam ranks: \$n   mesh procs: \$ms\";
    '"
}

case "$cmd" in
    snap|snapshot|"")
        snapshot
        ;;
    watch|live)
        echo "live refresh every 30 s -- Ctrl-C to stop"
        while true; do
            snapshot
            sleep 30
        done
        ;;
    tail)
        ssh -t "$REMOTE" "bash -lc '
            running=\$(grep -E \"^\| case_[0-9]+ \| RUNNING \" $STATUS 2>/dev/null | head -1 | awk \"{print \\\$2}\");
            [ -z \"\$running\" ] && { echo \"no case currently RUNNING\"; exit 0; };
            log=\$HOME/openfoam_case_rans_doe_60deg/doe_cases/\$running/log.solver;
            echo \"tailing \$log -- Ctrl-C to stop\";
            tail -f \$log | grep --line-buffered -E \"(^Time = |Courant Number|deltaT = )\";
        '"
        ;;
    attach)
        ssh -t "$REMOTE" "tmux attach -t doe60"
        ;;
    pull)
        n="${2:?usage: $0 pull <case_number>}"
        n="$(printf '%02d' "$n")"
        echo "pulling case_$n results to $MAC_BASE/cases/case_$n/"
        mkdir -p "$MAC_BASE/cases/case_$n"
        rsync -avz --progress \
              --include="case.env" --include="case_info.json" \
              --include="Allrun" --include="generateSTL.py" \
              --include="SIM_DONE" --include="SIM_FAILED" \
              --include="log.*" \
              --include="figures/***" \
              --include="postProcessing/***" --include="constant/***" \
              --include="system/***" --include="scripts/***" \
              --include="0/***" --include="1.2/***" \
              --exclude="processor*" --exclude="dynamicCode" \
              "$REMOTE:openfoam_case_rans_doe_60deg/doe_cases/case_$n/" \
              "$MAC_BASE/cases/case_$n/"
        ;;
    *)
        echo "usage: $0 [snap|watch|tail|attach|pull N]"
        exit 2
        ;;
esac
