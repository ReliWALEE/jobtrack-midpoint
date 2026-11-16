"""Deployment archives must work after root extraction for a non-root service."""
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


class SourceArchive(unittest.TestCase):
    def test_private_source_modes_are_normalized_without_packaging_secrets(self):
        spec = importlib.util.spec_from_file_location(
            'review_package_source', Path(__file__).resolve().parents[1] / 'deploy/package_source.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('server.py', 'account_factory.py', 'web/index.html', 'web/.env'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('fixture')
                path.chmod(0o600)
            output = root / 'source.zip'
            with patch.multiple(module, ROOT=root, OUTPUT=output):
                module.main()
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), {
                    'JobTrack/server.py', 'JobTrack/account_factory.py', 'JobTrack/web/index.html'})
                for entry in archive.infolist():
                    self.assertEqual((entry.external_attr >> 16) & 0o777, 0o644)
                    self.assertEqual(archive.read(entry), b'fixture')
