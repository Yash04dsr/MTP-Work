#!/usr/bin/env bash
# doe_watch.sh -- htop-style live view of doe_status.sh.
#
# Usage :
#     ./doe_watch.sh                           # refresh every 10 s
#     ./doe_watch.sh 5                         # refresh every 5 s
#     ./doe_watch.sh 10 /path/to/doe_root      # custom root
#     REFRESH=30 ./doe_watch.sh                # via env var
#
# Ctrl-C to exit.  Safe from any SSH session -- purely read-only.

set -u

INTERVAL="${1:-${REFRESH:-10}}"
ROOT="${2:-}"

SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
STATUS="$SELF_DIR/doe_status.sh"

if [[ ! -x "$STATUS" ]]; then
    chmod +x "$STATUS" 2>/dev/null || true
fi

trap 'printf "\n\nexit.\n"; exit 0' INT TERM

while true; do
    clear
    if [[ -n "$ROOT" ]]; then
        bash "$STATUS" "$ROOT"
    else
        bash "$STATUS"
    fi
    printf -- '---  refreshing every %ss   ctrl-c to quit  ---\n' "$INTERVAL"
    sleep "$INTERVAL"
done
