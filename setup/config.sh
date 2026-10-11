#!/usr/bin/env bash
# Shared configuration for setup entry points. Source only trusted shell files.
load_setup_config() {
  local config_dir key
  local -a keys=(PDK_FAMILY PDK_VERSION PDK_ROOT TOOLS_DIR ICDESIGN_PACKAGES_URL)
  local -A overrides=()
  config_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

  # Keep the old exported variable names working; canonical names take priority.
  if [[ ! -v PDK_FAMILY && -v ICDESIGN_IHP_SG13G2_PDK_FAMILY ]]; then
    PDK_FAMILY="$ICDESIGN_IHP_SG13G2_PDK_FAMILY"
  fi
  if [[ ! -v PDK_VERSION && -v ICDESIGN_IHP_SG13G2_PDK_VERSION ]]; then
    PDK_VERSION="$ICDESIGN_IHP_SG13G2_PDK_VERSION"
  fi
  if [[ ! -v PDK_ROOT && -v ICDESIGN_PDK_ROOT ]]; then
    PDK_ROOT="$ICDESIGN_PDK_ROOT"
  fi
  if [[ ! -v TOOLS_DIR && -v ICDESIGN_TOOLS_DIR ]]; then
    TOOLS_DIR="$ICDESIGN_TOOLS_DIR"
  fi
  for key in "${keys[@]}"; do
    if [[ -v $key ]]; then overrides[$key]="${!key}"; fi
  done
  if [[ -f "$config_dir/.env" ]]; then
    source "$config_dir/.env"
  fi
  for key in "${keys[@]}"; do
    if [[ -v overrides[$key] ]]; then
      printf -v "$key" '%s' "${overrides[$key]}"
    fi
    # Export settings so setup.sh's child installers inherit the same overrides.
    if [[ -v $key ]]; then export "$key"; fi
  done
}
load_setup_config
unset -f load_setup_config
