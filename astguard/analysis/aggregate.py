from __future__ import annotations

import json
import csv
import statistics
from collections import defaultdict
from pathlib import Path

from astguard.evaluation.metrics import evaluate_scores,threshold_metrics
from astguard.utils.atomic_io import atomic_write_json, atomic_write_text
from astguard.utils.hashing import sha256_file


class ResultAggregator:
    def aggregate_predictions(self, prediction_files: list[str | Path], output: str | Path) -> list[dict]:
        groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
        group_hashes: dict[tuple[str, int], set[str]] = defaultdict(set)
        population_reference = None
        label_reference = None
        for path in prediction_files:
            from astguard.analysis.runner import read_rows
            rows = read_rows(path)
            if not rows:
                raise ValueError(f"empty prediction artifact: {path}")
            required={"sample_id","label","probability","model_id","seed","split_hash","config_hash",
                      "checkpoint_hash","feature_hash","role","metric_version"}
            if any(required-set(row) for row in rows):
                raise ValueError(f"prediction artifact lacks common-schema provenance: {path}")
            ids=[row["sample_id"] for row in rows]
            if len(ids)!=len(set(ids)):raise ValueError(f"duplicate prediction IDs in {path}")
            population=(rows[0]["view"],rows[0]["role"],rows[0]["split_hash"],tuple(sorted(ids)))
            labels={row["sample_id"]:int(row["label"]) for row in rows}
            if any((row["view"],row["role"],row["split_hash"])!=population[:3] for row in rows):
                raise ValueError(f"mixed view/role/split provenance in {path}")
            if population_reference is None:population_reference=population;label_reference=labels
            elif population!=population_reference or labels!=label_reference:
                raise ValueError("prediction populations or labels differ across compared artifacts")
            file_hash=sha256_file(path)
            for row in rows:
                key=(row["model_id"], int(row["seed"]))
                groups[key].append(row);group_hashes[key].add(file_hash)
        results = []
        for (model, seed), rows in sorted(groups.items()):
            if len({row["sample_id"] for row in rows}) != len(rows):
                raise ValueError(f"duplicate prediction IDs or multiple artifacts for {model}/{seed}")
            for field in ("split_hash","config_hash","checkpoint_hash","feature_hash","metric_version","role"):
                if len({row[field] for row in rows})!=1:raise ValueError(f"mixed {field} for {model}/{seed}")
            labels=[int(row['label']) for row in rows];scores=[float(row['probability']) for row in rows]
            metric=evaluate_scores(labels,scores)
            if all('max_f1' in row.get('decisions',{}) for row in rows):
                metric.update(threshold_metrics(labels,[row['decisions']['max_f1'] for row in rows]))
                metric['threshold']='saved:max_f1'
            results.append({"model_id": model, "seed": seed, **metric,
                            "split_hash":rows[0]["split_hash"],"config_hash":rows[0]["config_hash"],
                            "checkpoint_hash":rows[0]["checkpoint_hash"],"feature_hash":rows[0]["feature_hash"],
                            "metric_version":rows[0]["metric_version"],"role":rows[0]["role"],
                            "prediction_hashes": sorted(group_hashes[(model,seed)])})
        atomic_write_json(output, results)
        return results

    def summarize_seeds(self,rows):
        grouped=defaultdict(list)
        for row in rows:grouped[row['model_id']].append(row)
        result=[]
        for model,items in sorted(grouped.items()):
            entry={'model_id':model,'seeds':sorted(row['seed'] for row in items),'seed_count':len(items)}
            for metric in ('average_precision','roc_auc','f1','mcc','recall','fpr'):
                values=[float(row[metric]) for row in items if row.get(metric) is not None]
                entry[metric+'_mean']=statistics.mean(values) if values else None
                entry[metric+'_sd']=statistics.stdev(values) if len(values)>1 else None
            entry['run_prediction_hashes']=sorted({value for row in items for value in row.get('prediction_hashes',[])})
            result.append(entry)
        return result

    def write_summary_tables(self,summary,output_dir):
        output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
        atomic_write_json(output/'summary.json',summary)
        columns=['model_id','seed_count','average_precision_mean','average_precision_sd','roc_auc_mean','f1_mean','mcc_mean']
        with (output/'summary.csv').open('w',encoding='utf-8',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=columns,extrasaction='ignore');writer.writeheader();writer.writerows(summary)
        def shown(value):return 'NA' if value is None else f'{value:.4f}' if isinstance(value,float) else str(value)
        markdown=['| Model | Seeds | AP mean | AP SD | ROC-AUC | F1 | MCC |','|---|---:|---:|---:|---:|---:|---:|']
        latex=['\\begin{tabular}{lrrrrrr}',r'Model & Seeds & AP & AP SD & ROC-AUC & F1 & MCC \\','\\hline']
        for row in summary:
            values=[row['model_id'],row['seed_count'],row['average_precision_mean'],row['average_precision_sd'],row['roc_auc_mean'],row['f1_mean'],row['mcc_mean']]
            markdown.append('| '+' | '.join(shown(v) for v in values)+' |')
            latex.append(' & '.join(shown(v).replace('_',r'\_') for v in values)+r' \\')
        latex.append('\\end{tabular}')
        atomic_write_text(output/'summary.md','\n'.join(markdown)+'\n');atomic_write_text(output/'summary.tex','\n'.join(latex)+'\n')

    def build_markdown_table(self, rows: list[dict], output: str | Path) -> None:
        lines = ["| Model | Seed | N | AP | ROC-AUC | F1 |", "|---|---:|---:|---:|---:|---:|"]
        for row in rows:
            def value(key):
                item = row.get(key)
                return "NA" if item is None else f"{item:.4f}" if isinstance(item, float) else str(item)
            lines.append(f"| {row['model_id']} | {row['seed']} | {row['count']} | {value('average_precision')} | {value('roc_auc')} | {value('f1')} |")
        atomic_write_text(output, "\n".join(lines) + "\n")
