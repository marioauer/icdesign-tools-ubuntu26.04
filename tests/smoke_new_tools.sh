#!/usr/bin/env bash
# Run after installing the four new packages (no PDK or graphical display needed).
set -euo pipefail
export PATH="/opt/icdesign/tools/bin:${PATH}"
work="$(mktemp -d)"
cleanup() {
  status=$?
  if (( status != 0 )); then
    for log in "$work"/*.log; do
      [[ -f "$log" ]] || continue
      printf '\n--- %s ---\n' "$log"
      tail -60 "$log"
    done
  fi
  rm -rf "$work"
}
trap cleanup EXIT
cd "$work"

verilator --version
iverilog -V
magic --version

cat > tb.sv <<'EOF'
module tb;
  logic a = 0;
  wire y = ~a;
  initial begin
    #1;
    if (y !== 1) $fatal(1, "inverter failed");
    a = 1;
    #1;
    if (y !== 0) $fatal(1, "inverter failed");
    $display("HDL_SMOKE_PASS");
    $finish;
  end
endmodule
EOF
iverilog -g2012 -s tb -o tb.vvp tb.sv
vvp tb.vvp | tee iverilog.log
grep -q HDL_SMOKE_PASS iverilog.log
verilator --binary --timing --top-module tb -j 2 tb.sv > verilator-build.log 2>&1
./obj_dir/Vtb | tee verilator.log
grep -q HDL_SMOKE_PASS verilator.log

cat > magic-smoke.tcl <<'EOF'
load smoke
box 0 0 10 10
paint metal1
save smoke
extract all
ext2spice lvs
ext2spice
quit -noprompt
EOF
magic -T scmos -dnull -noconsole magic-smoke.tcl > magic.log 2>&1
test -s smoke.mag
test -s smoke.ext
test -s smoke.spice

cat > one.spice <<'EOF'
.subckt top a b
R1 a b 100
.ends top
EOF
cp one.spice two.spice
netgen -batch lvs 'one.spice top' 'two.spice top' /dev/null lvs.log > netgen.log 2>&1
grep -q 'Circuits match uniquely' lvs.log
printf 'Verilator, Icarus Verilog, Magic extraction and netgen LVS smoke tests passed.\n'
