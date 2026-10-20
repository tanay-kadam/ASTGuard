"""Resume only the four explicitly paused campaign processes after foreign jobs exit.

This operational guard never signals any other user's process and never changes
scientific configs. Paused jobs retain their existing RNG/training state.
"""
import json
import os
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/tmp/astguard_seven_day_20261012/artifacts/seven_day_20261012')
PAUSED = {0: 3673635, 1: 3673921, 4: 3673926, 7: 3673613}


def main():
    start = datetime.now(timezone.utc).isoformat()
    pending = dict(PAUSED)
    log = ROOT/'resource_contention.jsonl'
    with log.open('a') as f:
        f.write(json.dumps({'utc': start, 'event': 'foreign_workload_after_launch', 'paused_own_pids': PAUSED})+'\n')
    while pending:
        gpu_rows = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid', '--format=csv,noheader'], text=True)
        uuids = {int(line.split(',')[0]): line.split(',')[1].strip() for line in gpu_rows.splitlines()}
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader'], text=True)
        by_uuid = {}
        for line in apps.splitlines():
            uuid, pid = line.split(',')
            by_uuid.setdefault(uuid.strip(), set()).add(int(pid))
        for gpu, pid in list(pending.items()):
            path = Path(f'/proc/{pid}')
            if not path.exists():
                pending.pop(gpu)
                continue
            cmdline = (path/'cmdline').read_bytes().replace(b'\0', b' ').decode()
            if path.stat().st_uid != os.getuid() or '/tmp/astguard_seven_day_20261012/' not in cmdline or 'astguard.train' not in cmdline:
                raise RuntimeError(f'Refusing to signal unrecognized PID {pid}')
            foreign = by_uuid.get(uuids[gpu], set()) - {pid}
            if not foreign:
                os.kill(pid, signal.SIGCONT)
                with log.open('a') as f:
                    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                        'event': 'resumed_own_process', 'gpu': gpu, 'pid': pid})+'\n')
                pending.pop(gpu)
        (ROOT/'resource_wait_status.json').write_text(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
            'waiting_own_pids': pending, 'foreign_processes_never_signaled': True}, indent=2)+'\n')
        if pending:
            time.sleep(30)


if __name__ == '__main__':
    main()
