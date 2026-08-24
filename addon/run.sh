#!/bin/sh
set -eu

CERT="/data/codex-file-bridge.crt"
KEY="/data/codex-file-bridge.key"
SAN_STATE="/data/codex-file-bridge.san"

SAN="$(
python3 - <<'PY'
import ipaddress
import json
import re

with open("/data/options.json", "r", encoding="utf-8") as f:
    options = json.load(f)

dns_raw = str(options.get("tls_san_dns", "homeassistant,homeassistant.local")).strip()
ip_raw = str(options.get("tls_san_ip", "")).strip()

parts = []
for name in (x.strip() for x in dns_raw.split(",")):
    if not name:
        continue
    if not re.fullmatch(r"[A-Za-z0-9.-]+", name):
        raise SystemExit(f"Invalid TLS DNS SAN: {name!r}")
    parts.append(f"DNS:{name}")

if ip_raw:
    try:
        ipaddress.ip_address(ip_raw)
    except ValueError as exc:
        raise SystemExit(f"Invalid TLS IP SAN: {ip_raw!r}") from exc
    parts.append(f"IP:{ip_raw}")

if not parts:
    raise SystemExit("At least one TLS SAN must be configured")

print(",".join(parts))
PY
)"

CURRENT_SAN=""
if [ -s "$SAN_STATE" ]; then
    CURRENT_SAN="$(cat "$SAN_STATE")"
fi

if [ ! -s "$CERT" ] || [ ! -s "$KEY" ] || [ "$CURRENT_SAN" != "$SAN" ]; then
    echo "Generating Home Assistant Codex Bridge TLS certificate..."
    echo "Configured SAN: $SAN"

    rm -f "$CERT" "$KEY"

    openssl req \
        -x509 \
        -newkey rsa:3072 \
        -sha256 \
        -nodes \
        -days 3650 \
        -keyout "$KEY" \
        -out "$CERT" \
        -subj "/CN=home-assistant-codex-bridge" \
        -addext "subjectAltName=$SAN"

    chmod 600 "$KEY"
    chmod 644 "$CERT"
    printf '%s\n' "$SAN" > "$SAN_STATE"
    chmod 600 "$SAN_STATE"
fi

echo
echo "TLS certificate SHA256 fingerprint:"
openssl x509 -in "$CERT" -noout -fingerprint -sha256
echo

exec python3 /server.py
