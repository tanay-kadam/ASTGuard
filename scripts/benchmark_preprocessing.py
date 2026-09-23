"""Measure uncached, cold-cache, and warm-cache structural preprocessing."""
from __future__ import annotations

import argparse
import dataclasses
import json
import statistics
import sys
import time
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from astguard.alignment.tokenizer import CanonicalTokenizer
from astguard.data.cache import FeatureCache
from astguard.data.preprocess import _preprocessing_hash,preprocess_record
from astguard.data.schema import SampleRecord,read_jsonl
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import hash_uniform,sha256_file


def _summary(values):
    ordered=sorted(values)
    return {"mean_seconds":statistics.mean(values),"median_seconds":statistics.median(values),
            "p95_seconds":ordered[min(len(ordered)-1,int(.95*len(ordered)))],
            "total_seconds":sum(values),"items_per_second":len(values)/sum(values)}


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument("--records",required=True)
    parser.add_argument("--checkpoint",required=True);parser.add_argument("--revision")
    parser.add_argument("--count",type=int,default=1000);parser.add_argument("--cache-root",default="data/cache/benchmarks")
    parser.add_argument("--role",choices=["train","test"],default="train")
    parser.add_argument("--output",required=True);args=parser.parse_args(argv)
    tokenizer=CanonicalTokenizer(args.checkpoint,args.revision)
    if args.role=="test":
        from astguard.protocol import verify_test_lock
        verify_test_lock()
    rows=[row for row in read_jsonl(args.records) if row.get("original_split","").lower()==args.role]
    buckets={index:[] for index in range(4)}
    def length_bin(value):return 0 if value<=128 else 1 if value<=256 else 2 if value<=510 else 3
    for row in rows:
        length=tokenizer.encode(row["source_canonical"],max_length=512).original_bpe_length
        buckets[length_bin(length)].append(row)
    per_bin=max(1,args.count//4);selected=[]
    for index in range(4):
        selected.extend(sorted(buckets[index],key=lambda row:hash_uniform("e8-fixed-sample-v1",row["sample_id"]))[:per_bin])
    if len(selected)<args.count:
        present={row["sample_id"] for row in selected}
        remainder=sorted((row for row in rows if row["sample_id"] not in present),
                         key=lambda row:hash_uniform("e8-fixed-sample-v1",row["sample_id"]))
        selected.extend(remainder[:args.count-len(selected)])
    rows=selected
    records=[SampleRecord.from_dict(row) for row in rows]
    if not records:raise ValueError("no train-only preprocessing benchmark records")
    preprocessing_hash=_preprocessing_hash(tokenizer.identity_hash,512,False,"leaf_path_radius4",False,"full_function","clean")
    cache_dir=Path(args.cache_root)/(preprocessing_hash+"-"+uuid.uuid4().hex[:8])
    cache=FeatureCache(cache_dir,preprocessing_hash)
    uncached=[];cold=[];warm=[]
    for record in records:
        start=time.perf_counter();preprocess_record(record,tokenizer);uncached.append(time.perf_counter()-start)
    for record in records:
        start=time.perf_counter()
        cache.get_or_build(record.raw_sha256,lambda record=record:dataclasses.asdict(preprocess_record(record,tokenizer)),
                           sample_id=record.sample_id)
        cold.append(time.perf_counter()-start)
    for record in records:
        start=time.perf_counter()
        cache.get_or_build(record.raw_sha256,lambda:(_ for _ in ()).throw(AssertionError("warm cache miss")),
                           sample_id=record.sample_id)
        warm.append(time.perf_counter()-start)
    report={"schema_version":"e8-preprocessing-v1",
            "scientific_result":args.role=="test" and len(records)==args.count and args.count>=1000,
            "information_boundary":args.role+"_only","sample_namespace":"e8-fixed-sample-v1","sample_count":len(records),
            "records_sha256":sha256_file(args.records),"preprocessing_hash":preprocessing_hash,
            "uncached_end_to_end":_summary(uncached),"cold_cache":_summary(cold),"warm_cache":_summary(warm),
            "cache_directory":str(cache_dir)}
    atomic_write_json(args.output,report);print(json.dumps(report,indent=2));return 0


if __name__=="__main__":raise SystemExit(main())
