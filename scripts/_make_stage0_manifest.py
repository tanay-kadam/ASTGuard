import json
from pathlib import Path

EXCLUDE = {
    "primevul:original:2771",
    "primevul:original:206947",
    "primevul:original:389786",
    "primevul:original:2769",
    "primevul:original:160154",
}

src = Path("artifacts/audits/P_clean.json")
dst = Path("artifacts/audits/P_clean_stage0.json")

manifest = json.loads(src.read_text(encoding="utf-8"))
before = len(manifest["ordered_sample_ids"])
manifest["ordered_sample_ids"] = [sid for sid in manifest["ordered_sample_ids"] if sid not in EXCLUDE]
after = len(manifest["ordered_sample_ids"])
manifest["stage0_excluded_outliers"] = sorted(EXCLUDE)
manifest["stage0_exclusion_reason"] = (
    "Excluded 5 sample_ids whose extracted 'function' spans thousands of lines "
    "(two of them >480KB / ~24000 lines, almost certainly mis-parsed data/lookup "
    "tables rather than real functions), causing intractable AST/DFG relation "
    "construction time under leaf_path_radius4 during feature-cache warming. "
    "Excluded for the Stage 0 diagnostic only; does not affect the full P_clean "
    "manifest used elsewhere."
)
dst.write_text(json.dumps(manifest), encoding="utf-8")
print("before", before, "after", after, "removed", before - after)
