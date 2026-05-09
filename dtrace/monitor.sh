#!/usr/bin/env sh
# PysiAdmin — dtrace/monitor.sh
# Launches all four DTrace probes in background, logs to logs/dtrace_YYYYMMDD.log
# Run: sudo sh dtrace/monitor.sh
set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "[dtrace] Must run as root." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/../logs"
mkdir -p "$LOG_DIR"
TODAY="$(date -u +%Y%m%d)"
LOGFILE="${LOG_DIR}/dtrace_${TODAY}.log"

echo "[dtrace] Logging to ${LOGFILE}"
echo "[dtrace] Starting all probes. Ctrl+C to stop."

dtrace -s "${SCRIPT_DIR}/exec_monitor.d" >> "$LOGFILE" 2>&1 &
PID_EXEC=$!

dtrace -s "${SCRIPT_DIR}/net_monitor.d"  >> "$LOGFILE" 2>&1 &
PID_NET=$!

dtrace -s "${SCRIPT_DIR}/file_monitor.d" >> "$LOGFILE" 2>&1 &
PID_FILE=$!

dtrace -s "${SCRIPT_DIR}/priv_monitor.d" >> "$LOGFILE" 2>&1 &
PID_PRIV=$!

echo "[dtrace] PIDs: exec=$PID_EXEC net=$PID_NET file=$PID_FILE priv=$PID_PRIV"

trap "kill $PID_EXEC $PID_NET $PID_FILE $PID_PRIV 2>/dev/null; echo '[dtrace] Stopped.'" INT TERM
wait
