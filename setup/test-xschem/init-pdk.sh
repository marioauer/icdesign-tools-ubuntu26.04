#!/usr/bin/env bash
#------------------------------------------------------------------------------
# Set environment variables to run xschem with IHP SG13G2.
# Source this file, do not execute it:
#   source test-xschem/init-pdk.sh
#------------------------------------------------------------------------------

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "Error: this script must be sourced so the environment variables remain active." >&2
  echo "Run: source $0" >&2
  exit 1
fi

add_path_once() {
  local dir=$1
  if [[ -n "$dir" && -d "$dir" && ":$PATH:" != *":$dir:"* ]]; then
    export PATH="$dir:$PATH"
    echo "Added $dir to PATH"
  fi
}

export PDK_ROOT=/opt/icdesign/pdks
export PDK=ihp-sg13g2
export SPICE_USERINIT_DIR="$PDK_ROOT/$PDK/libs.tech/ngspice"

add_path_once /opt/icdesign/tools/bin

echo "Using PDK: ${PDK_ROOT}/${PDK}"

REAL_PATH=$(readlink -f "${BASH_SOURCE[0]}")
SCRIPT_DIR=$(dirname "$REAL_PATH")

if [[ -n "$SCRIPT_DIR" && "$SCRIPT_DIR" != "." ]]; then
  add_path_once "$SCRIPT_DIR"
else
  echo "Error: Could not determine SCRIPT_DIR" >&2
  return 1
fi
