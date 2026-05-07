#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  doe_progress_120deg.sh -- live progress for the 120 deg DoE on doe-pri
#
#  Usage:
#      ./doe_progress_120deg.sh                # snapshot (default)
#      ./doe_progress_120deg.sh watch          # live refresh every 30 s
#      ./doe_progress_120deg.sh tail           # tail the running case's log.solver
#      ./doe_progress_120deg.sh attach         # attach to the orchestrator tmux
#      ./doe_progress_120deg.sh kill           # kill the orchestrator (asks before)
#      ./doe_progress_120deg.sh pull NN        # rsync case_NN finished outputs to Mac
# ---------------------------------------------------------------------------
set -euo pipefail

REMOTE="${REMOTE:-doe-pri}"
STATUS="\$HOME/openfoam_case_rans_doe_120deg/doe_results/STATUS.md"
LOG_DIR="\$HOME/openfoam_case_rans_doe_120deg_base/doe/logs"
MAC_BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/results_full_120deg"

cmd="${1:-snap}"

snapshot() {
    printf "\033[2J\033[H"
    ssh -o ConnectTimeout=8 "$REMOTE" "bash -lc '
        date;
        echo;
        cat $STATUS 2>/dev/null || echo \"(no STATUS.md yet)\";
        echo;
        echo \"--- last 6 orchestrator lines ---\";
        tail -n 6 $LOG_DIR/run_120deg_latest.log 2>/dev/null || true;
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
            log=\$HOME/openfoam_case_rans_doe_120deg/doe_cases/\$running/log.solver;
            echo \"tailing \$log -- Ctrl-C to stop\";
            tail -f \$log | grep --line-buffered -E \"(^Time = |Courant Number|deltaT = )\";
        '"
        ;;
    attach)
        ssh -t "$REMOTE" "tmux attach -t doe120"
        ;;
    kill)
        printf "really kill orchestrator + any running solver on $REMOTE? [y/N] "
        read -r ans
        if [[ "$ans" =~ ^[Yy]$ ]]; then
            ssh "$REMOTE" "bash -lc 'tmux kill-session -t doe120 2>/dev/null; pkill -f rhoReactingBuoy 2>/dev/null; pkill -f snappyHexMesh 2>/dev/null; echo done'"
        else
            echo "aborted"
        fi
        ;;
    pull)
        n="${2:-}"
        [[ -z "$n" ]] && { echo "usage: $0 pull NN"; exit 2; }
        n=$(printf "%02d" "${n#0}")
        echo "rsync remote case_$n -> $MAC_BASE/cases/case_$n/"
        rsync -av --info=stats1 \
              --include="case_info.json" --include="log.*" --include="SIM_DONE" \
              --include="postProcessing/***" --include="constant/polyMesh/***" \
              --include="1.2/***" --exclude="*" \
              "$REMOTE:openfoam_case_rans_doe_120deg/doe_cases/case_$n/" \
              "$MAC_BASE/cases/case_$n/"
        ;;
    *)
        echo "usage: $0 [snap|watch|tail|attach|kill|pull NN]"
        exit 2
        ;;
esac
