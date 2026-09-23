from __future__ import annotations

import argparse
import dataclasses
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from astguard.data.audit import LinkEvidence, normalize_repository
from astguard.data.schema import SampleRecord, SplitManifest, read_jsonl
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import hash_uniform, object_hash


_PRIORITY = {"train": 0, "tune": 1, "cal": 2, "test": 3}


class SplitBuilder:
    def freeze(
        self, records: list[SampleRecord], components: dict[str, str],
        evidence: Iterable[LinkEvidence] = (), view: str = "P_clean", version: str = "1.0",
    ) -> SplitManifest:
        if view == "P_clean":
            roles, exclusions = self._p_clean(records, components)
        elif view == "P_project":
            roles, exclusions = self._p_project(records, components)
        elif view == "D_transfer":
            roles, exclusions = self._d_transfer(records, components)
        else:
            raise ValueError(f"unsupported view {view}")
        kept = sorted((r for r in records if r.sample_id in roles), key=lambda r: r.sample_id)
        role_values = [roles[r.sample_id] for r in kept]
        manifest = SplitManifest(
            view=view, version=version, source_hashes=sorted({r.raw_sha256 for r in records}),
            rule_hash=object_hash({"view": view, "version": version}),
            ordered_sample_ids=[r.sample_id for r in kept],
            component_ids=[components[r.sample_id] for r in kept],
            original_splits=[r.original_split for r in kept], roles=role_values,
            exclusion_reasons=exclusions,
            link_evidence=[dataclasses.asdict(e) for e in evidence],
            counts=dict(sorted(Counter(role_values).items())),
        )
        manifest.file_hash = object_hash(dataclasses.asdict(manifest) | {"file_hash": ""})
        self._validate(manifest)
        return manifest

    def _p_clean(self, records: list[SampleRecord], components: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
        by_component: dict[str, list[SampleRecord]] = defaultdict(list)
        for record in records:
            by_component[components[record.sample_id]].append(record)
        roles: dict[str, str] = {}
        exclusions: dict[str, str] = {}
        for component, members in by_component.items():
            splits = {r.original_split.lower() for r in members}
            touches_test = "test" in splits
            touches_validation = bool(splits & {"valid", "validation", "val"})
            for record in members:
                split = record.original_split.lower()
                if split == "test":
                    roles[record.sample_id] = "test"
                elif split in {"valid", "validation", "val"}:
                    if touches_test:
                        exclusions[record.sample_id] = "validation_component_intersects_test"
                    else:
                        roles[record.sample_id] = "tune" if hash_uniform("validation-v1", component) < 0.5 else "cal"
                elif split == "train":
                    if touches_test or touches_validation:
                        exclusions[record.sample_id] = "train_component_intersects_validation_or_test"
                    else:
                        roles[record.sample_id] = "train"
                else:
                    exclusions[record.sample_id] = f"unknown_original_split:{record.original_split}"
        return roles, exclusions

    def _d_transfer(self, records: list[SampleRecord], components: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
        """Only independent standalone DiverseVul components enter transfer."""
        prime_components = {components[r.sample_id] for r in records if r.dataset == 'primevul'}
        roles: dict[str, str] = {}
        exclusions: dict[str, str] = {}
        for record in records:
            if record.dataset != 'diversevul':
                exclusions[record.sample_id] = 'source_dataset_not_transfer_cohort'
            elif components[record.sample_id] in prime_components:
                exclusions[record.sample_id] = 'component_intersects_any_primevul_split'
            else:
                roles[record.sample_id] = 'transfer'
        return roles, exclusions

    def _p_project(self, records: list[SampleRecord], components: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
        provisional: dict[str, str] = {}
        exclusions: dict[str, str] = {}
        for record in records:
            project = record.project_id or normalize_repository(record.repository_url)
            if not project:
                exclusions[record.sample_id] = "unknown_project"
                continue
            value = hash_uniform("project-v1", project)
            provisional[record.sample_id] = "train" if value < .7 else "tune" if value < .8 else "cal" if value < .9 else "test"
        target_by_component: dict[str, str] = {}
        for sample_id, role in provisional.items():
            component = components[sample_id]
            if component not in target_by_component or _PRIORITY[role] > _PRIORITY[target_by_component[component]]:
                target_by_component[component] = role
        roles: dict[str, str] = {}
        for sample_id, role in provisional.items():
            target = target_by_component[components[sample_id]]
            if role == target:
                roles[sample_id] = role
            else:
                exclusions[sample_id] = f"component_cross_partition_purged_to_{target}"
        return roles, exclusions

    @staticmethod
    def _validate(manifest: SplitManifest) -> None:
        if not (len(manifest.ordered_sample_ids) == len(manifest.component_ids) == len(manifest.roles)):
            raise ValueError("manifest columns have inconsistent lengths")
        seen: dict[str, str] = {}
        for component, role in zip(manifest.component_ids, manifest.roles):
            if component in seen and seen[component] != role:
                raise ValueError(f"component leakage between {seen[component]} and {role}")
            seen[component] = role


def component_fraction(component_id: str, fraction: float) -> bool:
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0,1]")
    return hash_uniform("fraction-v1", component_id) < fraction


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", required=True, nargs='+')
    parser.add_argument("--components", required=True)
    parser.add_argument("--view", default="P_clean")
    parser.add_argument("--output", default="artifacts/audits/split_manifest.json")
    parser.add_argument("--protocol")
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args(argv)
    import json
    records = [SampleRecord.from_dict(row) for path in args.records for row in read_jsonl(path)]
    component_doc = json.loads(Path(args.components).read_text(encoding="utf-8"))
    manifest = SplitBuilder().freeze(records, component_doc["components"], view=args.view)
    atomic_write_json(args.output, dataclasses.asdict(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
