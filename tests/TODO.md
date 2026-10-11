# Test coverage TODO

`make test` runs repository unit tests; it does not run installed-tool integration tests. `smoke_new_tools.sh` covers only Verilator, Icarus Verilog, Magic, and netgen. Previous manual installation/version checks and KLayout scripting checks are not part of the repeatable suite.

## Functional coverage for all nine tools

- [ ] ngspice: simulate a small circuit in batch mode and assert numerical results.
- [ ] Xschem: load a schematic and generate a netlist; check connectivity and model references.
- [ ] OpenVAF: compile a minimal Verilog-A model and verify the generated OSDI module.
- [ ] VACASK: simulate a circuit using a compiled Verilog-A model and assert numerical results.
- [ ] KLayout: create, write, and reload GDS/OASIS layouts; assert geometry and exercise Python/Ruby scripting.
- [ ] Verilator: extend the existing simulation smoke test with failure cases and broader SystemVerilog coverage.
- [ ] Icarus Verilog: extend the existing simulation smoke test with failure cases and VPI loading.
- [ ] Magic: assert extracted netlist contents, not just file existence; test known DRC violations.
- [ ] netgen: test both matching and mismatched netlists, asserting comparison results.

## Repeatable integration testing

- [ ] Add a separate integration-test target without making unit tests depend on installed tools.
- [ ] Install all built packages together in a clean Ubuntu 26.04 container and run every tool's functional tests.
- [ ] Check shared-library resolution, installed scripts, plugins, and runtime data.
- [ ] Run the integration suite in CI after building packages; retain failure logs and generated artifacts.
- [ ] Test graphical startup for Xschem, KLayout, and Magic using a virtual display.
- [ ] Add pinned IHP SG13G2 PDK integration tests spanning schematic netlisting, model compilation, simulation, extraction, DRC, and LVS.
