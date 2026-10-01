import json
from pathlib import Path

targets = {"primevul:original:2771", "primevul:original:206947", "primevul:original:389786",
           "primevul:original:2769", "primevul:original:160154"}

for path in Path("data/interim/primevul").glob("records.jsonl"):
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row["sample_id"] in targets:
                func = row.get("source_raw") or ""
                print(row["sample_id"], "chars=", len(func), "lines=", func.count("\n"))
