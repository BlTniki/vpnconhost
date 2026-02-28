#!/usr/bin/env bash
set -euo pipefail

default_iface() {
  ip route show default 0.0.0.0/0 2>/dev/null | awk '{print $5; exit}'
}

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing '$1'. Install: sudo apt-get update && sudo apt-get install -y wireguard-tools"
    exit 1
  }
}

need ip
need wg

IFACE="$(default_iface || true)"
if [[ -z "${IFACE}" ]]; then
  echo "Could not detect default interface."
  echo "Run: ip route"
  exit 1
fi

PRIV_KEY="$(wg genkey)"
PUB_KEY="$(printf "%s" "$PRIV_KEY" | wg pubkey)"

echo "Detected default external interface:"
echo "  $IFACE"
echo
echo "Generated WireGuard keys:"
echo "  PrivateKey: $PRIV_KEY"
echo "  PublicKey:  $PUB_KEY"
echo
echo "Paste into your .env (example):"
echo "WG_EXTERNAL_IFACE=$IFACE"
echo "WG_PRIVATE_KEY=$PRIV_KEY"
