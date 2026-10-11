#!/usr/bin/env python3
"""Build selected Debian packages with a shared Ubuntu 26.04 Docker image."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("ngspice", "openvaf", "vacask", "xschem", "klayout",
            "verilator", "iverilog", "magic", "netgen", "xyce", "xschem-gaw")
APT_NAME = re.compile(r"[a-z0-9][a-z0-9+.-]*\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SOURCE_NAMES = {"ngspice": ("ngspice",), "openvaf": ("openvaf",),
                "vacask": ("vacask", "openvaf", "boost"), "xschem": ("xschem",),
                "klayout": ("klayout",), "verilator": ("verilator",),
                "iverilog": ("iverilog",), "magic": ("magic",), "netgen": ("netgen",),
                "xyce": ("xyce", "trilinos"), "xschem-gaw": ("gaw",)}


def load(path):
    with path.open() as f:
        return json.load(f)


def select(control, requested=(), all_packages=False):
    if set(control) != set(PACKAGES) or any(type(v) is not bool for v in control.values()):
        raise ValueError("build-control.json must contain one boolean for every package")
    if requested:
        return list(dict.fromkeys(requested))
    return [p for p in PACKAGES if all_packages or control[p]]


def build_dependencies(packages=PACKAGES):
    data = load(ROOT / "shared/build-dependencies.json")
    if not isinstance(data, dict) or set(data) != {"common"}:
        raise ValueError("shared/build-dependencies.json must contain only common dependencies")
    groups = [data["common"]]
    for package in packages:
        if package not in PACKAGES:
            raise ValueError(f"unknown package: {package}")
        manifest = load(ROOT / "packages" / package / "dependencies.json")
        if not isinstance(manifest, dict) or set(manifest) != {"build", "runtime", "sources"}:
            raise ValueError(f"invalid dependency manifest for {package}")
        groups.append(manifest["build"])
    for group in groups:
        if not isinstance(group, list) or any(
            not isinstance(dep, str) or not APT_NAME.fullmatch(dep) for dep in group
        ):
            raise ValueError("invalid build dependency list")
    return sorted({dep for group in groups for dep in group})


def runtime_dependencies(package):
    data = load(ROOT / "packages" / package / "dependencies.json")
    deps = data["runtime"]
    if set(data) != {"build", "runtime", "sources"} or not isinstance(deps, list) or not deps or any(
        not isinstance(d, str) or not d or "\n" in d or "\r" in d for d in deps
    ):
        raise ValueError(f"invalid runtime dependencies for {package}")
    return ", ".join(deps)


def source_build_args(package):
    sources = load(ROOT / "packages" / package / "dependencies.json")["sources"]
    if not isinstance(sources, dict) or set(sources) != set(SOURCE_NAMES[package]):
        raise ValueError(f"invalid sources for {package}")
    args = []
    for name, info in sources.items():
        if name == "boost":
            if (set(info) != {"version", "sha256"} or
                not re.fullmatch(r"[0-9]+(?:\.[0-9]+){2}", info["version"]) or
                not SHA256.fullmatch(info["sha256"])):
                raise ValueError("invalid Boost pin")
            values = {"BOOST_VERSION": info["version"], "BOOST_SHA256": info["sha256"]}
        else:
            if set(info) != {"url", "ref", "commit"} or not SHA.fullmatch(info["commit"]):
                raise ValueError(f"invalid {name} commit pin")
            url = urlsplit(info["url"])
            if url.scheme != "https" or not url.hostname or url.username or url.password or not url.path:
                raise ValueError(f"invalid {name} source URL")
            if not isinstance(info["ref"], str) or not info["ref"].strip():
                raise ValueError(f"invalid {name} reference")
            values = {f"{name.upper()}_REPO": info["url"], f"{name.upper()}_COMMIT": info["commit"]}
        for key, value in values.items():
            args.extend(("--build-arg", f"{key}={value}"))
    return args


def run(*args):
    print("+", " ".join(str(a) for a in args), flush=True)
    subprocess.run(args, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", choices=PACKAGES, action="append", default=[], help="build explicitly (ignores control file)")
    parser.add_argument("--all", action="store_true", help="build all packages")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--list", action="store_true", help="print selected packages without Docker")
    output.add_argument("--list-build-deps", action="store_true", help="print common + selected package build dependencies without Docker")
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--maintainer", default="icdesign build <noreply@example.invalid>")
    args = parser.parse_args()
    if args.jobs < 1 or "\n" in args.maintainer or "\r" in args.maintainer:
        parser.error("invalid jobs or maintainer")
    if args.all and args.package:
        parser.error("--all and --package are mutually exclusive")
    selected = select(load(ROOT / "build-control.json"), args.package, args.all)
    if args.list:
        print("\n".join(selected))
        return
    if args.list_build_deps:
        print("\n".join(build_dependencies(selected)))
        return
    if not selected:
        print("Nothing selected; edit build-control.json or pass --package/--all")
        return
    deps = build_dependencies(selected)
    runtime = {p: runtime_dependencies(p) for p in selected}
    sources = {p: source_build_args(p) for p in selected}
    # VACASK compiles against OpenVAF; don't silently mix different sources.
    if "vacask" in selected:
        openvaf = load(ROOT / "packages/openvaf/dependencies.json")["sources"]["openvaf"]
        vacask_openvaf = load(ROOT / "packages/vacask/dependencies.json")["sources"]["openvaf"]
        if openvaf != vacask_openvaf:
            raise ValueError("VACASK and OpenVAF pins must match")
    base = "icdesign-build-ubuntu26.04:base"
    rust = "icdesign-build-ubuntu26.04:rust"
    run("docker", "build", "-f", str(ROOT / "shared/Dockerfile"), "--target", "base",
        "--build-arg", "BUILD_DEPS=" + " ".join(deps), "-t", base, str(ROOT / "shared"))
    if any(p in ("openvaf", "vacask") for p in selected):
        run("docker", "build", "-f", str(ROOT / "shared/Dockerfile"), "--target", "rust",
            "--build-arg", "BUILD_DEPS=" + " ".join(deps), "-t", rust, str(ROOT / "shared"))
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    for p in selected:
        image = f"icdesign-build-ubuntu26.04:{p}"
        run("docker", "build", "--build-arg", f"BASE_IMAGE={rust if p in ('openvaf', 'vacask') else base}",
            "--build-arg", f"JOBS={args.jobs}", "--build-arg", f"MAINTAINER={args.maintainer}",
            "--build-arg", f"RUNTIME_DEPS={runtime[p]}", *sources[p],
            "-t", image, str(ROOT / "packages" / p))
        cid = subprocess.check_output(["docker", "create", image], text=True).strip()
        try:
            with tempfile.TemporaryDirectory(dir=out) as tmp:
                run("docker", "cp", cid + ":/out/.", tmp)
                files = list(Path(tmp).glob(f"icdesign-{p}_*.deb"))
                if len(files) != 1 or len(list(Path(tmp).iterdir())) != 1:
                    raise RuntimeError(f"expected exactly one .deb from {p}")
                for old in out.glob(f"icdesign-{p}_*.deb"):
                    old.unlink()
                os.replace(files[0], out / files[0].name)
                print(f"Wrote {out / files[0].name}")
        finally:
            run("docker", "rm", "-f", cid)


if __name__ == "__main__":
    main()
