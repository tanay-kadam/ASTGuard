import json
from pathlib import Path
import sys
sys.path.insert(0, ".")
from astguard.utils.hashing import object_hash
from astguard.data.schema import read_jsonl

plan = json.loads(Path("artifacts/release_gates/registry_plan_stage0.json").read_text())
cohort = plan["cohorts"]["P_clean"]
manifest = json.loads(Path(cohort["manifest"]).read_text())
wanted = set(manifest["ordered_sample_ids"])
print("total_needed", len(wanted))

preprocessing_hash = "435aff72451638dae06492868e79a97c591178ea66ad2935799a61245bf0e869"
cache_root = Path("data/cache/features") / preprocessing_hash

source_by_id = {}
for path in cohort["records"]:
    for row in read_jsonl(path):
        if row["sample_id"] in wanted:
            source_by_id[row["sample_id"]] = row["raw_sha256"]

missing = []
for sid in wanted:
    src = source_by_id.get(sid)
    if src is None:
        missing.append((sid, "no_source_row"))
        continue
    key = object_hash([src, preprocessing_hash, sid])
    target = cache_root / key[:2] / (key + ".json")
    if not target.exists():
        missing.append((sid, "not_cached"))

print("missing_count", len(missing))
for sid, reason in missing[:50]:
    print("MISSING", sid, reason)
