"""Diagnostic: parse coverage under byte-preserving masking of annotation macros.

Diagnostic only. It does not change the registered extractor. The a-priori list
is fixed from documented Linux sparse/section annotations and Windows SDK
calling-convention macros; the project list is a pilot-derived sensitivity
check and must not be adopted on the strength of the pilot alone.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astguard.alignment.tokenizer import CanonicalTokenizer
from astguard.data.schema import read_jsonl
from astguard.parsing.trees import select_c_or_cpp
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import hash_uniform

A_PRIORI = {
    "linux_sparse": ["__user", "__kernel", "__iomem", "__force", "__rcu", "__percpu", "__bitwise", "__safe",
                     "__nocast", "__private"],
    "linux_attribute": ["__init", "__exit", "__initdata", "__always_inline", "noinline", "asmlinkage", "__cold",
                        "__hot", "__pure", "__must_check", "__maybe_unused", "__used", "notrace", "__weak",
                        "__sched", "__visible"],
    "windows_calling_convention": ["WINAPI", "CALLBACK", "APIENTRY", "STDMETHODCALLTYPE", "STDAPICALLTYPE"],
}
PILOT_DERIVED_PROJECT = ["MagickExport", "FLAC_API", "R_API", "PHPAPI", "STBIDEF", "HIDDEN", "NOINLINE"]


def masker(words):
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, sorted(words, key=len, reverse=True))) + r")\b")
    return lambda source: pattern.sub(lambda match: " " * len(match.group(0)), source)


def measure(rows, variants):
    report = {}
    for name, mask in variants.items():
        counts = Counter()
        for row in rows:
            masked = mask(row["source_canonical"])
            if len(masked.encode("utf-8")) != len(row["source_canonical"].encode("utf-8")):
                raise AssertionError("masking must preserve byte offsets")
            tree = select_c_or_cpp(masked, row.get("language_metadata"))
            counts[tree.language, tree.successful] += 1
        report[name] = {
            "n": len(rows),
            "parse_ok_fraction": sum(v for (_, ok), v in counts.items() if ok) / len(rows),
            "by_selected_language": {lang: {"ok": counts[lang, True], "n": counts[lang, True] + counts[lang, False]}
                                     for lang in ("c", "cpp")},
        }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", default="data/interim/primevul/records.jsonl")
    parser.add_argument("--pilot", default="artifacts/audits/extraction_pilot_500.json")
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--output", default="artifacts/audits/annotation_masking_diagnostic.json")
    args = parser.parse_args()
    sources = json.loads(Path("artifacts/environment/development_sources.json").read_text())
    tokenizer = CanonicalTokenizer(sources["codebert_path"])
    pilot_ids = {s["sample_id"] for s in json.loads(Path(args.pilot).read_text(encoding="utf-8"))["samples"]}

    pilot_rows, candidates = [], []
    for row in read_jsonl(args.records):
        if row["original_split"] != "train":
            continue
        if row["sample_id"] in pilot_ids:
            pilot_rows.append(row)
        else:
            candidates.append((hash_uniform("extraction-heldout-v1", row["sample_id"]), row))
    candidates.sort(key=lambda item: item[0])
    heldout_rows = []
    for _, row in candidates:
        source = row["source_canonical"]
        if source.strip() and tokenizer.encode(source).original_bpe_length <= 510:
            heldout_rows.append(row)
            if len(heldout_rows) >= args.count:
                break

    a_priori = [word for words in A_PRIORI.values() for word in words]
    variants = {"baseline": lambda source: source, "a_priori": masker(a_priori),
                "a_priori_plus_pilot_project": masker(a_priori + PILOT_DERIVED_PROJECT)}
    report = {
        "status": "diagnostic_only_extractor_unchanged",
        "metric": "selected tree has no error/missing node (equals AST nonempty on the registered pilot)",
        "a_priori_words": A_PRIORI,
        "pilot_derived_project_words": PILOT_DERIVED_PROJECT,
        "samples": {"pilot": {"salt": "extraction-pilot-v1", "results": measure(pilot_rows, variants)},
                    "heldout": {"salt": "extraction-heldout-v1", "excludes_pilot_ids": True,
                                "results": measure(heldout_rows, variants)}},
    }
    atomic_write_json(args.output, report)
    print(json.dumps({k: {v: r["parse_ok_fraction"] for v, r in s["results"].items()}
                      for k, s in report["samples"].items()}, indent=2))


if __name__ == "__main__":
    main()
