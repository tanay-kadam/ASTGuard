"""Read-only compact status and latest completed epoch for the frozen matrix."""
import json
from collections import Counter
from pathlib import Path

root = Path('/home/tkadam/ASTGuard/artifacts/release_gates/strengthening_20261006')
rows = []
for job in json.loads((root/'jobs.json').read_text())['jobs']:
    target = root/'jobs'/job['tag']
    path = target/'status.json'
    state = json.loads(path.read_text()) if path.exists() else {'status': 'not_started'}
    row = dict(tag=job['tag'], status=state['status'], gpu=state.get('gpu'))
    if state['status'] not in ('complete',):
        logs = list(target.glob('runs/*/train_log.jsonl'))
        if logs:
            lines = logs[0].read_text().splitlines()
            if lines:
                record = json.loads(lines[-1])
                row.update(epoch=record.get('epoch'), optimizer_steps=record.get('optimizer_steps'),
                           epoch_log_mtime=logs[0].stat().st_mtime)
        events = list(target.glob('runs/*/events.jsonl'))
        if events:
            row['events'] = [json.loads(line) for line in events[0].read_text().splitlines()][-2:]
        if state.get('error'):
            row['error'] = state['error']
    rows.append(row)
print(json.dumps({'counts': dict(Counter(row['status'] for row in rows)),
                  'unfinished': [row for row in rows if row['status'] != 'complete']}, indent=2))
