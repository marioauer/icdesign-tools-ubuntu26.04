#!/usr/bin/env bash
# Run after installing Xyce and xschem-gaw; no PDK or display required.
set -euo pipefail
export PATH="/opt/icdesign/tools/bin:${PATH}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cd "$work"
Xyce -v
cat > divider.cir <<'EOF'
Resistor divider smoke test
V1 in 0 DC 1
R1 in out 1k
R2 out 0 1k
.DC V1 1 1 1
.PRINT DC V(out)
.END
EOF
Xyce divider.cir > xyce.log 2>&1 || { cat xyce.log; exit 1; }
python3 - <<'PY'
from pathlib import Path
rows = [line.split() for line in Path('divider.cir.prn').read_text().splitlines()]
values = [float(row[-1]) for row in rows if row and row[0].isdigit()]
assert values and all(abs(v - 0.5) < 1e-9 for v in values), values
PY
# Upstream's help exits with status 1, before GTK tries to open a display.
status=0
gaw -h > gaw.log 2>&1 || status=$?
[[ "$status" == 1 ]]
grep -q 'Usage: gaw' gaw.log
printf 'Xyce divider simulation and GAW headless help smoke tests passed.\n'
