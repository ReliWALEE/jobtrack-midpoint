"""Per-run account lifecycle checks; provider signup is always mocked."""
import contextlib
import io
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import account_factory
import jobs
from server import create_server, rotate_account_background


class FreshRunAccounts(unittest.TestCase):
    def setUp(self):
        self.state = patch.multiple(jobs, _RUNTIME_KEY='', _RUN_ACCOUNT_STATE='manual')
        self.state.start()
        self.addCleanup(self.state.stop)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'db.sqlite3'

    def server(self):
        server = create_server(port=0, db_path=self.path)
        self.addCleanup(server.server_close)
        return server

    def test_each_run_acquires_a_new_key_even_with_existing_history(self):
        account_factory.remember_account(self.path, 'old@example.test', 'old-fixture-key')
        issued = iter(['first-run-fixture-key', 'second-run-fixture-key'])

        def acquire(**kwargs):
            self.assertEqual(jobs.configured_key(), '')
            self.assertEqual(kwargs['persist_path'], str(self.path))
            self.assertEqual(jobs._RUN_ACCOUNT_STATE, 'pending')
            return next(issued)

        with patch.dict(os.environ, {'JSEARCH_API_KEY': 'manual-fixture-key'}), \
             patch('account_factory.acquire_run_key', side_effect=acquire) as signup, \
             patch('account_factory.last_saved_key') as saved, \
             contextlib.redirect_stdout(io.StringIO()):
            for expected in ('first-run-fixture-key', 'second-run-fixture-key'):
                server = self.server()
                thread = rotate_account_background(server)
                thread.join(timeout=2)
                self.assertFalse(thread.is_alive())
                self.assertEqual(jobs.configured_key(), expected)
                self.assertEqual(server.jobs.sources()['account_setup'],
                                 {'mode': 'automatic', 'status': 'ready'})
            self.assertEqual(signup.call_count, 2)
            saved.assert_not_called()

    def test_pending_setup_blocks_old_keys_until_fresh_key_is_ready(self):
        entered, release = threading.Event(), threading.Event()
        server = self.server()

        def acquire(**kwargs):
            entered.set()
            if not release.wait(timeout=3):
                raise TimeoutError('fixture was not released')
            return 'new-fixture-key'

        with patch.dict(os.environ, {'JSEARCH_API_KEY': 'manual-fixture-key'}), \
             patch('account_factory.acquire_run_key', side_effect=acquire), \
             contextlib.redirect_stdout(io.StringIO()):
            thread = rotate_account_background(server)
            try:
                self.assertTrue(entered.wait(timeout=2))
                self.assertFalse(server.jobs.sources()['jsearch_ready'])
                self.assertEqual(server.jobs.sources()['account_setup']['status'], 'pending')
                with self.assertRaisesRegex(jobs.ProviderError, 'Creating a fresh account'):
                    server.jobs.search('linkedin', 'engineer')
            finally:
                release.set()
                thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            self.assertTrue(server.jobs.sources()['jsearch_ready'])

    def test_failed_setup_never_reuses_manual_or_saved_keys(self):
        server = self.server()
        jobs.set_runtime_key('previous-fixture-key')
        with patch.dict(os.environ, {'JSEARCH_API_KEY': 'manual-fixture-key'}), \
             patch('account_factory.acquire_run_key', side_effect=account_factory.AccountError('fixture failure')), \
             patch('account_factory.last_saved_key', return_value='saved-fixture-key') as saved, \
             contextlib.redirect_stdout(io.StringIO()):
            thread = rotate_account_background(server)
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            self.assertEqual(jobs.configured_key(), '')
            self.assertEqual(server.jobs.sources()['account_setup']['status'], 'failed')
            self.assertFalse(server.jobs.sources()['jsearch_ready'])
            saved.assert_not_called()
            with self.assertRaisesRegex(jobs.ProviderError, 'Could not create a fresh account'):
                server.jobs.search('linkedin', 'engineer')

    def test_empty_provider_key_is_a_failed_run(self):
        server = self.server()
        with patch('account_factory.acquire_run_key', return_value=' '), \
             contextlib.redirect_stdout(io.StringIO()):
            thread = rotate_account_background(server)
            thread.join(timeout=2)
        self.assertFalse(server.jobs.sources()['jsearch_ready'])
        self.assertEqual(server.jobs.sources()['account_setup']['status'], 'failed')

    def test_explicit_manual_mode_retains_existing_configuration(self):
        server = self.server()
        with patch.dict(os.environ, {'JSEARCH_API_KEY': 'manual-fixture-key'}):
            self.assertEqual(jobs.configured_key(), 'manual-fixture-key')
            self.assertTrue(server.jobs.sources()['jsearch_ready'])
            self.assertEqual(server.jobs.sources()['account_setup']['mode'], 'manual')
