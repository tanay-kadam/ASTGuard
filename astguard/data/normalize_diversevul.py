"""Stream the pinned standalone DiverseVul release into the common schema."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from astguard.data.adapters import _list
from astguard.data.schema import make_sample, read_jsonl
from astguard.utils.atomic_io import atomic_write_json


def normalize(source: Path, output: Path, batch_size: int = 4096) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / 'records.jsonl'
    parquet_path = output / 'records.parquet'
    counts: Counter = Counter()
    quarantine: list[dict] = []
    writer = None
    batch: list[dict] = []

    def flush() -> None:
        nonlocal writer
        if not batch:
            return
        table = pa.Table.from_pylist(batch)
        if writer is None:
            writer = pq.ParquetWriter(parquet_path, table.schema)
        writer.write_table(table)
        batch.clear()

    try:
        with json_path.open('w', encoding='utf-8', newline='\n') as handle:
            for index, row in enumerate(read_jsonl(source)):
                code, label = row.get('func'), row.get('target')
                if not isinstance(code, str) or type(label) not in (int, bool) or label not in (0, 1):
                    quarantine.append({'row_index': index, 'reason': 'missing_source_or_invalid_label'})
                    continue
                record = make_sample(dataset='diversevul', release='standalone', original_split='transfer',
                    source=code, label=label, original_row_index=index,
                    project_id=row.get('project'), commit_id=row.get('commit_id'),
                    cwe_ids=_list(row.get('cwe')), cve_ids=_list(row.get('cve')))
                encoded = record.to_dict()
                handle.write(json.dumps(encoded, sort_keys=True, ensure_ascii=False) + '\n')
                batch.append(encoded)
                counts['records'] += 1
                counts[f'label_{label}'] += 1
                if len(batch) >= batch_size:
                    flush()
        flush()
    finally:
        if writer is not None:
            writer.close()
    report = {'records': counts['records'], 'labels': {'0': counts['label_0'], '1': counts['label_1']},
              'quarantined': len(quarantine), 'source': str(source)}
    atomic_write_json(output / 'quarantine.json', quarantine)
    atomic_write_json(output / 'normalization_report.json', report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default='data/raw/diversevul/original/payload.jsonl')
    parser.add_argument('--output', default='data/interim/diversevul')
    args = parser.parse_args(argv)
    print(json.dumps(normalize(Path(args.source), Path(args.output)), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
