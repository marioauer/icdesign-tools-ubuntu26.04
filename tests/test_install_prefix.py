from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'shared/check-install-prefix'
PREFIX = '/opt/icdesign/tools'


class InstallPrefixTests(unittest.TestCase):
    def check_stage(self, root, prefix=PREFIX, metadata=False):
        return subprocess.run(
            ['bash', HELPER, root, prefix, *(['DEBIAN'] if metadata else [])],
            capture_output=True, text=True,
        )

    def test_private_payload_and_debian_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bindir = root / PREFIX.lstrip('/') / 'bin'
            bindir.mkdir(parents=True)
            (bindir / 'tool').write_text('binary')
            (bindir / 'alias').symlink_to('tool')
            self.assertEqual(self.check_stage(root).returncode, 0)
            (root / 'DEBIAN').mkdir()
            (root / 'DEBIAN/control').write_text('metadata')
            self.assertNotEqual(self.check_stage(root).returncode, 0)
            self.assertEqual(self.check_stage(root, metadata=True).returncode, 0)

    def test_reject_outside_paths_including_symlinks_and_empty_directories(self):
        for path, kind in [('usr/share/doc/license', 'file'),
                           ('usr/bin/alias', 'symlink'), ('etc', 'directory'),
                           ('opt/other', 'file'), ('opt/icdesign/tools-extra', 'file')]:
            with self.subTest(path=path), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / PREFIX.lstrip('/')).mkdir(parents=True)
                outside = root / path
                outside.parent.mkdir(parents=True, exist_ok=True)
                if kind == 'symlink':
                    outside.symlink_to('/opt/icdesign/tools/bin/tool')
                elif kind == 'directory':
                    outside.mkdir()
                else:
                    outside.write_text('unexpected')
                result = self.check_stage(root, metadata=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Staged path outside', result.stderr)

    def test_prefix_must_remain_below_opt(self):
        for prefix in ['/usr/local', '/opt', '/opt/../usr']:
            with self.subTest(prefix=prefix), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / prefix.lstrip('/')).mkdir(parents=True, exist_ok=True)
                self.assertNotEqual(self.check_stage(root, prefix).returncode, 0)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'opt/custom/tools').mkdir(parents=True)
            self.assertEqual(self.check_stage(root, '/opt/custom/tools').returncode, 0)

    def test_all_recipes_keep_payload_private_and_enforce_check(self):
        fedora = (ROOT / 'shared/package-rpm').exists()
        for dockerfile in sorted((ROOT / 'packages').glob('*/Dockerfile')):
            with self.subTest(package=dockerfile.parent.name):
                text = dockerfile.read_text()
                self.assertIn('ARG PREFIX=/opt/icdesign/tools', text)
                self.assertNotIn('/pkgroot/usr', text)
                self.assertIn('"/pkgroot${PREFIX}/share/doc/icdesign-', text)
                if not fedora:
                    self.assertIn('check-install-prefix /pkgroot "${PREFIX}" DEBIAN;', text)
                    self.assertLess(text.index('check-install-prefix'), text.index('dpkg-deb'))
                # Syntax-check every RUN command after joining Docker continuations.
                for line in text.replace('\\\n', '').splitlines():
                    if line.startswith('RUN '):
                        subprocess.run(['bash', '-n', '-c', line[4:]], check=True)
        if fedora:
            text = (ROOT / 'shared/package-rpm').read_text()
            self.assertIn('check-install-prefix /pkgroot "$PREFIX"', text)
            self.assertNotIn('/usr/share', text)
            self.assertIn('%global _build_id_links none', text)
        shared = (ROOT / 'shared/Dockerfile').read_text()
        self.assertIn('check-install-prefix /opt/icdesign/build/bin/', shared)
        subprocess.run(['bash', '-n', HELPER], check=True)
        klayout = (ROOT / 'packages/klayout/Dockerfile').read_text()
        self.assertIn('Icon=${PREFIX}/share/pixmaps/icdesign-klayout.png', klayout)
        self.assertIn('"/pkgroot${PREFIX}/share/applications/icdesign-klayout.desktop"', klayout)


if __name__ == '__main__':
    unittest.main()
