# IC design tools — student usage notes

Use this repository to set up an IC design environment on **Ubuntu 26.04**. It installs prebuilt tools and the **IHP SG13G2 process design kit (PDK)**; you do not need to build the tools yourself.

| Tool | Purpose |
| --- | --- |
| Xschem | Draw schematics and generate netlists |
| ngspice | Simulate circuits |
| Xyce | Simulate circuits with the Xyce simulator |
| xschem-gaw | View simulation waveforms with `gaw` |
| OpenVAF | Compile Verilog-A models |
| VACASK | Simulate circuits with Verilog-A models |
| KLayout | View and edit chip layouts; run DRC and LVS |
| Verilator | Compile and simulate Verilog/SystemVerilog as C++ models |
| Icarus Verilog | Compile Verilog/SystemVerilog with `iverilog` and simulate with `vvp` |
| Magic | Edit layouts, check design rules, and extract netlists |
| netgen | Compare extracted and schematic netlists (LVS) |

## 1. Get the repository

Use an Ubuntu 26.04 machine or VM with internet access, permission to use `sudo`, and enough free disk space for the tools and PDK. Xschem, KLayout, and graphical Magic sessions need a graphical desktop.

```sh
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/marioauer/icdesign-tools-ubuntu26.04.git
cd icdesign-tools-ubuntu26.04
```


## 2. Install the environment

From the repository directory, run:

```sh
./setup/setup.sh
```

Run this as your normal user account; the script requests `sudo` when needed. It installs:

- Basic Ubuntu utilities and development packages.
- Node.js 24 and the `uv` Python tool manager.
- IC design packages from the configured download site.
- The pinned IHP SG13G2 PDK, using `ciel`, and compiled Verilog-A models.

Installation can take some time and requires downloads. Wait for **“Setup completed successfully.”** If `uv` is not found afterward, close and reopen your terminal.

### If you only need the tools

```sh
./setup/install-icd-tools.sh
```

This installs every package listed in the published manifest but does not install the PDK or the other setup prerequisites. The download site hosts `.deb` files, not an apt repository.

## 3. Make the tools available in your terminal

All tool package files, including licenses, documentation, desktop launchers and icons, are installed under `/opt/icdesign/tools`; packaging rejects payload outside this prefix. System dependencies still use Ubuntu's standard locations.

Add these lines to your `~/.bashrc` once:

```sh
export PATH="/opt/icdesign/tools/bin:$PATH"
export XDG_DATA_DIRS="/opt/icdesign/tools/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
export PDK_ROOT="/opt/icdesign/pdks"
```

Then reload your shell settings:

```sh
source ~/.bashrc
command -v xschem ngspice Xyce gaw openvaf vacask klayout verilator iverilog vvp magic netgen
```

The command should print a path for each installed tool. Check the simulator and compiler:

```sh
ngspice --version
Xyce -v
openvaf --help
klayout -v
verilator --version
iverilog -V
magic --version
```

## 4. Start working

Keep your coursework in a separate directory, rather than editing the installation scripts:

```sh
mkdir -p ~/icdesign/work
cd ~/icdesign/work
xschem
```

To open an existing schematic, use `xschem circuit.sch`. To simulate an ngspice netlist interactively, use `ngspice circuit.cir`. Replace these paths with your own files. To edit a layout, run `klayout -e layout.gds` (or open an OASIS file).

For Xyce simulation, run `Xyce circuit.cir`. Launch `gaw` from a graphical desktop to view waveforms, or use it as the waveform viewer from Xschem.

For digital simulation, compile with `iverilog -g2012 -o sim.vvp testbench.sv` and run `vvp sim.vvp`, or use `verilator --binary --timing --top-module testbench testbench.sv` and run `./obj_dir/Vtestbench`. Verilator's package installs the C++ compiler, make, Python, and Perl needed to build simulations.

Launch `magic` with the technology/startup configuration supplied by your PDK. For LVS, use `netgen -batch lvs 'layout.spice top' 'schematic.spice top' /path/to/pdk/setup.tcl lvs.log`. Here `top` is the subcircuit name; use your PDK's netgen setup file, not a generic configuration. This is Open Circuit Design's netgen, not Ubuntu's unrelated mesh-generation package.

The default PDK location is:

```text
/opt/icdesign/pdks/ihp-sg13g2
```

## Configuration and updates

All setup scripts read **`setup/.env`**, even when run from another directory. It contains the course defaults for `PDK_FAMILY`, `PDK_VERSION`, `PDK_ROOT`, `TOOLS_DIR`, and `ICDESIGN_PACKAGES_URL`. There should be no need to change those values.

This file is executed as Bash code: use only a trusted copy and do not put secrets in it. The repository-root `.env` is not loaded. Command-line options override exported environment variables, which override `setup/.env` defaults. These settings configure the scripts, not your interactive shell.

To reinstall the PDK or see its options (requires `uv`; Ciel runs through `uv tool run`):

```sh
./setup/install-pdk.sh --help
./setup/install-pdk.sh
```

To install the currently published tool packages again:

```sh
./setup/install-icd-tools.sh
```

Use the download URL provided by your instructor. Switching Git branches does not change the download site unless that branch changes `setup/.env`.

## Troubleshooting

- **`command not found`:** Check the `PATH` settings above and reopen your terminal. Try `/opt/icdesign/tools/bin/xschem` to launch Xschem directly.
- **Xschem cannot open a display:** Run it from a graphical Ubuntu session. Remote sessions need a working graphical display connection.
- **PDK symbols or models are missing:** Check that the PDK installation completed and that your project's Xschem/model configuration points to the installed PDK. Check that the `xschemrc` file for this PDK is present.
- **Downloads fail:** Check your internet connection and `ICDESIGN_PACKAGES_URL`. The site must provide `manifest.json` and the listed packages.
- **Installation fails:** Read the first error in the terminal output. Correct the problem before rerunning the relevant script; do not continue with a partially installed environment.

**Warning:** If Ubuntu asks to install one of these packages (such as `xschem`), decline the installation (say no). Those binaries are not up to date.

## Optional: build packages locally

Most students can skip this section. Local builds require Docker, Python 3, network access, and substantial disk space and time, especially for VACASK and KLayout.

This variant builds inside `ubuntu:26.04` (Resolute), independent of the host OS. Its Docker image tags and download site are separate from the Ubuntu 24.04 variant. GitHub Actions uses an Ubuntu 24.04 host to run Docker; the packages still target Ubuntu 26.04. Do not install these packages on Ubuntu 24.04.

Source pins are retained from the 24.04 variant, including LLVM 18 for OpenVAF's `llvm18` feature and the checksum-verified Boost 1.88 archive for VACASK. Both LLVM 18 build and runtime packages are available in Ubuntu 26.04's repositories.

KLayout 0.30.12 is built from a pinned upstream commit, with Qt5, Ruby, Python and libgit2 support. Its dependency manifest follows [upstream's Ubuntu 26 package](https://www.klayout.de/build.html); versioned shared-library dependencies are also computed from the built binaries and plugins. Binaries are installed in `/opt/icdesign/tools/bin`, libraries and plugins in `/opt/icdesign/tools/lib/klayout`, and a desktop launcher is included.

```sh
python3 scripts/build.py --list                 # packages enabled in build-control.json
make build                                     # build enabled packages into dist/
python3 scripts/build.py --package ngspice --jobs 4
python3 scripts/build.py --package klayout --jobs 4
make all                                       # build all eleven packages
./setup/install-icd-tools.sh --local dist        # install locally built packages
make test                                      # run repository tests
```

Xyce is pinned to commit `16889483` (7.11.0 development sources), with Trilinos 16.1.0 built privately as static libraries using Xyce's recommended CMake cache and Ubuntu's SuiteSparse paths. xschem-gaw is pinned to commit `6b8fa4ab` and built with GTK3; the installed executable is `gaw`. Both packages compute shared-library dependencies from their installed ELF files. Xyce's integration helpers are under `/opt/icdesign/tools/share/xyce`.

`build-control.json` currently enables only `xyce` and `xschem-gaw` for verification. Publishing retains disabled packages from the previous download site.

```sh
python3 scripts/build.py --package xyce --package xschem-gaw --jobs 4
# After installing the packages (no graphical display needed):
bash tests/smoke_xyce_gaw.sh
```

The additional source pins are Verilator 5.052, Icarus Verilog 13.0, Magic 8.3.685, and netgen 1.5.324. Magic and netgen are built with Tcl/Tk support and GNU C17 for compatibility with Ubuntu 26.04's compiler. Shared-library dependencies are computed from all installed ELF executables and modules; runtime scripts and data are included.

For faster verification, temporarily disable existing packages in `build-control.json`, or select only the new packages explicitly:

```sh
python3 scripts/build.py --package verilator --package iverilog --package magic --package netgen --jobs 4
# After installing the packages, run headless simulation, extraction, and LVS checks:
bash tests/smoke_new_tools.sh
```

Package source pins and dependencies are in `packages/<name>/dependencies.json`. You do not need to change them for normal course use.
