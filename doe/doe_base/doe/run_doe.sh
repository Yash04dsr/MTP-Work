#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  run_doe.sh  --  sequential, resumable DoE driver
#
#  Usage (from inside a tmux session on the compute host) :
#      cd ~/openfoam_case_rans_doe/doe
#      ./run_doe.sh                       # run every pending case in order
#      ./run_doe.sh --only 03,07          # run only cases 3 and 7
#      ./run_doe.sh --from 05             # resume from case 5 onwards
#
#  Resilience features
#  -------------------
#    1. After each case finishes, log.solver + case_info.json + metrics are
#       copied into   <DOE_RESULTS_DIR>/case_NN/   -- so if the PC crashes
#       mid-DoE, all completed results are preserved OUTSIDE the case
#       directory that might get clobbered.
#    2. The case directory keeps the sentinel file  SIM_DONE  on success,
#       and  SIM_FAILED  (with a copy of the last 200 log lines) on error.
#       Re-running run_doe.sh skips any case with SIM_DONE.
#    3. Mesh reuse : cases with the same slice_id share meshes.  The first
#       case in a slice builds the mesh; subsequent cases in that slice
#       import the polyMesh + decomposed processor dirs via $REUSE_MESH_FROM.
#    4. Metrics + figures computed per-case via all_metrics.py + make_figures
#       scripts from the doe tools dir (../tools/ by default).
# ---------------------------------------------------------------------------
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# The stamp_cases.py output lives in ../doe_cases by convention.
CASES_DIR="${CASES_DIR:-$(cd "${HERE}/../../doe_cases" 2>/dev/null && pwd || echo "${HOME}/openfoam_case_rans_doe/doe_cases")}"
RESULTS_DIR="${RESULTS_DIR:-${CASES_DIR}/../doe_results}"
TOOLS_DIR="${TOOLS_DIR:-${HERE}/../../tools}"

mkdir -p "${RESULTS_DIR}"

# ---- argument parsing ------------------------------------------------
FROM_CASE=""
ONLY_CASES=""
DRY_RUN=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --from)  FROM_CASE="$2"; shift 2 ;;
        --only)  ONLY_CASES="$2"; shift 2 ;;
        --dry)   DRY_RUN=1; shift ;;
        -h|--help)
            sed -n '1,35p' "$0"; exit 0 ;;
        *) echo "unknown flag: $1"; exit 2 ;;
    esac
done

log()  { echo "[run_doe] $(date +%FT%T) $*"; }
die()  { echo "[run_doe] ERROR: $*" >&2; exit 1; }

# ---- select cases ----------------------------------------------------
mapfile -t ALL_CASES < <(
    find "${CASES_DIR}" -maxdepth 1 -type d -name 'case_*' -printf '%f\n' | sort
)
if [[ ${#ALL_CASES[@]} -eq 0 ]]; then
    die "no case_NN/ dirs under ${CASES_DIR} -- did you run stamp_cases.py?"
fi

if [[ -n "${ONLY_CASES}" ]]; then
    IFS=',' read -ra WANT <<<"${ONLY_CASES}"
    SELECTED=()
    for n in "${WANT[@]}"; do
        SELECTED+=("case_$(printf '%02d' "${n#0}")")
    done
elif [[ -n "${FROM_CASE}" ]]; then
    START="case_$(printf '%02d' "${FROM_CASE#0}")"
    SELECTED=()
    for c in "${ALL_CASES[@]}"; do
        if [[ "$c" < "$START" ]]; then continue; fi
        SELECTED+=("$c")
    done
else
    SELECTED=("${ALL_CASES[@]}")
fi

log "selected ${#SELECTED[@]} cases : ${SELECTED[*]}"

# ---- per-case helpers ------------------------------------------------

# Given a case dir, return the slice_id it belongs to by sourcing case.env.
case_slice_id() {
    local cd="$1"
    # shellcheck disable=SC1090,SC1091
    ( source "${cd}/case.env" && echo "${SLICE_ID}" )
}

# Given a slice_id, return the first case in that slice that already has
# a polyMesh built.  Empty if none.
find_mesh_donor() {
    local slice="$1" target="$2"
    for c in "${ALL_CASES[@]}"; do
        local cdir="${CASES_DIR}/${c}"
        [[ "${cdir}" == "${target}" ]] && continue
        [[ -d "${cdir}/constant/polyMesh" ]] || continue
        local s
        s="$(case_slice_id "${cdir}")"
        if [[ "${s}" == "${slice}" ]]; then
            echo "${cdir}"
            return
        fi
    done
}

# Post-process a finished case.  Copies logs + computes metrics + figures.
post_process() {
    local cdir="$1" cname
    cname="$(basename "${cdir}")"
    local out="${RESULTS_DIR}/${cname}"
    mkdir -p "${out}"

    cp -f "${cdir}/case_info.json" "${out}/"           2>/dev/null || true
    cp -f "${cdir}/log.solver"     "${out}/log.solver" 2>/dev/null || true
    cp -f "${cdir}/log.blockMesh"  "${out}/"           2>/dev/null || true
    cp -f "${cdir}/log.snappyHexMesh" "${out}/"        2>/dev/null || true
    cp -f "${cdir}/log.checkMesh"  "${out}/"           2>/dev/null || true
    if [[ -d "${cdir}/postProcessing" ]]; then
        tar czf "${out}/postProcessing.tar.gz" \
            -C "${cdir}" postProcessing 2>/dev/null || true
    fi

    # Detailed CoV + Delta-p metrics via all_metrics.py.  Best-effort:
    # if the tool isn't available we still have the raw logs / postProc.
    if [[ -x "${TOOLS_DIR}/all_metrics.py" ]]; then
        python3 "${TOOLS_DIR}/all_metrics.py" \
            --case "${cdir}" \
            --outdir "${out}" \
            --label "${cname}" \
            > "${out}/all_metrics.log" 2>&1 \
            || log "[warn] all_metrics.py failed for ${cname} (see ${out}/all_metrics.log)"
    fi

    # Optional figure pack (skipped if pvbatch/pyvista not installed).
    if [[ -x "${TOOLS_DIR}/make_figures.py" ]]; then
        python3 "${TOOLS_DIR}/make_figures.py" \
            --case "${cdir}" --outdir "${out}/figures" \
            > "${out}/make_figures.log" 2>&1 \
            || log "[warn] make_figures.py failed for ${cname}"
    fi

    # Tiny provenance file : git-like commit info for results.
    {
        echo "case       : ${cname}"
        echo "completed  : $(date +%FT%T)"
        echo "case_dir   : ${cdir}"
        echo "hostname   : $(hostname)"
    } > "${out}/PROVENANCE.txt"

    log "[${cname}] stashed results -> ${out}"
}

# ---- main loop -------------------------------------------------------
RUN_START="$(date +%s)"
for cname in "${SELECTED[@]}"; do
    cdir="${CASES_DIR}/${cname}"
    [[ -d "${cdir}" ]] || { log "[skip] ${cname} : no dir"; continue; }

    if [[ -f "${cdir}/SIM_DONE" ]]; then
        log "[skip] ${cname} : already done (SIM_DONE present)"
        # Even so, make sure results are copied (useful on first resume).
        post_process "${cdir}"
        continue
    fi

    # Mesh reuse : find a donor case within the same slice.
    slice="$(case_slice_id "${cdir}")"
    donor=""
    donor="$(find_mesh_donor "${slice}" "${cdir}")" || true
    if [[ -n "${donor}" ]]; then
        log "[${cname}] mesh-reuse from ${donor}"
        export REUSE_MESH_FROM="${donor}"
    else
        log "[${cname}] first case in slice ${slice} -- will build mesh"
        unset REUSE_MESH_FROM || true
    fi

    log "[${cname}] launching Allrun"
    if [[ "${DRY_RUN}" -eq 1 ]]; then
        log "[dry]  would run : ${cdir}/Allrun"
        continue
    fi

    start_ts="$(date +%s)"
    if bash "${cdir}/Allrun" >> "${cdir}/log.run_doe" 2>&1; then
        elapsed=$(( $(date +%s) - start_ts ))
        log "[${cname}] SIM OK  (${elapsed}s wall)"
        post_process "${cdir}"
    else
        elapsed=$(( $(date +%s) - start_ts ))
        log "[${cname}] SIM FAILED  (${elapsed}s wall)"
        tail -n 200 "${cdir}/log.run_doe" > "${cdir}/SIM_FAILED" || true
        post_process "${cdir}"
        log "[${cname}] continuing with next case"
    fi
done

RUN_END="$(date +%s)"
TOTAL=$(( RUN_END - RUN_START ))
log "DoE loop finished in ${TOTAL}s (= $(( TOTAL / 60 )) min)"
log "Results archive : ${RESULTS_DIR}"
