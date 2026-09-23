from __future__ import annotations

import argparse
import dataclasses
import math
from urllib.parse import urlsplit
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from astguard.data.schema import SampleRecord, read_jsonl
from astguard.parsing.lexical import lexical_fingerprint, shingle_set
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_text


@dataclasses.dataclass(frozen=True)
class LinkEvidence:
    left: str
    right: str
    kind: str
    value: str


class _UnionFind:
    def __init__(self, values: Iterable[str]):
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: str, right: str) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            low, high = sorted((a, b))
            self.parent[high] = low


class LeakageAuditor:
    """Build deterministic dependence components from source-only linkage rules."""

    def __init__(self, jaccard_threshold: float = 0.90, length_ratio: float = 0.80):
        self.jaccard_threshold = jaccard_threshold
        self.length_ratio = length_ratio

    def build_components(self, records: list[SampleRecord]) -> tuple[dict[str, str], list[LinkEvidence]]:
        ids = [r.sample_id for r in records]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate sample_id")
        uf = _UnionFind(ids)
        evidence: list[LinkEvidence] = []

        def link_groups(kind: str, entries: Iterable[tuple[str, str]]) -> None:
            groups: dict[str, list[str]] = defaultdict(list)
            for value, sample_id in entries:
                if value:
                    groups[value].append(sample_id)
            for value, members in sorted(groups.items()):
                first = sorted(members)[0]
                for other in sorted(members)[1:]:
                    uf.union(first, other)
                    evidence.append(LinkEvidence(first, other, kind, value))

        lexical: dict[str, tuple[int, frozenset[str]]] = {}
        for record in records:
            try:
                fingerprint, tokens = lexical_fingerprint(record.source_canonical)
            except ValueError:
                fingerprint,tokens='',[]
            record.lexical_sha256 = fingerprint
            lexical[record.sample_id] = (len(tokens), shingle_set(tokens))
        link_groups("raw_sha256", ((r.raw_sha256, r.sample_id) for r in records))
        link_groups("lexical_sha256", ((r.lexical_sha256, r.sample_id) for r in records))
        link_groups("repository_commit", ((f"{project_identity(r)}@{r.commit_id.lower()}" if project_identity(r) and r.commit_id else "", r.sample_id) for r in records))
        link_groups("cve", ((cve, r.sample_id) for r in records for cve in r.cve_ids))
        link_groups("pair", ((pair, r.sample_id) for r in records for pair in r.pair_ids))

        # Global ordered prefix filtering: Jaccard >= t implies the prefixes of
        # length |S|-ceil(t*|S|)+1 intersect. Exact verification follows.
        frequency = defaultdict(int)
        for _, shingles in lexical.values():
            for shingle in shingles:
                frequency[shingle] += 1
        inverted: dict[str, list[str]] = defaultdict(list)
        for sample_id, (_, shingles) in lexical.items():
            prefix_length = len(shingles)-math.ceil(self.jaccard_threshold*len(shingles))+1
            for shingle in sorted(shingles,key=lambda x:(frequency[x],x))[:prefix_length]:
                inverted[shingle].append(sample_id)
        # Verify candidates while scanning buckets so the complete primary join
        # does not materialize a potentially enormous global pair set. Pairs
        # already joined by a previous prefix or metadata need no second edge.
        for shingle in sorted(inverted,key=lambda value:(frequency[value],value)):
            members=sorted(set(inverted[shingle]))
            for left_index,left in enumerate(members):
                for right in members[left_index+1:]:
                    if uf.find(left)==uf.find(right):continue
                    left_length,left_set=lexical[left];right_length,right_set=lexical[right]
                    ratio=min(left_length,right_length)/max(1,max(left_length,right_length))
                    if ratio<self.length_ratio or left_length<5 or right_length<5:continue
                    score=len(left_set & right_set)/max(1,len(left_set | right_set))
                    if score>=self.jaccard_threshold:
                        uf.union(left,right)
                        evidence.append(LinkEvidence(left,right,"near_clone",f"jaccard={score:.12g}"))

        members_by_root: dict[str, list[str]] = defaultdict(list)
        for sample_id in ids:
            members_by_root[uf.find(sample_id)].append(sample_id)
        mapping: dict[str, str] = {}
        for members in members_by_root.values():
            component_id = sha256_text("\n".join(sorted(members)))
            for sample_id in members:
                mapping[sample_id] = component_id
        return mapping, sorted(evidence, key=lambda x: (x.kind, x.left, x.right, x.value))


def normalize_repository(value: str | None) -> str:
    if not value:
        return ""
    normalized = value.strip().replace('\\','/').rstrip('/')
    if normalized.startswith('git@') and ':' in normalized:
        normalized = normalized[4:].replace(':','/',1)
    parsed = urlsplit(normalized if '://' in normalized else 'https://'+normalized)
    normalized = (parsed.hostname or '').lower() + parsed.path
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    return normalized.rstrip("/")


def project_identity(record: SampleRecord) -> str:
    """Use the supplied project name when a release omits repository URLs."""
    if record.repository_url:
        return normalize_repository(record.repository_url)
    return (record.project_id or '').strip().lower()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", required=True, nargs='+')
    parser.add_argument("--output", default="artifacts/audits/components.json")
    args = parser.parse_args(argv)
    records = [SampleRecord.from_dict(row) for path in args.records for row in read_jsonl(path)]
    mapping, evidence = LeakageAuditor().build_components(records)
    atomic_write_json(args.output, {"components": mapping, "evidence": [dataclasses.asdict(e) for e in evidence]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
