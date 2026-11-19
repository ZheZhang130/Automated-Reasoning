"""Portable host contracts: stdlib-only tests, no inference or Docker required."""
import json
import os
import subprocess
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from local_agent import cli, portable
from local_agent.platform_support import REPO, Settings, model_lock


class Portable(unittest.TestCase):
    def test_backend_selection_preserves_windows(self):
        windows = Settings.load(system='Windows', environ={'CSC2108_ROOT': '/ignored', 'CSC2108_OLLAMA_ENDPOINT': 'http://other:1234'})
        self.assertEqual(windows.backend, 'windows')
        self.assertEqual(str(windows.root).replace('\\', '/'), 'E:/CSC2108Local')
        self.assertEqual(windows.endpoint, cli.ENDPOINT)
        mac = Settings.load(system='Darwin', environ={})
        self.assertEqual(mac.backend, 'portable')
        self.assertEqual(mac.root, (Path.home() / '.local/share/csc2108').resolve())
        with self.assertRaises(ValueError):
            Settings.load('windows', system='Darwin')

    def test_endpoint_and_checkout_guards(self):
        for endpoint in ('https://example.com', 'http://127.0.0.1:11434', 'http://localhost:1234/path', 'http://user:pass@localhost:1234'):
            with self.assertRaises(ValueError):
                Settings.load('portable', environ={'CSC2108_OLLAMA_ENDPOINT': endpoint})
        with self.assertRaises(ValueError):
            Settings.load('portable', environ={'CSC2108_ROOT': str(REPO / 'bad')})
        with tempfile.TemporaryDirectory() as root:
            settings = Settings('portable', Path(root))
            out = settings.output(Path(root) / 'new')
            self.assertTrue(out.is_dir())
            with self.assertRaises(FileExistsError):
                settings.output(out)
            with self.assertRaises(ValueError):
                settings.output(REPO / 'bad')

    def test_frozen_paths_work_on_posix_without_rewriting_hashes(self):
        with tempfile.TemporaryDirectory() as root, patch('local_agent.cli.importlib.metadata.version', side_effect=cli.PACKAGES.__getitem__):
            result = cli.verify(services=False, settings=Settings('portable', Path(root)))
        self.assertEqual(result['frozen_files_verified'], 38)
        self.assertEqual(result['profile'], 'heredoc-v6-16k-common')
        self.assertEqual(result['system_prompt_sha256'], '291f0f67e2dd461f777f9798a08c99de14d987b99acb6bc4e5f213162590ef05')
        self.assertEqual(result['image_ids'], {})

    def test_adapter_keeps_original_bytecode_and_limits(self):
        # A sentinel checks host binding substitution without importing the SDK or running an agent.
        def original(*, actions=20, repairs=3, seconds=600):
            return Path('E:/CSC2108Local/logs/ollama-project.stderr.log'), actions, repairs, seconds
        base = types.SimpleNamespace(Budget=object, container_args=lambda p: [], docker=lambda *a: None)
        runtime = types.SimpleNamespace(run=original, v3=base)
        with tempfile.TemporaryDirectory() as root:
            settings = Settings('portable', Path(root))
            function = portable.adapted_run(runtime, settings, {'agent': {'reference': 'test-image'}})
            self.assertIs(function.__code__, original.__code__)
            self.assertEqual(function(), (Path(root) / 'logs/ollama-project.stderr.log', 20, 3, 600))
            self.assertEqual(original()[0], Path('E:/CSC2108Local/logs/ollama-project.stderr.log'))

    def test_native_arm_image_verification_and_retag_rejection(self):
        with tempfile.TemporaryDirectory() as root:
            settings = Settings('portable', Path(root))
            manifest = {'schema_version': 1, 'recipe_sha256': portable.recipe_hash(), 'agent_reference': portable.BASE_IMAGE,
                        'agent': {'reference': 'agent', 'image_id': 'a', 'architecture': 'arm64'},
                        'judge': {'reference': 'judge', 'image_id': 'j', 'architecture': 'arm64'}}
            settings.manifest.write_text(json.dumps(manifest))
            def inspect(reference):
                return {'Id': {'agent': 'a', 'judge': 'j'}[reference], 'Architecture': 'arm64', 'Os': 'linux'}
            with patch.object(portable, 'inspect_image', side_effect=inspect), patch.object(portable, 'docker_preflight'):
                self.assertEqual(portable.verify_images(settings), manifest)
            with patch.object(portable, 'inspect_image', return_value={'Id': 'retagged', 'Architecture': 'arm64'}):
                with self.assertRaisesRegex(RuntimeError, 'image changed'):
                    portable.verify_images(settings)

    def test_adapter_preserves_user_task_paths(self):
        def original(task):
            return Path(task)
        runtime = types.SimpleNamespace(run=original, v3=types.SimpleNamespace(Budget=object, container_args=lambda p: [], docker=lambda *a: None))
        with tempfile.TemporaryDirectory() as root:
            function = portable.adapted_run(runtime, Settings('portable', Path(root)), {'agent': {'reference': 'image'}})
            for task in (Path(root) / 'public', 'E:/CSC2108Local/eval-v2/development-v5/public/example'):
                self.assertEqual(function(task), Path(task))

    def test_emulated_or_nonlinux_images_are_rejected(self):
        info = json.dumps({'OSType': 'linux', 'MemoryLimit': True, 'PidsLimit': True, 'Architecture': 'aarch64'})
        with patch.object(portable.subprocess, 'check_output', return_value=info):
            with patch.object(portable, 'inspect_image', return_value={'Id': 'a', 'Os': 'linux', 'Architecture': 'arm64'}):
                self.assertEqual(portable.docker_preflight('a')['image_architecture'], 'arm64')
            with patch.object(portable, 'inspect_image', return_value={'Id': 'a', 'Os': 'linux', 'Architecture': 'amd64'}):
                with self.assertRaisesRegex(RuntimeError, 'native-architecture'):
                    portable.docker_preflight('a')

    @unittest.skipIf(os.name == 'nt', 'POSIX advisory lock; Windows retains the historical lock')
    def test_posix_lock_contention_and_reuse(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ):
            settings = Settings('portable', Path(root))
            with model_lock(settings):
                with self.assertRaisesRegex(RuntimeError, 'owns this data root'):
                    with model_lock(settings):
                        pass
            with model_lock(settings):
                self.assertTrue((Path(root) / 'eval-v2/gpu.lock').exists())

    def test_fixture_exports_separate_private_row(self):
        from local_agent.portable_sanity import fixtures
        with tempfile.TemporaryDirectory() as root:
            result = fixtures(Path(root) / 'fixture', Settings('portable', Path(root)))
            public = Path(result['public'])
            self.assertEqual({p.name for p in public.iterdir()}, {'task.json', 'check.py', 'solution.py', 'public_tests.json'})
            self.assertNotIn('private_test_cases', (public / 'task.json').read_text())
            self.assertEqual(Path(result['private_row']).parent, public.parent)


if __name__ == '__main__':
    unittest.main(verbosity=2)
