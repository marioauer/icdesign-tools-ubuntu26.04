#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

# Override for forks: https://<owner>.github.io/<repository>
BASE_URL="${ICDESIGN_PACKAGES_URL:-https://marioauer.github.io/icdesign-tools-ubuntu26.04}"
LOCAL_DIR=""
if [[ ${1:-} == --local && $# == 2 ]]; then
  LOCAL_DIR="$2"
elif (($#)); then
  echo "Usage: $0 [--local DIRECTORY]" >&2
  exit 2
fi
SUDO=()
if (( EUID != 0 )); then SUDO=(sudo); fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
chmod 755 "$tmp" # apt's sandbox user must be able to read the downloads

if [[ -n "$LOCAL_DIR" ]]; then
  shopt -s nullglob
  files=("$LOCAL_DIR"/icdesign-*.deb)
  ((${#files[@]})) || { echo "No packages in $LOCAL_DIR" >&2; exit 1; }
  cp -- "${files[@]}" "$tmp/"
else
  curl -fsSL "${BASE_URL%/}/manifest.json" -o "$tmp/manifest.json"
  # Validate remote filenames before interpreting them as paths or URLs.
  python3 - "$tmp/manifest.json" > "$tmp/names" <<'PY'
import json, re, sys
with open(sys.argv[1]) as f:
    manifest = json.load(f)
if not isinstance(manifest, dict) or not manifest:
    sys.exit('Empty or invalid package manifest')
for tool, name in manifest.items():
    if not re.fullmatch(r'[a-z0-9][a-z0-9+-]*', tool) or not isinstance(name, str) or not re.fullmatch(r'icdesign-' + re.escape(tool) + r'_[A-Za-z0-9.+:~_-]+_[A-Za-z0-9_-]+\.deb', name):
        sys.exit('Invalid package manifest entry')
for name in manifest.values():
    print(name)
PY
  mapfile -t names < "$tmp/names"
  ((${#names[@]})) || { echo 'No packages in manifest' >&2; exit 1; }
  for name in "${names[@]}"; do
    curl -fsSL "${BASE_URL%/}/$name" -o "$tmp/$name"
  done
fi
shopt -s nullglob
files=("$tmp"/*.deb)
((${#files[@]})) || { echo 'No packages downloaded' >&2; exit 1; }
"${SUDO[@]}" apt-get install -y "${files[@]}"
