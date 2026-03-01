#!/usr/bin/env bash
set -euo pipefail

VM_NAME="${VM_NAME:-vpnlab}"
CPU="${CPU:-2}"
MEM="${MEM:-4G}"
DISK="${DISK:-20G}"
UBUNTU="${UBUNTU:-24.04}"

MOUNT_SRC="$(pwd)"
MOUNT_DST="/home/ubuntu/project"

vm_exists() {
  multipass info "$VM_NAME" >/dev/null 2>&1
}

vm_state() {
  multipass info "$VM_NAME" 2>/dev/null | awk -F': *' '/^State:/{print $2; exit}'
}

ensure_vm_created() {
  if vm_exists; then
    echo "[i] VM '$VM_NAME' already exists"
  else
    echo "[i] Creating VM '$VM_NAME'..."
    multipass launch "$UBUNTU" \
      --name "$VM_NAME" \
      --cpus "$CPU" \
      --memory "$MEM" \
      --disk "$DISK" \
      --cloud-init vm/cloud-init.yaml
  fi
}

ensure_vm_running() {
  local st
  st="$(vm_state || true)"

  if [[ "$st" == "Running" ]]; then
    return 0
  fi

  echo "[i] Starting VM '$VM_NAME' (current state: ${st:-unknown})..."
  multipass start "$VM_NAME"

  for _ in {1..30}; do
    st="$(vm_state || true)"
    [[ "$st" == "Running" ]] && return 0
    sleep 1
  done

  echo "[!] VM '$VM_NAME' did not reach Running state in time. Current state: ${st:-unknown}" >&2
  exit 1
}

ensure_wg_tools() {
  echo "[i] Checking wireguard tools inside VM..."
  if multipass exec "$VM_NAME" -- bash -lc 'command -v wg >/dev/null 2>&1'; then
    echo "[i] wg is already installed"
    return 0
  fi

  echo "[i] Installing wireguard-tools (bootstrap)..."
  multipass exec "$VM_NAME" -- bash -lc 'sudo apt-get update && sudo apt-get install -y wireguard-tools iproute2'
}

is_mounted() {
  multipass info "$VM_NAME" 2>/dev/null | grep -Eq "=>[[:space:]]*${MOUNT_DST}([[:space:]]|$)"
}

ensure_mount() {
  if is_mounted; then
    echo "[i] '${MOUNT_DST}' is already mounted in '$VM_NAME' (skipping mount)"
    return 0
  fi

  echo "[i] Mounting project into VM..."
  set +e
  out="$(multipass mount "$MOUNT_SRC" "$VM_NAME":"$MOUNT_DST" 2>&1)"
  rc=$?
  set -e

  if [[ $rc -ne 0 ]]; then
    if echo "$out" | grep -qi "already mounted"; then
      echo "[i] '${MOUNT_DST}' is already mounted in '$VM_NAME' (multipass said so; continuing)"
    else
      echo "$out" >&2
      exit $rc
    fi
  fi
}

main() {
  ensure_vm_created
  ensure_vm_running
  ensure_wg_tools
  ensure_mount

  echo
  multipass info "$VM_NAME"
  echo
  echo "Connect:"
  echo "  multipass shell $VM_NAME"
  echo "or:"
  echo "  multipass exec $VM_NAME -- bash"
  echo
  echo "Then inside VM run:"
  echo "  cd ${MOUNT_DST}"
  echo "  ./vm/wg-init.sh"
  echo "  sudo bash vm/provision.sh"
}

main "$@"
