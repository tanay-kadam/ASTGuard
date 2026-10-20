"""Apply a recorded scheduling amendment without changing frozen training code."""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file

ROOT = REPO/'artifacts/seven_day_20261012'
AMENDMENT = ROOT/'deadline_amendment_20261012.json'
STATUS = ROOT/'deadline_guard_status.json'
SESSION = 'astguard_7day_deadline_guard'


def configure():
    if AMENDMENT.exists():
        raise FileExistsError('Preserve existing scheduling amendments')
    plan_path = ROOT/'plan.json'
    plan = json.loads(plan_path.read_text())
    local = datetime(2026, 10, 16, 21, tzinfo=ZoneInfo('America/Indiana/Indianapolis'))
    atomic_write_json(AMENDMENT, {
        'recorded_utc': datetime.now(timezone.utc).isoformat(),
        'user_instruction': 'make the stop deadline 16th 9 pm',
        'timezone': 'America/Indiana/Indianapolis',
        'stop_starting_after_local': local.isoformat(),
        'stop_starting_after_utc': local.astimezone(timezone.utc).isoformat(),
        'supersedes_stop_starting_after_utc': plan['stop_starting_after_utc'],
        'frozen_plan_sha256': sha256_file(plan_path),
        'policy': 'Stop starting new training runs; in-progress runs and evaluation continue.',
        'model_training_and_cohort_protocols_unchanged': True,
    })


def load():
    doc = json.loads(AMENDMENT.read_text())
    assert sha256_file(ROOT/'plan.json') == doc['frozen_plan_sha256']
    local = datetime.fromisoformat(doc['stop_starting_after_local'])
    deadline = datetime.fromisoformat(doc['stop_starting_after_utc'])
    assert local.astimezone(timezone.utc) == deadline
    assert deadline.tzinfo is not None
    return doc, deadline


def watch():
    doc, deadline = load()
    while True:
        now = datetime.now(timezone.utc)
        remaining = (deadline-now).total_seconds()
        if remaining <= 0:
            (ROOT/'STOP_STARTING').touch(exist_ok=True)
        atomic_write_json(STATUS, {
            'status': 'cutoff_applied' if remaining <= 0 else 'armed',
            'utc': now.isoformat(), 'pid': os.getpid(),
            'stop_starting_after_utc': doc['stop_starting_after_utc'],
            'stop_starting_after_local': doc['stop_starting_after_local'],
            'amendment_sha256': sha256_file(AMENDMENT),
            'processes_signaled': False,
            'stop_file_exists': (ROOT/'STOP_STARTING').exists(),
        })
        if remaining <= 0:
            return
        time.sleep(min(30, remaining))


def launch():
    load()
    if subprocess.run(['tmux', 'has-session', '-t', SESSION], capture_output=True).returncode == 0:
        raise RuntimeError('Deadline guard already running')
    argv = [sys.executable, '-u', str(Path(__file__).resolve()), '--watch']
    shell = shlex.join(argv)+' > '+shlex.quote(str(ROOT/'deadline_guard.log'))+' 2>&1'
    subprocess.run(['tmux', 'new-session', '-d', '-s', SESSION, '-c', str(REPO), shell], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--configure', action='store_true')
    parser.add_argument('--launch', action='store_true')
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.configure: configure()
    if args.launch: launch()
    if args.watch: watch()
    if args.check:
        doc, _ = load()
        print(json.dumps({'amendment': doc, 'guard': json.loads(STATUS.read_text())}, indent=2))
    if not any(vars(args).values()): parser.error('choose an action')


if __name__ == '__main__': main()
