import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build", ROOT / "scripts/build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class BuildTests(unittest.TestCase):
    def test_selection(self):
        control = dict.fromkeys(build.PACKAGES, True)
        control["vacask"] = False
        self.assertEqual(build.select(control), [p for p in build.PACKAGES if p != "vacask"])
        self.assertEqual(build.select(control, ("vacask",)), ["vacask"])
        self.assertEqual(build.select(control, all_packages=True), list(build.PACKAGES))
        with self.assertRaises(ValueError):
            build.select({"ngspice": True})

    def test_build_dependency_union(self):
        deps = build.build_dependencies(("ngspice",))
        self.assertIn("git", deps)
        self.assertIn("libedit-dev", deps)
        self.assertNotIn("llvm-18-dev", deps)
        self.assertNotIn("cmake", deps)
        union = build.build_dependencies(("openvaf", "vacask"))
        self.assertEqual(union.count("llvm-18-dev"), 1)
        self.assertEqual(union, build.build_dependencies(("vacask", "openvaf")))
        self.assertEqual(build.build_dependencies(()),
                         sorted(build.load(ROOT / "shared/build-dependencies.json")["common"]))

    def test_ubuntu_target_and_image_tags(self):
        self.assertIn("FROM ubuntu:26.04 AS base",
                      (ROOT / "shared/Dockerfile").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            commands = []

            def fake_run(*args):
                commands.append(args)
                if args[:2] == ("docker", "cp"):
                    package = args[2].split(":", 1)[0]
                    (Path(args[3]) / f"icdesign-{package}_1_amd64.deb").write_bytes(b"test")

            argv = ["build.py", "--all", "--out", tmp]
            with patch.object(sys, "argv", argv), patch.object(build, "run", side_effect=fake_run), \
                    patch.object(build.subprocess, "check_output",
                                 side_effect=lambda args, **kwargs: args[-1].split(":")[-1]):
                build.main()
            images = [cmd[cmd.index("-t") + 1] for cmd in commands if cmd[:2] == ("docker", "build")]
            self.assertEqual(images, [f"icdesign-build-ubuntu26.04:{tag}"
                                      for tag in ("base", "rust", *build.PACKAGES)])
            for package in build.PACKAGES:
                tag = "rust" if package in ("openvaf", "vacask") else "base"
                self.assertIn(f"ARG BASE_IMAGE=icdesign-build-ubuntu26.04:{tag}",
                              (ROOT / "packages" / package / "Dockerfile").read_text())
                self.assertEqual(len(list(Path(tmp).glob(f"icdesign-{package}_*.deb"))), 1)

    def test_ubuntu_runtime_dependencies(self):
        deps = build.runtime_dependencies("ngspice").split(", ")
        self.assertIn("libxt6t64", deps)
        self.assertNotIn("libxt6", deps)
        for package in ("ngspice", "xschem"):
            self.assertIn("libreadline8t64", build.runtime_dependencies(package).split(", "))

    def test_klayout_manifest(self):
        deps = build.build_dependencies(("klayout",))
        for dep in ("qtbase5-dev", "qttools5-dev", "qtmultimedia5-dev",
                    "libqt5xmlpatterns5-dev", "libqt5svg5-dev", "libqt5opengl5-dev",
                    "ruby-dev", "python3-dev", "libgit2-dev", "zlib1g-dev"):
            self.assertIn(dep, deps)
        self.assertNotIn("llvm-18-dev", deps)
        runtime = build.runtime_dependencies("klayout").split(", ")
        for dep in ("libqt5core5t64", "libqt5gui5t64", "libgit2-1.9", "libruby3.3",
                    "libpython3.14", "python3"):
            self.assertIn(dep, runtime)
        self.assertIn("KLAYOUT_COMMIT=e71272c3b178105bd2a2f25af54673a7af7ed60d",
                      build.source_build_args("klayout"))

    def test_digital_and_layout_manifests(self):
        expected = {
            "verilator": ("autoconf", "flex", "bison", "help2man", "liblz4-dev"),
            "iverilog": ("autoconf", "flex", "bison", "gperf", "libreadline-dev"),
            "magic": ("tcl-dev", "tk-dev", "libcairo2-dev", "libgl-dev", "zlib1g-dev"),
            "netgen": ("tcl-dev", "tk-dev", "libx11-dev"),
        }
        for package, dependencies in expected.items():
            with self.subTest(package=package):
                deps = build.build_dependencies((package,))
                self.assertTrue(set(dependencies).issubset(deps))
                self.assertNotIn("llvm-18-dev", deps)
                self.assertNotIn("qtbase5-dev", deps)
        self.assertTrue({"perl", "make", "g++"}.issubset(
            build.runtime_dependencies("verilator").split(", ")))
        self.assertIn("RTimothyEdwards/netgen.git", build.load(
            ROOT / "packages/netgen/dependencies.json")["sources"]["netgen"]["url"])

    def test_xyce_and_gaw_manifests(self):
        self.assertTrue({"cmake", "gfortran", "libfl-dev", "libsuitesparse-dev",
                         "libblas-dev", "liblapack-dev", "libfftw3-dev"}.issubset(
            build.build_dependencies(("xyce",))))
        self.assertTrue({"autopoint", "gettext", "libgtk-3-dev"}.issubset(
            build.build_dependencies(("xschem-gaw",))))
        self.assertIn("libgtk-3-0t64", build.runtime_dependencies("xschem-gaw").split(", "))
        self.assertIn("TRILINOS_COMMIT=11a16481fa1af48e3cfdb0aa84c29617ce94479f",
                      build.source_build_args("xyce"))
        self.assertIn("GAW_COMMIT=6b8fa4ab007e88b3129381e0479737ae014a8b51",
                      build.source_build_args("xschem-gaw"))
        control = {p: p in ("xyce", "xschem-gaw") for p in build.PACKAGES}
        self.assertEqual(build.select(control), ["xyce", "xschem-gaw"])
        for package in ("xyce", "xschem-gaw"):
            dockerfile = (ROOT / "packages" / package / "Dockerfile").read_text()
            self.assertIn("dpkg-shlibdeps", dockerfile)
            self.assertIn("--root-owner-group", dockerfile)
        xyce = (ROOT / "packages/xyce/Dockerfile").read_text()
        self.assertIn("-D BUILD_SHARED_LIBS=OFF", xyce)
        self.assertIn("-D TPL_AMD_INCLUDE_DIRS=/usr/include/suitesparse", xyce)

    def test_smoke_script_syntax(self):
        for name in ("smoke_new_tools.sh", "smoke_xyce_gaw.sh"):
            subprocess.run(["bash", "-n", ROOT / "tests" / name], check=True)

    def test_new_packages_only_selection(self):
        new = ("verilator", "iverilog", "magic", "netgen")
        control = {p: p in new for p in build.PACKAGES}
        self.assertEqual(build.select(control), list(new))
        self.assertEqual(build.select(control, all_packages=True), list(build.PACKAGES))

    def test_invalid_build_dependencies(self):
        for invalid in ("git", ["git; echo bad"], [123], [[]]):
            with self.subTest(invalid=invalid), patch.object(build, "load", return_value={"common": invalid}):
                with self.assertRaises(ValueError):
                    build.build_dependencies(())
        with patch.object(build, "load", side_effect=[{"common": ["git"]}, {"runtime": [], "sources": {}}]):
            with self.assertRaises(ValueError):
                build.build_dependencies(("ngspice",))

    def test_list_build_dependencies(self):
        for options, packages in ((["--all"], build.PACKAGES), (["--package", "ngspice"], ("ngspice",)),
                                  (["--package", "klayout"], ("klayout",))):
            result = subprocess.check_output(
                [sys.executable, ROOT / "scripts/build.py", "--list-build-deps", *options], text=True)
            self.assertEqual(result.splitlines(), build.build_dependencies(packages))

    def test_manifests(self):
        self.assertIn("libclang-18-dev", build.build_dependencies())
        for package in build.PACKAGES:
            self.assertTrue(build.runtime_dependencies(package))
            args = build.source_build_args(package)
            self.assertIn("--build-arg", args)
            self.assertTrue(any("_COMMIT=" in arg for arg in args))
        self.assertIn("BOOST_SHA256=3621533e820dcab1e8012afd583c0c73cf0f77694952b81352bf38c1488f9cb4",
                      build.source_build_args("vacask"))
        openvaf = build.load(ROOT / "packages/openvaf/dependencies.json")["sources"]["openvaf"]
        vacask = build.load(ROOT / "packages/vacask/dependencies.json")["sources"]["openvaf"]
        self.assertEqual(openvaf, vacask)
        result = subprocess.check_output([sys.executable, ROOT / "scripts/build.py", "--list"], text=True)
        self.assertEqual(result.splitlines(), build.select(build.load(ROOT / "build-control.json")))

    def test_retains_disabled_from_previous_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            previous = root / "previous"
            previous.mkdir()
            old_name = "icdesign-vacask_0.3.4-2_amd64.deb"
            (previous / old_name).write_bytes(b"old")
            (previous / "manifest.json").write_text(json.dumps({"vacask": old_name}))
            dist = root / "dist"
            dist.mkdir()
            new_name = "icdesign-ngspice_47-1_amd64.deb"
            (dist / new_name).write_bytes(b"new")
            site = root / "site"
            subprocess.run([sys.executable, ROOT / "scripts/prepare_site.py", "--dist", dist,
                            "--site", site, "--previous-url", previous.as_uri()], check=True)
            self.assertEqual(json.loads((site / "manifest.json").read_text()),
                             {"ngspice": new_name, "vacask": old_name})
            self.assertEqual((site / old_name).read_bytes(), b"old")

    def test_site_from_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / "dist"
            site = Path(tmp) / "site"
            dist.mkdir()
            (dist / "icdesign-ngspice_47-1_amd64.deb").write_bytes(b"test")
            (dist / "icdesign-klayout_0.30.12-1_amd64.deb").write_bytes(b"klayout")
            new_files = {p: f"icdesign-{p}_1_amd64.deb"
                         for p in ("verilator", "iverilog", "magic", "netgen", "xyce", "xschem-gaw")}
            for package, name in new_files.items():
                (dist / name).write_bytes(package.encode())
            subprocess.run([sys.executable, ROOT / "scripts/prepare_site.py", "--dist", dist, "--site", site], check=True)
            self.assertEqual(json.loads((site / "manifest.json").read_text()),
                             {"ngspice": "icdesign-ngspice_47-1_amd64.deb",
                              "klayout": "icdesign-klayout_0.30.12-1_amd64.deb",
                              **new_files})
            self.assertTrue((site / "icdesign-ngspice_47-1_amd64.deb").exists())
            self.assertEqual((site / "icdesign-klayout_0.30.12-1_amd64.deb").read_bytes(), b"klayout")
            self.assertIn("klayout</a>", (site / "index.html").read_text())
            for package, name in new_files.items():
                self.assertEqual((site / name).read_bytes(), package.encode())
                self.assertIn(f"{package}</a>", (site / "index.html").read_text())
            self.assertIn("Ubuntu 26.04", (site / "index.html").read_text())


if __name__ == "__main__":
    unittest.main()
