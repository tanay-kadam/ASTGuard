"""Generate registered T1-T6/F1-F6 solely from stored result artifacts."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from astguard.analysis.aggregate import ResultAggregator
from astguard.analysis.claim_guards import supported_claims
from astguard.analysis.runner import read_rows
from astguard.utils.atomic_io import atomic_write_json,atomic_write_text
from astguard.utils.hashing import sha256_file


def _value(value):
    if value is None:return "NA"
    if isinstance(value,float):return f"{value:.6g}"
    if isinstance(value,(dict,list)):return json.dumps(value,sort_keys=True,separators=(",",":"))
    return str(value)


def write_table(rows,stem):
    if not rows:raise ValueError(f"no rows for {stem.name}")
    columns=sorted({key for row in rows for key in row})
    with stem.with_suffix(".csv").open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=columns);writer.writeheader();writer.writerows(rows)
    markdown=["| "+" | ".join(columns)+" |","|"+"|".join("---" for _ in columns)+"|"]
    latex=[r"\begin{tabular}{"+"l"*len(columns)+"}",r" & ".join(column.replace("_",r"\_") for column in columns)+r" \\","\hline"]
    for row in rows:
        values=[_value(row.get(column)) for column in columns]
        markdown.append("| "+" | ".join(value.replace("|",r"\|") for value in values)+" |")
        latex.append(" & ".join(value.replace("_",r"\_").replace("%",r"\%") for value in values)+r" \\")
    latex.append(r"\end{tabular}")
    atomic_write_text(stem.with_suffix(".md"),"\n".join(markdown)+"\n")
    atomic_write_text(stem.with_suffix(".tex"),"\n".join(latex)+"\n")


def _artifact_rows(spec):
    document=json.loads(Path(spec["path"]).read_text(encoding="utf-8"))
    if isinstance(document,list):return document
    value=document
    for key in spec.get("rows_key","").split("."):
        if key:value=value[key]
    if not isinstance(value,list):raise ValueError(f"{spec['path']} does not resolve to a row list")
    return value


def line_figure(rows,spec,stem):
    cache=stem.parent/".matplotlib-cache";cache.mkdir(exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR",str(cache.resolve()))
    import matplotlib.pyplot as plt
    groups={}
    for row in rows:groups.setdefault(str(row[spec["group"]]),[]).append((float(row[spec["x"]]),float(row[spec["y"]])))
    figure,axis=plt.subplots(figsize=(6.4,4.2))
    for name,points in sorted(groups.items()):
        points=sorted(points);axis.plot([x for x,_ in points],[y for _,y in points],marker="o",label=name)
    axis.set_xlabel(spec["x"]);axis.set_ylabel(spec["y"]);axis.legend();figure.tight_layout()
    for suffix in (".png",".pdf",".svg"):figure.savefig(stem.with_suffix(suffix),dpi=200)
    plt.close(figure)


def pr_pair_figure(rows,spec,stem):
    """Render F3 as PR curves and the paired logit-margin distribution."""
    pair_path=spec.get("pair_path")
    if not pair_path:
        return line_figure(rows,spec,stem)
    pair_rows=read_rows(pair_path)
    if not pair_rows:raise ValueError("F3 pair_path contains no paired margins")
    cache=stem.parent/".matplotlib-cache";cache.mkdir(exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR",str(cache.resolve()))
    import matplotlib.pyplot as plt
    figure,axes=plt.subplots(1,2,figsize=(11,4.2))
    curves={}
    for row in rows:
        curves.setdefault((str(row[spec["group"]]),int(row.get("seed",0))),[]).append(
            (float(row[spec["x"]]),float(row[spec["y"]])))
    seen=set()
    for (model,_seed),points in sorted(curves.items()):
        points=sorted(points)
        axes[0].plot([x for x,_ in points],[y for _,y in points],alpha=.7,
                     label=model if model not in seen else None)
        seen.add(model)
    axes[0].set_xlabel(spec["x"]);axes[0].set_ylabel(spec["y"]);axes[0].legend()
    models=sorted({str(row["model_id"]) for row in pair_rows})
    values=[[float(row["logit_margin"]) for row in pair_rows if str(row["model_id"])==model] for model in models]
    axes[1].boxplot(values,tick_labels=models,showfliers=False);axes[1].axhline(0,color="black",linewidth=.8)
    axes[1].set_ylabel("vulnerable - patched logit");axes[1].tick_params(axis="x",rotation=30)
    figure.tight_layout()
    for suffix in (".png",".pdf",".svg"):figure.savefig(stem.with_suffix(suffix),dpi=200)
    plt.close(figure)


def architecture_figure(stem):
    cache=stem.parent/".matplotlib-cache";cache.mkdir(exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR",str(cache.resolve()))
    import matplotlib.pyplot as plt
    figure,axis=plt.subplots(figsize=(10,3.2));axis.axis("off")
    boxes=[("CodeBERT hidden state\nhᵢ","$g_{ihr}=\\sigma(W_{hr}h_i+b_{hr})$"),
           ("Sparse relations\n$M^r_{ij}$","$S_{hij}=Q_iK_j^T/\\sqrt d+\\sum_r\\beta_{hr}g_{ihr}M^r_{ij}$"),
           ("Attention + encoder\nlayers","Function classifier\nlogit")]
    boxes[0]=("CodeBERT hidden state\n$h_i$","$g_{ihr}=\\sigma(W_{hr}h_i+b_{hr})$")
    for index,(top,bottom) in enumerate(boxes):
        x=.04+index*.32
        axis.text(x,.68,top,ha="left",va="center",bbox={"boxstyle":"round","fc":"#dbeafe","ec":"#2563eb"})
        axis.text(x,.25,bottom,ha="left",va="center",bbox={"boxstyle":"round","fc":"#f1f5f9","ec":"#475569"})
        if index<len(boxes)-1:axis.annotate("",xy=(x+.30,.48),xytext=(x+.22,.48),arrowprops={"arrowstyle":"->"})
    figure.tight_layout()
    for suffix in (".png",".pdf",".svg"):figure.savefig(stem.with_suffix(suffix),dpi=200)
    plt.close(figure)


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument("--plan",required=True);parser.add_argument("--output-dir",required=True)
    args=parser.parse_args(argv);plan=json.loads(Path(args.plan).read_text(encoding="utf-8"))
    required_tables={"T1","T3","T4","T5","T6"};required_figures={"F2","F3","F4","F5","F6"}
    if set(plan.get("tables",{}))!=required_tables or set(plan.get("figures",{}))!=required_figures:
        raise ValueError(f"plan must provide tables {sorted(required_tables)} and figures {sorted(required_figures)}")
    if not plan.get("main_predictions"):raise ValueError("plan must provide main_predictions for T2")
    output=Path(args.output_dir);tables=output/"tables";figures=output/"figures"
    tables.mkdir(parents=True,exist_ok=True);figures.mkdir(parents=True,exist_ok=True)
    provenance={}
    for name,spec in sorted(plan["tables"].items()):
        rows=_artifact_rows(spec);write_table(rows,tables/name)
        provenance[name]={"source":spec["path"],"sha256":sha256_file(spec["path"])}
    aggregator=ResultAggregator();seed_rows=aggregator.aggregate_predictions(plan["main_predictions"],tables/"T2.seed_rows.json")
    summary=aggregator.summarize_seeds(seed_rows);write_table(summary,tables/"T2")
    provenance["T2"]={"sources":[{"path":path,"sha256":sha256_file(path)} for path in plan["main_predictions"]]}
    architecture_figure(figures/"F1");provenance["F1"]={"source":"executable ASTGuard architecture definition"}
    for name,spec in sorted(plan["figures"].items()):
        rows=_artifact_rows(spec)
        (pr_pair_figure if name=="F3" else line_figure)(rows,spec,figures/name)
        provenance[name]={"source":spec["path"],"sha256":sha256_file(spec["path"]),
                          "x":spec["x"],"y":spec["y"],"group":spec["group"]}
        if spec.get("pair_path"):
            provenance[name]["pair_source"]={"path":spec["pair_path"],"sha256":sha256_file(spec["pair_path"])}
    claims={}
    if plan.get("claim_evidence"):
        evidence=json.loads(Path(plan["claim_evidence"]).read_text(encoding="utf-8"))
        claims=supported_claims(evidence);provenance["claim_evidence"]={"source":plan["claim_evidence"],
            "sha256":sha256_file(plan["claim_evidence"])}
    atomic_write_json(output/"claim_guard_results.json",claims)
    atomic_write_json(output/"provenance_map.json",provenance)
    atomic_write_json(output/"status.json",{"status":"complete","numeric_cells_are_artifact_derived":True,
        "supported_claims":claims,"tables":["T1","T2","T3","T4","T5","T6"],
        "figures":["F1","F2","F3","F4","F5","F6"]})
    print(output);return 0


if __name__=="__main__":raise SystemExit(main())
