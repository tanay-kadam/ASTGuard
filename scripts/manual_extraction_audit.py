"""Create and score the human-reviewed extraction release-gate pack.

The preparation command never fills gold labels. Reviewers must author the
expected projected DFG edges and span verdicts independently of the extractor.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astguard.alignment.projection import RelationProjector
from astguard.data.schema import read_jsonl, write_jsonl
from astguard.utils.atomic_io import atomic_write_json, atomic_write_text
from astguard.utils.hashing import hash_uniform, sha256_file

EDGE_SEMANTICS = """\
Record directed scalar dependencies as `[consumer_id, source_id]` using the identifier token ids below.

- A read `u` of a local scalar or parameter links `[u, d]` to every definition `d` of that binding that can reach it
  (declaration with initializer, assignment, `++`/`--`, compound assignment, or the parameter declarator).
- A new assignment/definition occurrence `d_new` links `[d_new, r]` to every scalar read `r` in its right-hand side.
  Compound assignment and increment read the old value before writing, so `i++` or `i += n` inside a loop
  can give a self-edge `[k, k]` (the read at token `k` reached by the write at `k` from the previous iteration).
- Pointer, array, and member expressions contribute only their scalar base/index reads; do not add memory or alias edges.
- Calls contribute only scalar argument reads; no callee effects or return provenance.
- Type names, function names, member selectors, and unknown globals have no bindings or edges.
  Keywords such as `return` appear in the token table because the lexer tags them as identifiers; they never have edges.
- Branches, loops, `break`, `continue`, and `return` follow normal control flow; loop back edges can carry definitions.
"""


def prepare(args) -> dict:
    records = {row["sample_id"]: row for row in read_jsonl(args.records)}
    features = {row["sample_id"]: row for row in read_jsonl(args.features)}
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    roles = dict(zip(manifest["ordered_sample_ids"], manifest["roles"]))
    candidates = []
    for sample_id, feature in features.items():
        record = records.get(sample_id)
        if record is None or roles.get(sample_id) != "train" or feature.get("dfg_status") != "ok":
            continue
        language = feature.get("language_selected")
        if language not in {"c", "cpp"}:
            continue
        candidates.append((hash_uniform("manual-extraction-audit-v1", sample_id), language, sample_id))
    candidates.sort()
    chosen = []
    target_each = args.count // 2
    counts = Counter()
    for _, language, sample_id in candidates:
        if counts[language] < target_each:
            chosen.append(sample_id)
            counts[language] += 1
    for _, language, sample_id in candidates:
        if len(chosen) >= args.count:
            break
        if sample_id not in set(chosen):
            chosen.append(sample_id)
            counts[language] += 1
    if len(chosen) < args.count:
        raise ValueError(f"only {len(chosen)} supported train-only C/C++ functions are available")
    rows = []
    for sample_id in chosen:
        record, feature = records[sample_id], features[sample_id]
        rows.append({"audit_schema": "manual-extraction-v1", "sample_id": sample_id,
                     "language": feature["language_selected"], "source": record["source_canonical"],
                     "offsets_byte": feature["offsets_byte"], "special_tokens_mask": feature["special_tokens_mask"],
                     "lexical_nodes": feature["lexical_nodes"],
                     "extractor_projected_dfg_edges": feature["dfg_token_edges"],
                     "review": {"review_status": "unreviewed", "reviewer_ids": [],
                                "span_alignment_ok": None, "gold_projected_dfg_edges": None,
                                "notes": ""}})
    write_jsonl(args.output, rows)
    report = {"status": "prepared_not_reviewed", "count": len(rows), "language_counts": dict(counts),
              "records_sha256": sha256_file(args.records), "features_sha256": sha256_file(args.features),
              "manifest_sha256": sha256_file(args.manifest), "pack_sha256": sha256_file(args.output),
              "information_boundary": "train_only"}
    atomic_write_json(Path(args.output).with_suffix(".manifest.json"), report)
    return report


def _position(source: str, char: int) -> str:
    line = source.count("\n", 0, char) + 1
    return f"{line}:{char - (source.rfind(chr(10), 0, char) + 1) + 1}"


def worksheet(args) -> dict:
    """Write blind per-function review sheets; extractor edges are deliberately omitted."""
    rows = list(read_jsonl(args.pack))
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    template = {}
    for number, row in enumerate(rows, 1):
        source = row["source"]
        raw = source.encode("utf-8")
        identifiers = [node for node in row["lexical_nodes"] if node["kind"] == "identifier"]
        lines = [f"# Review {number:02d}: `{row['sample_id']}` ({row['language']})", "",
                 "Author edges from the source alone. Do not open the pack file or any extractor output.", "",
                 EDGE_SEMANTICS, "## Source", "", "```" + ("cpp" if row["language"] == "cpp" else "c")]
        lines += [f"{index:4d} | {text}" for index, text in enumerate(source.split("\n"), 1)]
        lines += ["```", "", "## Identifier tokens", "", "| id | text | line:col |", "|---|---|---|"]
        lines += [f"| {node['id']} | `{node['text']}` | {_position(source, node['start_char'])} |" for node in identifiers]
        lines += ["", "## BPE span check", "",
                  "Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.", "",
                  "| bpe index | source bytes |", "|---|---|"]
        for index, ((start, end), special) in enumerate(zip(row["offsets_byte"], row["special_tokens_mask"])):
            if not special and end > start:
                lines.append(f"| {index} | `{raw[start:end].decode('utf-8', 'replace')!r}` |")
        atomic_write_text(output / f"{number:02d}_{row['sample_id'].replace(':', '_')}.md", "\n".join(lines) + "\n")
        template[row["sample_id"]] = {"dfg_edges": None, "span_alignment_ok": None, "reviewer_ids": [], "notes": ""}
    atomic_write_json(output / "gold_template.json", template)
    atomic_write_text(output / "README.md", "# Manual extraction review\n\n"
                      "Copy `gold_template.json` to `gold.json`. For each function, fill `dfg_edges` "
                      "(an empty list is valid), `span_alignment_ok`, and `reviewer_ids`, using only the "
                      "matching worksheet. Then run `manual_extraction_audit.py import` and `evaluate`.\n\n"
                      + EDGE_SEMANTICS)
    return {"status": "worksheets_written", "count": len(rows), "output_dir": str(output),
            "pack_sha256": sha256_file(args.pack)}


def import_gold(args) -> dict:
    """Project reviewer lexical edges onto BPE indices with the registered projector."""
    rows = list(read_jsonl(args.pack))
    features = {row["sample_id"]: row for row in read_jsonl(args.features)}
    gold = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    reviewed = []
    for row in rows:
        entry = gold.get(row["sample_id"])
        if entry is None:
            raise ValueError(f"gold file has no entry for {row['sample_id']}")
        if entry.get("dfg_edges") is None or entry.get("span_alignment_ok") is None or not entry.get("reviewer_ids"):
            raise ValueError(f"incomplete gold entry for {row['sample_id']}")
        identifiers = {node["id"] for node in row["lexical_nodes"] if node["kind"] == "identifier"}
        edges = [tuple(int(v) for v in edge) for edge in entry["dfg_edges"]]
        for consumer, source in edges:
            if consumer not in identifiers or source not in identifiers:
                raise ValueError(f"{row['sample_id']}: edge {[consumer, source]} must join identifier ids")
        feature = features[row["sample_id"]]
        if feature["offsets_byte"] != row["offsets_byte"]:
            raise ValueError(f"{row['sample_id']}: features do not match the pack")
        leaf_to_bpe = {int(key): value for key, value in feature["leaf_to_bpe"].items()}
        projected, _ = RelationProjector().project(edges, leaf_to_bpe, symmetric=False)
        reviewed.append(row | {"review": {"review_status": "complete", "reviewer_ids": list(entry["reviewer_ids"]),
                                          "span_alignment_ok": bool(entry["span_alignment_ok"]),
                                          "gold_lexical_dfg_edges": [list(edge) for edge in sorted(set(edges))],
                                          "gold_projected_dfg_edges": [list(edge) for edge in projected],
                                          "notes": entry.get("notes", "")}})
    write_jsonl(args.output, reviewed)
    return {"status": "imported", "count": len(reviewed), "gold_sha256": sha256_file(args.gold),
            "reviewed_pack_sha256": sha256_file(args.output)}


def evaluate(args) -> dict:
    rows = list(read_jsonl(args.pack))
    if len(rows) < args.minimum_count:
        raise ValueError(f"audit requires at least {args.minimum_count} rows")
    tp = fp = fn = 0
    span_failures = 0
    reviewers = set()
    for row in rows:
        review = row.get("review", {})
        if review.get("review_status") != "complete":
            raise ValueError(f"sample {row.get('sample_id')} is not independently reviewed")
        gold = review.get("gold_projected_dfg_edges")
        if gold is None or review.get("span_alignment_ok") is None:
            raise ValueError(f"sample {row.get('sample_id')} has incomplete gold fields")
        reviewers.update(review.get("reviewer_ids", []))
        predicted = {tuple(edge) for edge in row["extractor_projected_dfg_edges"]}
        expected = {tuple(edge) for edge in gold}
        tp += len(predicted & expected)
        fp += len(predicted - expected)
        fn += len(expected - predicted)
        span_failures += not bool(review["span_alignment_ok"])
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    passed = precision is not None and recall is not None and precision >= .90 and recall >= .80 and span_failures == 0
    result = {"status": "passed" if passed else "failed", "schema_version": "manual-extraction-gate-v1",
              "reviewed_count": len(rows), "reviewer_count": len(reviewers),
              "two_reviewer_preference_met": len(reviewers) >= 2,
              "true_positive_edges": tp, "false_positive_edges": fp, "false_negative_edges": fn,
              "projected_edge_precision": precision, "projected_edge_recall": recall,
              "span_alignment_failures": span_failures, "required_precision": .90,
              "required_recall": .80, "pack_sha256": sha256_file(args.pack)}
    atomic_write_json(args.output, result)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    make = subparsers.add_parser("prepare")
    make.add_argument("--records", required=True)
    make.add_argument("--features", required=True)
    make.add_argument("--manifest", required=True)
    make.add_argument("--count", type=int, default=50,
                      help="50 satisfies the independent byte/span gate and exceeds the 30-edge minimum")
    make.add_argument("--output", required=True)
    sheets = subparsers.add_parser("worksheet")
    sheets.add_argument("--pack", required=True)
    sheets.add_argument("--output-dir", required=True)
    load = subparsers.add_parser("import")
    load.add_argument("--pack", required=True)
    load.add_argument("--features", required=True, help="feature rows used to prepare the pack")
    load.add_argument("--gold", required=True)
    load.add_argument("--output", required=True)
    score = subparsers.add_parser("evaluate")
    score.add_argument("--pack", required=True)
    score.add_argument("--minimum-count", type=int, default=50)
    score.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    commands = {"prepare": prepare, "worksheet": worksheet, "import": import_gold, "evaluate": evaluate}
    result = commands[args.command](args)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
