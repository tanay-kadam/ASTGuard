import json
from pathlib import Path

p = Path("artifacts/release_gates/registry_plan_stage0.json")
data = json.loads(p.read_text(encoding="utf-8"))
print("OK", data["cohorts"]["P_clean"]["manifest"])
