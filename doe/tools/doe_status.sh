#!/usr/bin/env bash
# doe_status.sh -- snapshot of the DoE campaign.
#
# Scans doe_cases/ and doe_results/ and prints, per case:
#
#     case_NN  [STATE]   progress   t_elapsed / t_sim   residuals (U/p_rgh)
#
# STATE   = DONE | RUNNING | FAILED | PENDING
# Works entirely from log files, so it is safe to call while the solver is
# running (read-only) and can be invoked from any SSH session.
#
# Usage :
#     ./doe_status.sh                          # auto-detect root
#     ./doe_status.sh /path/to/doe_root        # explicit root
#
# Where doe_root contains  doe_cases/  and  doe_results/.
# The script also writes doe_root/doe_results/STATUS.md (markdown), which
# is what run_doe.sh uses as the live heartbeat file.

set -u

# ---------- locate DoE root ---------------------------------------
if [[ $# -ge 1 ]]; then
    ROOT="${1%/}"
else
    # default: parent of the script (the repo structure is
    # doe_base/tools/doe_status.sh  ->  root = parent of doe_base)
    SELF="$(cd "$(dirname "$0")" && pwd)"
    ROOT="$(dirname "$(dirname "$SELF")")"
    # If run as ~/openfoam_case_rans_doe_base/tools/doe_status.sh
    # we actually want ~/openfoam_case_rans_doe which holds the live runs.
    if [[ ! -d "$ROOT/doe_cases" ]]; then
        CAND="$HOME/openfoam_case_rans_doe"
        if [[ -d "$CAND/doe_cases" ]]; then
            ROOT="$CAND"
        fi
    fi
fi

CASES_DIR="$ROOT/doe_cases"
RES_DIR="$ROOT/doe_results"

if [[ ! -d "$CASES_DIR" ]]; then
    echo "doe_status.sh: $CASES_DIR not found (pass DoE root as \$1)"
    exit 2
fi
mkdir -p "$RES_DIR"

END_TIME_DEFAULT="1.2"

# Pull endTime from doe_base controlDict, falling back to default.
END_TIME="$(grep -E '^endTime' "$ROOT/doe_base/system/controlDict" 2>/dev/null \
          | awk '{print $2}' | tr -d ';' | head -n1)"
END_TIME="${END_TIME:-$END_TIME_DEFAULT}"

# ---------- helpers -----------------------------------------------
hms() {                                   # seconds -> HH:MM:SS
    local s=${1%.*}
    [[ -z "$s" || "$s" == "-" ]] && { echo "--:--:--"; return; }
    printf '%02d:%02d:%02d' $((s/3600)) $(((s/60)%60)) $((s%60))
}

# Extract last solver time from log.solver (looks for 'Time = 0.123')
last_sim_time() {
    local log="$1"
    [[ -f "$log" ]] || { echo "-"; return; }
    # use last occurrence of "Time = " at column 0
    tac "$log" 2>/dev/null | grep -m1 -E '^Time = ' \
        | awk '{print $3}' | tr -d 's'
}

# Extract last U / p_rgh residual (final residual only).
last_residual() {
    local log="$1" field="$2"
    [[ -f "$log" ]] || { echo "-"; return; }
    tac "$log" 2>/dev/null \
        | grep -m1 -E "Solving for $field" \
        | sed -nE 's/.*Final residual = ([0-9.eE+-]+).*/\1/p'
}

# Elapsed wall-clock since log.solver started being written.
elapsed_sec() {
    local log="$1"
    [[ -f "$log" ]] || { echo "-"; return; }
    local start=$(stat -c %Y "$log" 2>/dev/null || stat -f %m "$log")
    local now=$(date +%s)
    echo $(( now - start ))
}

# ---------- discover cases ----------------------------------------
mapfile -t CASES < <(ls -d "$CASES_DIR"/case_* 2>/dev/null | sort)

if [[ ${#CASES[@]} -eq 0 ]]; then
    echo "No cases found under $CASES_DIR."
    exit 0
fi

# ---------- header ------------------------------------------------
NOW="$(date '+%Y-%m-%d %H:%M:%S')"
BOLD=$'\e[1m'; GREEN=$'\e[32m'; YEL=$'\e[33m'; RED=$'\e[31m'
DIM=$'\e[2m'; RST=$'\e[0m'
is_tty=0
[[ -t 1 ]] && is_tty=1

pcol() {  # $1 state token, $2 text
    local st="$1" txt="$2"
    (( is_tty )) || { printf '%s' "$txt"; return; }
    case "$st" in
        DONE)     printf '%s%s%s' "$GREEN" "$txt" "$RST" ;;
        RUNNING)  printf '%s%s%s' "$BOLD$YEL" "$txt" "$RST" ;;
        FAILED)   printf '%s%s%s' "$RED" "$txt" "$RST" ;;
        *)        printf '%s%s%s' "$DIM" "$txt" "$RST" ;;
    esac
}

printf '\n%sDoE status%s  (%s)\n' "$BOLD" "$RST" "$NOW"
printf 'root    = %s\n' "$ROOT"
printf 'endTime = %s s\n\n' "$END_TIME"
printf '%-10s %-9s %-9s %-10s %-10s %-10s  %s\n' \
       "case" "state" "t_sim" "progress" "U_res" "p_res" "wall_elapsed"
printf '%s\n' "----------------------------------------------------------------------------"

# ---------- build STATUS.md in parallel ---------------------------
md="$RES_DIR/STATUS.md"
{
    echo "# DoE live status"
    echo
    echo "_Updated: **$NOW**  (endTime = $END_TIME s)_"
    echo
    echo "| case | state | t_sim | progress | U_res | p_res | wall_elapsed |"
    echo "|---|---|---:|---:|---:|---:|---:|"
} > "$md"

done_cnt=0; fail_cnt=0; run_cnt=0; pend_cnt=0
total_done_sec=0

for d in "${CASES[@]}"; do
    c=$(basename "$d")
    logS="$d/log.solver"
    resdir="$RES_DIR/$c"

    state="PENDING"
    if [[ -f "$resdir/SIM_DONE" || -f "$d/SIM_DONE" ]]; then
        state="DONE"
    elif [[ -f "$resdir/SIM_FAILED" || -f "$d/SIM_FAILED" ]]; then
        state="FAILED"
    elif [[ -f "$logS" ]]; then
        # Running unless log.solver has a clean 'End' marker recently.
        if tac "$logS" 2>/dev/null | head -n 20 | grep -qE '^End$|ExecutionTime'; then
            # log present but ended -> treat as DONE (runner will post-process).
            state="DONE"
        else
            state="RUNNING"
        fi
    fi

    tsim="$(last_sim_time "$logS")"
    prog="-"
    if [[ "$tsim" != "-" && -n "$tsim" ]]; then
        prog="$(awk -v t="$tsim" -v E="$END_TIME" 'BEGIN{printf "%.1f%%", 100.0*t/E}')"
    fi
    ur="$(last_residual "$logS" "Ux")"
    [[ -z "$ur" || "$ur" == "-" ]] && ur="$(last_residual "$logS" "U")"
    pr="$(last_residual "$logS" "p_rgh")"
    el="-"
    if [[ "$state" == "RUNNING" ]]; then
        el=$(elapsed_sec "$logS")
    elif [[ "$state" == "DONE" && -f "$resdir/case_info.json" ]]; then
        # prefer recorded wall-clock from case_info.json if runner wrote it
        el=$(grep -oE '"wall_seconds"\s*:\s*[0-9.]+' "$resdir/case_info.json" \
             | awk -F: '{print $2}' | tr -d ' ')
        [[ -z "$el" ]] && el="-"
    fi

    case "$state" in
        DONE)    done_cnt=$((done_cnt+1))
                 [[ "$el" != "-" ]] && total_done_sec=$((total_done_sec + ${el%.*})) ;;
        FAILED)  fail_cnt=$((fail_cnt+1)) ;;
        RUNNING) run_cnt=$((run_cnt+1)) ;;
        *)       pend_cnt=$((pend_cnt+1)) ;;
    esac

    el_hms="$(hms "$el")"
    ur_p="${ur:--}"; pr_p="${pr:--}"
    # format residuals defensively (could be "-", empty, or a number).
    fmt_res() {
        local x="$1"
        if [[ -z "$x" || "$x" == "-" ]]; then
            echo "    -    "
        else
            awk -v v="$x" 'BEGIN{printf "%.3e", v}'
        fi
    }
    ur_fmt="$(fmt_res "$ur_p")"
    pr_fmt="$(fmt_res "$pr_p")"

    printf '%-10s ' "$c"
    pcol "$state" "$(printf '%-9s' "$state")"
    printf ' %-9s %-10s %-11s %-11s  %s\n' \
           "${tsim:--}" "$prog" "${ur_fmt}" "${pr_fmt}" "$el_hms"

    echo "| $c | $state | ${tsim:--} | $prog | ${ur_fmt} | ${pr_fmt} | $el_hms |" >> "$md"
done

avg="-"
if (( done_cnt > 0 )); then
    avg=$(( total_done_sec / done_cnt ))
fi
remaining=$(( ${#CASES[@]} - done_cnt - fail_cnt ))
eta="-"
if [[ "$avg" != "-" && $avg -gt 0 && $remaining -gt 0 ]]; then
    eta=$(( avg * remaining ))
fi

printf '\n%sdone%s=%d  %srunning%s=%d  pending=%d  %sfailed%s=%d   (total %d)\n' \
       "$GREEN" "$RST" "$done_cnt" \
       "$BOLD$YEL" "$RST" "$run_cnt" \
       "$pend_cnt" \
       "$RED" "$RST" "$fail_cnt" \
       "${#CASES[@]}"
printf 'avg wall/case = %s   ETA remaining = %s\n\n' \
       "$(hms "$avg")" "$(hms "$eta")"

{
    echo
    echo "**done** = $done_cnt &nbsp;&nbsp; **running** = $run_cnt &nbsp;&nbsp;"
    echo "pending = $pend_cnt &nbsp;&nbsp; **failed** = $fail_cnt &nbsp;&nbsp;"
    echo "(total = ${#CASES[@]})"
    echo
    echo "- avg wall-clock per completed case : \`$(hms "$avg")\`"
    echo "- ETA for remaining $remaining cases  : \`$(hms "$eta")\`"
    echo
} >> "$md"

exit 0
