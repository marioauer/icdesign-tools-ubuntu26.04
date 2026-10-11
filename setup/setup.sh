#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

SUDO=()
if (( EUID != 0 )); then
  SUDO=(sudo)
fi

install_apt_packages() {
  echo "Updating Ubuntu package lists..."
  "${SUDO[@]}" apt-get update

  echo "Installing basic Ubuntu packages..."
  "${SUDO[@]}" apt-get install -y \
    build-essential \
    ca-certificates \
    curl \
    git \
    mc \
    pipx \
    vim-gtk3
}

install_nodejs() {
  if command -v node >/dev/null 2>&1 && [[ "$(node -p 'process.versions.node.split(`.`)[0]' 2>/dev/null)" == "24" ]]; then
    echo "Node.js 24 is already installed; skipping NodeSource setup."
    return
  fi

  echo "Installing Node.js 24 from NodeSource..."
  if (( EUID == 0 )); then
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
  else
    curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
  fi
  "${SUDO[@]}" apt-get install -y nodejs
}

install_uv() {
  if command -v uv >/dev/null 2>&1; then
    echo "uv is already installed; skipping uv installer."
    return
  fi

  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  echo "If 'uv' is still not found, close and reopen the terminal or add ~/.local/bin to PATH."
}

install_apt_packages
install_nodejs
install_uv
export PATH="${HOME}/.local/bin:${PATH}"

bash "${SCRIPT_DIR}/install-icd-tools.sh"
bash "${SCRIPT_DIR}/install-pdk.sh"

echo "Setup completed successfully."
