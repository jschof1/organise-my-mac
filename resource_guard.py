"""Opt-in macOS heavy-command gate and one-shot resource monitor (stdlib only)."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager

GIB = 1024 ** 3
DRIVE = Path('/Volumes/Jack Drive')
DRIVE_UUID = '77835823-7D54-386B-B6C2-2E65AB80C5B8'
DEFAULTS = {'CMAKE_BUILD_PARALLEL_LEVEL': '2', 'UV_THREADPOOL_SIZE': '2',
            'MAKEFLAGS': '-j2'}


def state_dir():
    return Path.home() / '.local/state/mac-resource-guard'


@contextmanager
def lock(name='heavy.lock'):
    directory = state_dir()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / name).open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield None
        else:
            # Closing releases our reference; an inherited child retains ownership.
            yield handle


def free_gib(path):
    stat = os.statvfs(path)
    return stat.f_bavail * stat.f_frsize / GIB


def jack_drive():
    result = {'available': False, 'free_gib': None, 'error': None}
    try:
        if not os.path.ismount(DRIVE):
            raise ValueError('Jack Drive is not mounted')
        info = subprocess.run(['/usr/sbin/diskutil', 'info', '-plist', str(DRIVE)],
                              capture_output=True, check=True, timeout=3)
        volume = plistlib.loads(info.stdout)
        if (volume.get('VolumeUUID') != DRIVE_UUID or volume.get('Mounted') is False
                or volume.get('MountPoint') != str(DRIVE)):
            raise ValueError('Jack Drive mount identity does not match')
        result.update(available=True, free_gib=free_gib(DRIVE))
    except (OSError, ValueError, plistlib.InvalidFileException,
            subprocess.SubprocessError) as error:
        result['error'] = str(error)[:500]
    return result


def notification_state():
    try:
        with (state_dir() / 'status.json').open() as handle:
            saved = json.loads(handle.read(16385))
        value = saved.get('notification', {})
        attempt = value.get('last_attempt_at')
        return {'last_attempt_at': attempt if isinstance(attempt, (int, float)) else None,
                'error': str(value['error'])[:500] if value.get('error') else None}
    except (OSError, ValueError, AttributeError, TypeError):
        return {'last_attempt_at': None, 'error': None}


def status(lock_owned=False):
    result = {'checked_at': time.time(), 'home': str(Path.home()),
              'home_free_gib': None, 'load_1m': None, 'logical_cpus': os.cpu_count(),
              'disk_status': 'unknown', 'reasons': [], 'notification': notification_state()}
    reasons = result['reasons']
    try:
        free = result['home_free_gib'] = free_gib(Path.home())
        result['disk_status'] = 'critical' if free < 10 else 'low' if free < 25 else 'healthy'
        if free < 10:
            reasons.append('Home volume has less than 10 GiB available')
    except OSError as error:
        reasons.append('Home volume measurement failed: ' + str(error))
    try:
        load = result['load_1m'] = os.getloadavg()[0]
        if not result['logical_cpus'] or load > result['logical_cpus']:
            reasons.append('Load exceeds logical CPU count or CPU count is unknown')
    except OSError as error:
        reasons.append('Load measurement failed: ' + str(error))
    result['heavy_job_running'] = False
    if not lock_owned:
        try:
            with lock() as handle:
                result['heavy_job_running'] = handle is None
                if handle is None:
                    reasons.append('Another guarded heavy job holds the lock')
        except OSError as error:
            reasons.append('Guard lock unavailable: ' + str(error))
    result['heavy_allowed'] = not reasons
    result['jack_drive'] = jack_drive()
    return result


def run_command(command):
    with lock() as handle:
        if handle is None:
            print('Refused: another guarded heavy job holds the lock', file=sys.stderr)
            return 1
        current = status(lock_owned=True)
        if not current['heavy_allowed']:
            print('Refused: ' + '; '.join(current['reasons']), file=sys.stderr)
            return 1
        env = os.environ.copy()
        for key, value in DEFAULTS.items():
            env.setdefault(key, value)
        child = subprocess.Popen(['/usr/bin/nice', '-n', '10', *command],
                                 env=env, pass_fds=(handle.fileno(),))
        while True:
            try:
                return child.wait()
            except KeyboardInterrupt:
                # Terminal SIGINT reaches the child too; retain the lock until exit.
                continue


def notify(message):
    script = ('on run argv\n'
              'display notification (item 1 of argv) with title "Mac Resource Guard"\n'
              'end run')
    try:
        subprocess.run(['/usr/bin/osascript', '-e', script, message],
                       capture_output=True, check=True, timeout=5)
        return None
    except (OSError, subprocess.SubprocessError) as error:
        detail = getattr(error, 'stderr', b'') or b''
        if isinstance(detail, bytes):
            detail = detail.decode(errors='replace')
        return (str(error) + ': ' + detail)[:500]


def write_status(current):
    destination = state_dir() / 'status.json'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=state_dir(), delete=False) as handle:
            temporary = handle.name
            json.dump(current, handle, indent=2, allow_nan=False)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def monitor():
    with lock('monitor.lock') as handle:
        if handle is None:
            raise OSError('Another monitor pass is running')
        current = status()
        alerts = []
        if current['disk_status'] in ('low', 'critical'):
            alerts.append(f"Home disk {current['disk_status']}: {current['home_free_gib']:.1f} GiB free")
        if (current['load_1m'] is not None and current['logical_cpus']
                and current['load_1m'] > current['logical_cpus']):
            alerts.append(f"High load: {current['load_1m']:.2f} / {current['logical_cpus']} CPUs")
        last = current['notification']['last_attempt_at']
        if alerts and (last is None or current['checked_at'] - last >= 3600):
            current['notification'] = {'last_attempt_at': current['checked_at'],
                                       'error': notify('; '.join(alerts))}
        write_status(current)
        return current


def display(current, as_json):
    if as_json:
        print(json.dumps(current, indent=2, allow_nan=False))
    else:
        print(f"Home free GiB: {current['home_free_gib']} ({current['disk_status']})")
        print(f"1m load: {current['load_1m']}; logical CPUs: {current['logical_cpus']}")
        print('Heavy command: ' + ('allowed' if current['heavy_allowed'] else 'refused'))
        for reason in current['reasons']:
            print('  ' + reason)
        drive = current['jack_drive']
        print('Jack Drive: ' + (f"available, {drive['free_gib']:.1f} GiB free"
                                if drive['available'] else 'unavailable: ' + drive['error']))
        if current['notification']['error']:
            print('Notification failure: ' + current['notification']['error'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    for action in ('status', 'check', 'monitor'):
        commands.add_parser(action).add_argument('--json', action='store_true')
    commands.add_parser('run').add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.action == 'run' and (len(args.command) < 2 or args.command[0] != '--'):
        parser.error('run requires -- command args...')
    try:
        if args.action == 'run':
            return run_command(args.command[1:])
        current = monitor() if args.action == 'monitor' else status()
        display(current, args.json)
        return int(args.action == 'check' and not current['heavy_allowed'])
    except (OSError, subprocess.SubprocessError) as error:
        print('Resource guard error: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    code = main()
    sys.exit(128 - code if code < 0 else code)
