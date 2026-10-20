"""Keep the selection-diagnostic report current without changing training."""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from seven_day_finalize import ROOT, selection_diagnostic, synthetic_checks

while datetime.now(timezone.utc) < datetime.fromisoformat('2026-10-19T05:30:00+00:00'):
    path = ROOT/'verified_metrics.json'
    if path.exists():
        checks = json.loads(path.read_text())['jobs']
        selection_diagnostic(checks)
        synthetic_checks(checks)
        if (json.loads((ROOT/'selection_diagnostic.json').read_text())['complete']
                and json.loads((ROOT/'synthetic_control_checks.json').read_text())['complete']):
            break
    time.sleep(60)
