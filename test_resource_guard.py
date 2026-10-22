import contextlib
import io
import json
import os
from pathlib import Path
import plistlib
import select
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import resource_guard as guard


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ, HOME=str(self.home)))
        self.free = self.stack.enter_context(patch.object(guard, 'free_gib', return_value=30))
        self.load = self.stack.enter_context(patch.object(os, 'getloadavg', return_value=(1, 1, 1)))
        self.stack.enter_context(patch.object(os, 'cpu_count', return_value=2))
        self.stack.enter_context(patch.object(guard, 'jack_drive', return_value={
            'available': False, 'free_gib': None, 'error': 'not mounted'}))

    def test_disk_boundaries_and_load_gate(self):
        for free, disk, allowed in [(9.99, 'critical', False), (10, 'low', True),
                                     (24.99, 'low', True), (25, 'healthy', True)]:
            with self.subTest(free=free):
                self.free.return_value = free
                current = guard.status()
                self.assertEqual(current['disk_status'], disk)
                self.assertEqual(current['heavy_allowed'], allowed)
        self.load.return_value = (2, 0, 0)
        self.assertTrue(guard.status()['heavy_allowed'])
        self.load.return_value = (2.01, 0, 0)
        self.assertFalse(guard.status()['heavy_allowed'])

    def test_refused_commands_never_execute_and_check_is_nonzero(self):
        marker = self.home / 'executed'
        command = [sys.executable, '-c', f'from pathlib import Path; Path({str(marker)!r}).touch()']
        for free, load in [(9, 0), (30, 3)]:
            with self.subTest(free=free, load=load):
                self.free.return_value = free
                self.load.return_value = (load, 0, 0)
                with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(guard.run_command(command), 1)
                    self.assertEqual(guard.main(['check', '--json']), 1)
                self.assertFalse(marker.exists())

    def test_failed_measurements_fail_closed(self):
        self.free.side_effect = OSError('unavailable')
        self.assertFalse(guard.status()['heavy_allowed'])
        self.free.side_effect = None
        self.load.side_effect = OSError('unavailable')
        self.assertFalse(guard.status()['heavy_allowed'])

    def test_exit_code_worker_defaults_explicit_overrides_and_nice(self):
        output = self.home / 'child.json'
        script = ('import json,os,pathlib; '
                  f'pathlib.Path({str(output)!r}).write_text(json.dumps('
                  '[os.environ[k] for k in '+repr(list(guard.DEFAULTS))+
                  ']+[os.nice(0)])); raise SystemExit(7)')
        with patch.dict(os.environ, {'MAKEFLAGS': '-j1'}):
            for key in ('CMAKE_BUILD_PARALLEL_LEVEL', 'UV_THREADPOOL_SIZE'):
                os.environ.pop(key, None)
            self.assertEqual(guard.run_command([sys.executable, '-c', script]), 7)
        self.assertEqual(json.loads(output.read_text()), ['2', '2', '-j1', min(19, os.nice(0) + 10)])
        self.assertTrue(guard.status()['heavy_allowed'])

    def test_real_child_holds_flock_until_exit_and_excludes_second_command(self):
        child_script = 'import sys; print("ready", flush=True); sys.stdin.readline()'
        wrapper = ('import resource_guard as g; '
                   'g.status=lambda **kw: {"heavy_allowed": True}; '
                   f'raise SystemExit(g.run_command({[sys.executable, "-c", child_script]!r}))')
        process = subprocess.Popen([sys.executable, '-B', '-c', wrapper],
                                   cwd=Path(guard.__file__).parent,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        try:
            self.assertTrue(select.select([process.stdout], [], [], 5)[0], 'child did not start')
            self.assertEqual(process.stdout.readline().strip(), 'ready')
            self.assertTrue(guard.status()['heavy_job_running'])
            marker = self.home / 'second-child'
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(guard.run_command([
                    sys.executable, '-c', f'open({str(marker)!r}, "w").close()']), 1)
            self.assertFalse(marker.exists())
            self.assertTrue(guard.status()['heavy_job_running'])
        finally:
            process.stdin.close()
            process.wait(timeout=5)
            process.stdout.close()
        self.assertEqual(process.returncode, 0)
        self.assertFalse(guard.status()['heavy_job_running'])

    def test_monitor_is_bounded_atomic_and_cools_down_visible_notification_failure(self):
        self.free.return_value = 12
        with patch.object(guard, 'notify', return_value='headless notification unavailable') as notify:
            first = guard.monitor()
            second = guard.monitor()
            self.assertEqual(notify.call_count, 1)
            self.assertEqual(first['notification'], second['notification'])
            self.assertEqual(guard.status()['notification']['error'], 'headless notification unavailable')
            with patch.object(guard.time, 'time', return_value=first['checked_at'] + 3600):
                guard.monitor()
            self.assertEqual(notify.call_count, 2)
        path = guard.state_dir() / 'status.json'
        self.assertLess(path.stat().st_size, 16384)
        self.assertEqual(json.loads(path.read_text())['disk_status'], 'low')
        self.assertEqual(sorted(p.name for p in path.parent.iterdir()),
                         ['heavy.lock', 'monitor.lock', 'status.json'])


class VolumeAndNotificationTests(unittest.TestCase):
    def test_macos_plist_without_optional_mounted_key(self):
        info = plistlib.dumps({'VolumeUUID': guard.DRIVE_UUID, 'MountPoint': str(guard.DRIVE)})
        with patch.object(os.path, 'ismount', return_value=True), \
                patch.object(guard.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, info)), \
                patch.object(guard, 'free_gib', return_value=123):
            self.assertTrue(guard.jack_drive()['available'])

    def test_missing_mount_does_not_measure_fallback_directory(self):
        with patch.object(os.path, 'ismount', return_value=False), \
                patch.object(guard.subprocess, 'run') as run, patch.object(guard, 'free_gib') as free:
            self.assertEqual(guard.jack_drive()['free_gib'], None)
            self.assertFalse(guard.jack_drive()['available'])
            run.assert_not_called()
            free.assert_not_called()

    def test_volume_uuid_and_mount_must_match(self):
        for uuid, mounted, point, available in [
            ('wrong', True, str(guard.DRIVE), False),
            (guard.DRIVE_UUID, False, str(guard.DRIVE), False),
            (guard.DRIVE_UUID, True, '/elsewhere', False),
            (guard.DRIVE_UUID, True, str(guard.DRIVE), True),
        ]:
            with self.subTest(uuid=uuid, mounted=mounted, point=point):
                info = plistlib.dumps({'VolumeUUID': uuid, 'Mounted': mounted, 'MountPoint': point})
                with patch.object(os.path, 'ismount', return_value=True), \
                        patch.object(guard.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, info)), \
                        patch.object(guard, 'free_gib', return_value=123) as free:
                    result = guard.jack_drive()
                    self.assertEqual(result['available'], available)
                    self.assertEqual(result['free_gib'], 123 if available else None)
                    self.assertEqual(free.call_count, int(available))

    def test_notification_text_is_an_argument_never_script_source(self):
        message = '\"); do shell script "touch /tmp/should-not-run" -- $(echo bad)\n'
        with patch.object(guard.subprocess, 'run') as run:
            self.assertIsNone(guard.notify(message))
            args, kwargs = run.call_args
            self.assertEqual(args[0][-1], message)
            self.assertNotIn(message, args[0][2])
            self.assertNotIn('shell', kwargs)
        with patch.object(guard.subprocess, 'run', side_effect=FileNotFoundError('osascript unavailable')):
            self.assertIn('osascript unavailable', guard.notify('warning'))


if __name__ == '__main__':
    unittest.main()
