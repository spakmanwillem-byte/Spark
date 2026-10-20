#!/usr/bin/env bash
# DuckDNS-updater: houdt JOUWNAAM.duckdns.org gelijk aan je (wisselende) Ziggo-IP.
#
# Eenmalig:
#   sudo cp deploy/duckdns-update.sh /usr/local/bin/duckdns-update.sh && sudo chmod +x /usr/local/bin/duckdns-update.sh
#   sudo nano /etc/duckdns.conf    →  DOMAIN=jouwnaam   TOKEN=xxxx-xxxx   (token staat op duckdns.org na inloggen)
#   echo '*/5 * * * * root /usr/local/bin/duckdns-update.sh' | sudo tee /etc/cron.d/duckdns
set -euo pipefail
CONF="${DUCKDNS_CONF:-/etc/duckdns.conf}"
[ -f "$CONF" ] || { echo "Geen $CONF (DOMAIN=... TOKEN=...)"; exit 1; }
# shellcheck disable=SC1090
. "$CONF"
RESULT=$(curl -fs --max-time 10 "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=" || echo "KO")
echo "$(date '+%F %T') duckdns ${DOMAIN}: ${RESULT}" >> /var/log/duckdns.log
[ "$RESULT" = "OK" ]
