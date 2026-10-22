"""Install the read-only monitor and opt-in command gate for the current Mac user."""
from pathlib import Path
import os
import plistlib
import shutil
import subprocess

home = Path.home()
library = home / '.local/lib/mac-resource-guard'
state = home / '.local/state/mac-resource-guard'
binary = home / '.local/bin/mac-resource-guard'
agents = home / 'Library/LaunchAgents'
for directory in (library, state, binary.parent, agents):
    directory.mkdir(parents=True, exist_ok=True)
state.chmod(0o700)
shutil.copy2(Path(__file__).with_name('resource_guard.py'), library / 'resource_guard.py')
binary.write_text('#!/bin/sh\nexec /usr/bin/python3 -B "$HOME/.local/lib/mac-resource-guard/resource_guard.py" "$@"\n')
binary.chmod(0o755)
label = 'com.jack.mac-resource-guard'
plist = agents / (label + '.plist')
with plist.open('wb') as handle:
    plistlib.dump({
        'Label': label,
        'ProgramArguments': ['/usr/bin/python3', '-B', str(library / 'resource_guard.py'), 'monitor'],
        'StartInterval': 300, 'RunAtLoad': True, 'Nice': 10,
        'LowPriorityIO': True, 'ProcessType': 'Background',
        'StandardOutPath': '/dev/null', 'StandardErrorPath': '/dev/null',
    }, handle)
target = 'gui/' + str(os.getuid())
subprocess.run(['/bin/launchctl', 'bootout', target + '/' + label],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(['/bin/launchctl', 'bootstrap', target, str(plist)], check=True)
print('Installed ' + str(binary))
print('Monitor runs every 5 minutes while this user session is active.')
print('Only commands invoked through mac-resource-guard run are gated.')
