import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import installer
from transforms import META_OLD, UI_REPLACEMENTS
from transforms import RECENT, TOP


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'extension'
        self.settings = Path(self.temp.name) / 'settings.json'
        self.settings.write_bytes(b'{\r\n // Keep this comment\r\n "chatgpt.historyCurrentWorkspaceOnly": false,\r\n "other": 42\r\n}\r\n')
        self.originals = [META_OLD.encode(), json.dumps({
            'name': 'chatgpt', 'publisher': 'openai', 'version': installer.VERSION,
            'contributes': {'configuration': {'properties': {}}}}).encode(),
            '\n'.join(old for old, new in UI_REPLACEMENTS).encode(),
            (RECENT + '\n' + TOP).encode()]
        for name, data in zip(installer.FILES, self.originals):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def run_action(self, action):
        with patch('sys.argv', ['installer.py', action, '--extension', str(self.root), '--settings', str(self.settings)]), contextlib.redirect_stdout(io.StringIO()):
            installer.main()

    def test_install_idempotent_restore_preserves_bytes(self):
        original_settings = self.settings.read_bytes()
        self.run_action('check')
        self.assertFalse((self.root / installer.BACKUP_DIR).exists())
        self.run_action('install')
        self.assertIn(b': true,\r\n', self.settings.read_bytes())
        self.assertIn(b'// Keep this comment', self.settings.read_bytes())
        patched = [(self.root / name).read_bytes() for name in installer.FILES]
        self.run_action('install')
        self.assertEqual(patched, [(self.root / name).read_bytes() for name in installer.FILES])
        self.run_action('restore')
        self.assertEqual(self.originals, [(self.root / name).read_bytes() for name in installer.FILES])
        self.assertEqual(original_settings, self.settings.read_bytes())
        self.run_action('install')
        self.run_action('restore')

    def test_changed_file_prevents_any_restore(self):
        self.run_action('install')
        target = self.root / installer.FILES[-1]
        target.write_bytes(target.read_bytes() + b'other change')
        before = [(self.root / name).read_bytes() for name in installer.FILES]
        with self.assertRaises(ValueError):
            self.run_action('restore')
        self.assertEqual(before, [(self.root / name).read_bytes() for name in installer.FILES])

    def test_new_settings_preserved_on_restore(self):
        self.run_action('install')
        self.settings.write_text('{"newSetting": true}')
        self.run_action('restore')
        self.assertEqual('{"newSetting": true}', self.settings.read_text())

    def test_unknown_bundle_rejected_before_writes(self):
        target = self.root / installer.FILES[-1]
        target.write_text('unknown build')
        with self.assertRaises(ValueError):
            self.run_action('install')
        self.assertEqual(self.originals[0], (self.root / installer.FILES[0]).read_bytes())
        self.assertFalse((self.root / installer.BACKUP_DIR).exists())


if __name__ == '__main__':
    unittest.main()
