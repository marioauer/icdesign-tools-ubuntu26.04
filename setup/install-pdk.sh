#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename -- "${BASH_SOURCE[0]}")"
source "${SCRIPT_DIR}/config.sh"

PDK_FAMILY="${PDK_FAMILY:-ihp-sg13g2}"
PDK_VERSION="${PDK_VERSION:-5cccb161f7492697cfa52eb14dc03beb00bdca9e}"
PDK_ROOT="${PDK_ROOT:-/opt/icdesign/pdks}"
TOOLS_DIR="${TOOLS_DIR:-/opt/icdesign/tools}"
SUDO=()
if (( EUID != 0 )); then
  SUDO=(sudo)
fi

usage() {
  cat <<USAGE
Usage: ${SCRIPT_NAME} [--pdk-root PATH] [--version COMMIT_OR_TAG] [--no-openvaf-compile]

Downloads/enables the ${PDK_FAMILY} PDK with ciel on this machine. The Debian
package does not contain the PDK payload, keeping it small for distribution.

Defaults:
  --pdk-root ${PDK_ROOT}
  --version  ${PDK_VERSION}
USAGE
}

compile_openvaf=1
while (($#)); do
  case "$1" in
    --pdk-root)
      [[ $# -ge 2 ]] || { echo "Missing value for --pdk-root" >&2; usage; exit 2; }
      PDK_ROOT="$2"; shift 2 ;;
    --version)
      [[ $# -ge 2 ]] || { echo "Missing value for --version" >&2; usage; exit 2; }
      PDK_VERSION="$2"; shift 2 ;;
    --no-openvaf-compile) compile_openvaf=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if ! command -v uv >/dev/null 2>&1; then
  echo "${SCRIPT_NAME}: uv is required (run ${SCRIPT_DIR}/setup.sh first)." >&2
  echo "See: https://docs.astral.sh/uv/" >&2
  exit 1
fi

if ! command -v pipx >/dev/null 2>&1; then
  echo "${SCRIPT_NAME}: pipx is required (run ${SCRIPT_DIR}/setup.sh first)." >&2
  exit 1
fi

"${SUDO[@]}" mkdir -p "${PDK_ROOT}"
echo "Enabling ${PDK_FAMILY} PDK ${PDK_VERSION} under ${PDK_ROOT}..."
"${SUDO[@]}" env "PATH=${PATH}" pipx run ciel enable "${PDK_VERSION}" --pdk-family "${PDK_FAMILY}" --pdk-root "${PDK_ROOT}"

if [[ "${compile_openvaf}" = 1 ]]; then
  va_dir="${PDK_ROOT}/${PDK_FAMILY}/libs.tech/verilog-a"
  if [[ -d "${va_dir}" ]]; then
    echo "Compiling Verilog-A models with OpenVAF (safe to rerun; existing outputs may be refreshed)..."
    (cd "${va_dir}" && "${SUDO[@]}" env "PATH=${TOOLS_DIR}/bin:${PATH}" bash -e ./openvaf-compile-va.sh)
  else
    echo "Warning: Verilog-A directory not found: ${va_dir}" >&2
  fi
fi

echo "PDK setup completed successfully."
