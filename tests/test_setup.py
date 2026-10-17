import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "setup"


def environment():
    return {k: v for k, v in os.environ.items()
            if not k.startswith("ICDESIGN_")
            and k not in ("PDK_FAMILY", "PDK_VERSION", "PDK_ROOT", "TOOLS_DIR")}


class SetupTests(unittest.TestCase):
    def test_shell_syntax(self):
        for script in SETUP.glob("*.sh"):
            subprocess.run(["bash", "-n", script], check=True)

    def test_default_download_site(self):
        result = subprocess.check_output(
            ["bash", "-eu", "-c", 'source "$1/config.sh"; printf "%s\\n" "$ICDESIGN_PACKAGES_URL"',
             "test", str(SETUP)], env=environment(), cwd="/tmp", text=True)
        self.assertEqual(result.strip(),
                         "https://marioauer.github.io/icdesign-tools-ubuntu26.04")

    def test_configuration_and_export(self):
        env = environment()
        env.update(PDK_FAMILY="test-family", PDK_VERSION="test-version",
                   ICDESIGN_PACKAGES_URL="https://example.invalid/tools")
        result = subprocess.check_output(
            ["bash", "-eu", "-c",
             'source "$1/config.sh"; bash -c '\
             "'printf \"%s\\n\" \"$PDK_FAMILY\" \"$PDK_VERSION\" \"$ICDESIGN_PACKAGES_URL\"'",
             "test", str(SETUP)], env=env, cwd="/tmp", text=True)
        self.assertEqual(result.splitlines(),
                         ["test-family", "test-version", "https://example.invalid/tools"])

    def test_pdk_defaults_legacy_and_cli(self):
        env = environment()
        result = subprocess.check_output(
            ["bash", SETUP / "install-pdk.sh", "--help"], env=env, cwd="/tmp", text=True)
        self.assertIn("Usage: install-pdk.sh", result)
        self.assertIn("ihp-sg13g2", result)
        env["ICDESIGN_IHP_SG13G2_PDK_VERSION"] = "legacy-version"
        result = subprocess.check_output(
            ["bash", SETUP / "install-pdk.sh", "--help"], env=env, text=True)
        self.assertIn("--version  legacy-version", result)
        env["PDK_VERSION"] = "canonical-version"
        result = subprocess.check_output(
            ["bash", SETUP / "install-pdk.sh", "--version", "cli-version", "--help"],
            env=env, text=True)
        self.assertIn("--version  cli-version", result)
        result = subprocess.check_output(
            ["bash", SETUP / "install-pdk.sh", "--help"], env=env, text=True)
        self.assertIn("--version  canonical-version", result)

    def test_pdk_uses_uv_without_pipx(self):
        for script in ("install-pdk.sh", "setup.sh"):
            self.assertNotIn("pipx", (SETUP / script).read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            mocks = {
                "uv": '#!/bin/bash\nprintf "%s\\n" "$@" > "$LOG"\n',
                "sudo": '#!/bin/bash\nexec "$@"\n',
                "pipx": '#!/bin/bash\nexit 99\n',
            }
            for name, content in mocks.items():
                path = bin_dir / name
                path.write_text(content)
                path.chmod(0o755)
            log = root / "uv-args"
            pdk_root = root / "PDKs with spaces"
            env = environment()
            env.update(PATH=f"{bin_dir}:{env['PATH']}", LOG=str(log),
                       PDK_FAMILY="test-family")
            subprocess.run(["bash", SETUP / "install-pdk.sh", "--pdk-root", str(pdk_root),
                            "--version", "test-version", "--no-openvaf-compile"],
                           env=env, cwd="/tmp", capture_output=True, text=True, check=True)
            self.assertTrue(pdk_root.is_dir())
            self.assertEqual(log.read_text().splitlines(),
                             ["tool", "run", "ciel", "enable", "test-version",
                              "--pdk-family", "test-family", "--pdk-root", str(pdk_root)])

    def test_manifest_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            # No network or system installation: intercept curl, sudo and apt.
            mocks = {
                "curl": '#!/bin/bash\nprintf "%s\\n" "$2" >> "$LOG"\n'
                        'if [[ "$2" == */manifest.json ]]; then\n'
                        '  cp "$MANIFEST" "$4"\nelse\n  touch "$4"\nfi\n',
                "sudo": '#!/bin/bash\nexec "$@"\n',
                "apt-get": '#!/bin/bash\necho apt >> "$LOG"\n',
            }
            for name, content in mocks.items():
                path = bin_dir / name
                path.write_text(content)
                path.chmod(0o755)
            manifest = root / "manifest.json"
            log = root / "log"
            env = environment()
            env.update(PATH=f"{bin_dir}:{env['PATH']}", MANIFEST=str(manifest),
                       LOG=str(log), ICDESIGN_PACKAGES_URL="https://example.invalid/custom/")
            for entries, valid in (
                ({"future-tool": "icdesign-future-tool_1.0_amd64.deb"}, True),
                ({"future+tool": "icdesign-future+tool_1.0_amd64.deb"}, True),
                ({"good": "icdesign-good_1_amd64.deb", "../bad": "bad.deb"}, False),
                ({"tool": "icdesign-other_1_amd64.deb"}, False),
                ({"tool": "../icdesign-tool_1_amd64.deb"}, False),
                ({}, False),
            ):
                with self.subTest(entries=entries):
                    manifest.write_text(json.dumps(entries))
                    log.write_text("")
                    result = subprocess.run(["bash", SETUP / "install-icd-tools.sh"],
                                            env=env, capture_output=True, text=True)
                    self.assertEqual(result.returncode == 0, valid, result.stderr)
                    lines = log.read_text().splitlines()
                    self.assertEqual(lines[0], "https://example.invalid/custom/manifest.json")
                    if valid:
                        self.assertIn("apt", lines)
                    else:
                        self.assertEqual(len(lines), 1)


if __name__ == "__main__":
    unittest.main()
