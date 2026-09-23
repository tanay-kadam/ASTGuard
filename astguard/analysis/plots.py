from __future__ import annotations

from html import escape
from pathlib import Path

from astguard.utils.atomic_io import atomic_write_text


def write_metric_svg(rows: list[dict], output: str | Path, metric: str = "average_precision") -> None:
    width, height = 640, max(160, 70 + 42 * len(rows))
    bars = []
    for index, row in enumerate(rows):
        value = row.get(metric)
        value = 0.0 if value is None else max(0.0, min(1.0, float(value)))
        y = 45 + index * 42
        bars.append(f'<text x="10" y="{y+15}" font-size="13">{escape(row["model_id"])}</text>')
        bars.append(f'<rect x="180" y="{y}" width="{400*value:.2f}" height="22" fill="#3b82f6"/>')
        bars.append(f'<text x="{190+400*value:.2f}" y="{y+16}" font-size="12">{value:.3f}</text>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="100%" height="100%" fill="white"/><text x="10" y="24" font-size="17">Smoke {escape(metric)}</text>{"".join(bars)}</svg>\n'
    atomic_write_text(output, svg)


def write_metric_figure(rows,output_stem,metric='average_precision_mean'):
    import os
    stem=Path(output_stem);stem.parent.mkdir(parents=True,exist_ok=True)
    cache=stem.parent/'.matplotlib-cache';cache.mkdir(parents=True,exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR',str(cache.resolve()))
    import matplotlib.pyplot as plt
    names=[row['model_id'] for row in rows];values=[0 if row.get(metric) is None else row[metric] for row in rows]
    errors=[0 if row.get(metric.replace('_mean','_sd')) is None else row[metric.replace('_mean','_sd')] for row in rows]
    figure,axis=plt.subplots(figsize=(max(6,len(rows)*1.1),4))
    axis.bar(names,values,yerr=errors,capsize=3,color='#3b82f6');axis.set_ylabel(metric);axis.set_ylim(0,1)
    axis.tick_params(axis='x',rotation=30);figure.tight_layout()
    for suffix in ('.png','.pdf','.svg'):figure.savefig(stem.with_suffix(suffix),dpi=200)
    plt.close(figure)
