#!/usr/bin/env bash
set -euo pipefail

VM_NAME="${VM_NAME:-vpnlab}"
CPU="${CPU:-2}"
MEM="${MEM:-4G}"
DISK="${DISK:-20G}"
UBUNTU="${UBUNTU:-22.04}"

if multipass info "$VM_NAME" >/dev/null 2>&1; then
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

echo "[i] Mounting project into VM..."
multipass mount "$(pwd)" "$VM_NAME":/home/ubuntu/project

echo
multipass info "$VM_NAME"
echo
echo "Connect:"
echo "  multipass shell $VM_NAME"
echo "or:"
echo "  multipass exec $VM_NAME -- bash"
echo
echo "Then inside VM run:"
echo "  cd /home/ubuntu/project"
echo "  sudo bash vm/provision.sh"
