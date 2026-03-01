#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="${SRC_DIR:-/home/ubuntu/project}"
APP_DIR="${APP_DIR:-/home/nginx/vpnconhost}"
APP_USER="${APP_USER:-nginx}"
APP_GROUP="${APP_GROUP:-www-data}"
SERVICE_NAME="${SERVICE_NAME:-vpnconhost}"
SOCK_PATH="${SOCK_PATH:-/run/vpnconhost/vpnconhost.sock}"
VENV_DIR="${VENV_DIR:-$APP_DIR/venv}"

ENV_FILE="${ENV_FILE:-$SRC_DIR/.env}"

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "Run as root: sudo bash $0"
    exit 1
  fi
}

install_packages() {
  apt-get update
  apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    build-essential libssl-dev libffi-dev \
    nginx \
    wireguard-tools iproute2 iptables ufw \
    rsync ca-certificates curl
}

load_env() {
  if [[ -f "$ENV_FILE" ]]; then
    # Загружаем .env как bash-совместимый файл (KEY=VALUE). Комментарии допускаются.
    set -a
    # shellcheck disable=SC1090
    source <(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ENV_FILE" || true)
    set +a
    echo "[i] Loaded env from $ENV_FILE"
  else
    echo "[i] No .env found at $ENV_FILE (will use defaults where possible)"
  fi
}

ensure_user() {
  if id -u "$APP_USER" >/dev/null 2>&1; then
    echo "[i] user '$APP_USER' exists"
  else
    useradd -r -m -d /home/nginx -s /usr/sbin/nologin "$APP_USER"
  fi

  echo "$APP_USER ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/$APP_USER"
  chmod 0440 "/etc/sudoers.d/$APP_USER"
}

sync_project() {
  mkdir -p "$APP_DIR"

  # rsync запускаем от root, чтобы он мог удалять/перезаписывать старые файлы деплоя.
  # При этом НЕ сохраняем owner/group/perms с source (на multipass mount они могут быть “не те”).
  rsync -a --delete \
    --no-owner --no-group --no-perms \
    --exclude ".git/" \
    --exclude "__pycache__/" \
    --exclude "*.pyc" \
    --exclude ".venv/" \
    --exclude "venv/" \
    --exclude "vpnconhostenv/" \
    --exclude ".pytest_cache/" \
    --exclude ".mypy_cache/" \
    --exclude ".ruff_cache/" \
    --exclude "logs/app.log" \
    --exclude "*.db" \
    "$SRC_DIR"/ "$APP_DIR"/

  # Приводим ownership к нужному
  chown -R "$APP_USER":"$APP_GROUP" "$APP_DIR"
}



setup_venv_and_deps() {
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel

  if [[ -f "$APP_DIR/requirements.txt" ]]; then
    "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
  fi

  "$VENV_DIR/bin/pip" install gunicorn
}

write_gunicorn_service() {
  # Убедимся, что конфиг реально есть в APP_DIR (он должен приехать rsync'ом из проекта)
  if [[ ! -f "${APP_DIR}/gunicorn.conf.py" ]]; then
    echo "[!] ${APP_DIR}/gunicorn.conf.py not found. Add it to your project root."
    exit 1
  fi

  cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=Gunicorn instance to serve ${SERVICE_NAME}
After=network.target

[Service]
User=${APP_USER}
Group=${APP_GROUP}
WorkingDirectory=${APP_DIR}
Environment="PATH=${VENV_DIR}/bin"

# Важно: подхватываем .env из проекта (из APP_DIR, уже после rsync)
EnvironmentFile=-${APP_DIR}/.env
Environment="GUNICORN_BIND=unix:${SOCK_PATH}"

# Создаёт /run/vpnconhost и держит его в нужных правах
RuntimeDirectory=vpnconhost
+RuntimeDirectoryMode=0755

# Чтобы сокет создавался 660 (rw для owner+group)
UMask=0007
 
ExecStart=${VENV_DIR}/bin/gunicorn -c ${APP_DIR}/gunicorn.conf.py wsgi:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF


  systemctl daemon-reload
  systemctl enable "${SERVICE_NAME}.service"
  systemctl restart "${SERVICE_NAME}.service"
  systemctl status --no-pager "${SERVICE_NAME}.service" || true
}


write_nginx_site() {
  cat > "/etc/nginx/sites-available/${SERVICE_NAME}" <<EOF
server {
    listen 80;
    listen [::]:80;

    location / {
        include proxy_params;
        proxy_pass http://unix:${SOCK_PATH};
    }
}
EOF

  ln -sf "/etc/nginx/sites-available/${SERVICE_NAME}" "/etc/nginx/sites-enabled/${SERVICE_NAME}"
  rm -f /etc/nginx/sites-enabled/default || true

  nginx -t
  systemctl restart nginx
}

enable_forwarding_sysctl() {
  cat > /etc/sysctl.d/99-vpnlab.conf <<EOF
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
EOF
  sysctl --system
}

detect_default_iface() {
  ip route show default 0.0.0.0/0 2>/dev/null | awk '{print $5; exit}'
}

setup_ufw_basic() {
  # Чтобы UFW не отрезал SSH/вход
  ufw --force reset
  ufw default deny incoming
  ufw default allow outgoing

  # SSH (Multipass обычно использует 22)
  ufw allow 22/tcp

  # HTTP (nginx)
  ufw allow 80/tcp

  # WireGuard порт
  local port="${WG_LISTEN_PORT:-51820}"
  ufw allow "${port}/udp"

  # Включаем форвардинг в UFW
  sed -i 's/^DEFAULT_FORWARD_POLICY=.*/DEFAULT_FORWARD_POLICY="ACCEPT"/' /etc/default/ufw || true

  ufw --force enable
}

write_wg0_conf() {
  # Из .env:
  local ext_iface="${WG_EXTERNAL_IFACE:-}"
  local priv_key="${WG_PRIVATE_KEY:-}"
  local addr="${WG_ADDRESS:-10.8.0.1/24}"
  local port="${WG_LISTEN_PORT:-51820}"

  if [[ -z "$ext_iface" ]]; then
    ext_iface="$(detect_default_iface || true)"
  fi

  if [[ -z "$ext_iface" ]]; then
    echo "[!] Cannot determine external interface. Set WG_EXTERNAL_IFACE in .env (e.g. ens3)."
    exit 1
  fi

  if [[ -z "$priv_key" ]]; then
    echo "[!] WG_PRIVATE_KEY is empty. Set WG_PRIVATE_KEY in .env"
    exit 1
  fi

  mkdir -p /etc/wireguard
  chmod 700 /etc/wireguard

  cat > /etc/wireguard/wg0.conf <<EOF
[Interface]
Address = ${addr}
SaveConfig = true
PostUp = ufw route allow in on wg0 out on ${ext_iface}
PostUp = ufw route allow in on wg0 out on wg0
PostUp = iptables -t nat -I POSTROUTING -o ${ext_iface} -j MASQUERADE
PostUp = ip6tables -t nat -I POSTROUTING -o ${ext_iface} -j MASQUERADE
PreDown = ufw route delete allow in on wg0 out on ${ext_iface}
PreDown = ufw route delete allow in on wg0 out on wg0
PreDown = iptables -t nat -D POSTROUTING -o ${ext_iface} -j MASQUERADE
PreDown = ip6tables -t nat -D POSTROUTING -o ${ext_iface} -j MASQUERADE
ListenPort = ${port}
PrivateKey = ${priv_key}
EOF

  chmod 600 /etc/wireguard/wg0.conf
}

start_wireguard() {
  systemctl enable --now wg-quick@wg0
  systemctl restart wg-quick@wg0
  systemctl status --no-pager wg-quick@wg0 || true
}

main() {
  require_root
  install_packages
  load_env

  ensure_user
  enable_forwarding_sysctl

  # App
  sync_project
  setup_venv_and_deps
  write_gunicorn_service
  write_nginx_site

  # WireGuard server
  setup_ufw_basic
  write_wg0_conf
  start_wireguard

  echo
  echo "[OK] Provisioning finished."
  echo "App:      systemctl status ${SERVICE_NAME}"
  echo "Nginx:    systemctl status nginx"
  echo "WG:       systemctl status wg-quick@wg0"
  echo "WG show:  wg show"
  echo "Config:   /etc/wireguard/wg0.conf"
}

main "$@"
