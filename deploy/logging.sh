#!/usr/bin/env bash
# Gedeeld door install.sh / run.sh / doctor.sh: alles wat op het scherm komt gaat ook naar logs/<naam>_<datum>.log
# (zonder kleurcodes) + logs/laatste_<naam>.log. Bij een fout staat regelnummer + commando onderaan de log.
# Gebruik:  source "$SCRIPT_DIR/deploy/logging.sh" <naam>
_name="${1:-spark}"
LOG_DIR="${SPARK_LOG_DIR:-$SCRIPT_DIR/logs}"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/${_name}_$(date +%Y%m%d_%H%M%S).log"
LATEST="$LOG_DIR/laatste_${_name}.log"
: > "$LOG_FILE"; ln -sf "$(basename "$LOG_FILE")" "$LATEST"
{
  echo "# $_name — $(date '+%F %T') — $(uname -s) $(uname -m) — user: $(id -un) — map: $SCRIPT_DIR"
  echo "# commando: $0 ${*:2}"
} >> "$LOG_FILE"
exec > >(tee >(sed -u 's/\x1b\[[0-9;]*m//g' >> "$LOG_FILE")) 2>&1
_log_on_err() { echo -e "\n\033[0;31m[FOUT]\033[0m regel $1 in $_name: '$2' (exit $3) — zie log: $LOG_FILE"; }
trap '_log_on_err "$LINENO" "$BASH_COMMAND" "$?"' ERR
_log_on_exit() { sleep 0.3; echo -e "\033[0;34m[LOG]\033[0m $LOG_FILE  (ook: $LATEST)"; }
trap '_log_on_exit' EXIT
