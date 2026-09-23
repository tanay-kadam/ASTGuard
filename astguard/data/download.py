from __future__ import annotations

import argparse
import json
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file


OFFICIAL = {
    "primevul": "https://github.com/DLVulDet/PrimeVul",
    "diversevul": "https://github.com/wagner-group/diversevul",
    "codexglue": "https://github.com/microsoft/CodeXGLUE/tree/main/Code-Code/Defect-detection",
}

PRIMEVUL_FILES = {
    'primevul_train.jsonl':'1qRO_Qdy7KXcZbJJAu5J3VZWkRVvT4Kbu',
    'primevul_valid.jsonl':'1CMQ185Ww_bsBWGbJe4sZW0vzceWnmNE7',
    'primevul_test.jsonl':'1fVybeCHhFfBMOHQ5rGSA-mzu9Egri38H',
    'primevul_train_paired.jsonl':'1CYE_AZdZTIHPepOIxmPNZtMPdwB6cEt1',
    'primevul_valid_paired.jsonl':'1UBoDzBD9tXAieRlXYjjB-2HpPf9I83mg',
    'primevul_test_paired.jsonl':'1rNDKb65Yn1rCBURzHeBcH4jVVdQ1oD4r',
}

DIVERSEVUL_FILE_ID='12IWKhmLhq7qn5B_iXgn5YerOQtkH-6RG'


def acquire_primevul(lock_path):
    import gdown
    lock_path=Path(lock_path)
    lock=json.loads(lock_path.read_text()) if lock_path.exists() else {'schema_version':1,'sources':[]}
    for name,file_id in PRIMEVUL_FILES.items():
        target=Path('data/raw/primevul/original')/name
        target.parent.mkdir(parents=True,exist_ok=True)
        logical='primevul/'+name
        registered=next((row for row in lock['sources'] if row['logical_name']==logical),None)
        if registered:
            if target.exists():
                if sha256_file(target)!=registered['sha256']:
                    raise ValueError(f'registered source changed: {target}')
                continue
        if target.exists():
            raise ValueError(f'unregistered existing payload: {target}; import with an explicit checksum')
        partial=target.with_suffix('.partial')
        url=f'https://drive.google.com/uc?id={file_id}'
        gdown.download(url,str(partial),quiet=False)
        if registered and sha256_file(partial)!=registered['sha256']:
            partial.unlink(missing_ok=True)
            raise ValueError(f'registered source checksum mismatch: {target}')
        count=0
        with partial.open(encoding='utf-8') as handle:
            for line in handle:
                row=json.loads(line)
                if not isinstance(row,dict): raise ValueError('expected JSON object')
                count+=1
        if registered and registered.get('rows') is not None and count!=registered['rows']:
            partial.unlink(missing_ok=True)
            raise ValueError(f'registered source row count mismatch: {target}')
        partial.replace(target)
        if registered:
            continue
        lock['sources'].append({'logical_name':logical,'release':'original','official_landing_url':OFFICIAL['primevul'],
            'resolved_download_url':url,'upstream_revision':'6f54687c84947b1d17486495440b37030d147289',
            'retrieved_utc':datetime.now(timezone.utc).isoformat(),'bytes':target.stat().st_size,'sha256':sha256_file(target),
            'rows':count,'license_access_notes':'PrimeVul MIT; underlying project source licenses apply',
            'local_immutable_path':str(target.resolve())})
        atomic_write_json(lock_path,lock)


def acquire_diversevul(lock_path):
    import gdown
    path=Path('data/raw/diversevul/original/payload.jsonl')
    path.parent.mkdir(parents=True,exist_ok=True)
    lock_path=Path(lock_path)
    lock=json.loads(lock_path.read_text()) if lock_path.exists() else {'schema_version':1,'sources':[]}
    logical='diversevul/standalone'
    known=next((row for row in lock['sources'] if row['logical_name']==logical),None)
    if known:
        if path.exists():
            if sha256_file(path)!=known['sha256']:raise ValueError('registered DiverseVul payload changed')
            return
    if path.exists():raise ValueError('existing DiverseVul payload not registered')
    url='https://drive.google.com/uc?id='+DIVERSEVUL_FILE_ID
    partial=path.with_suffix('.partial')
    gdown.download(url,str(partial),quiet=False)
    if known and sha256_file(partial)!=known['sha256']:
        partial.unlink(missing_ok=True)
        raise ValueError('registered DiverseVul payload checksum mismatch')
    count=0
    with partial.open(encoding='utf-8') as handle:
        for line in handle:
            if not isinstance(json.loads(line),dict):raise ValueError('DiverseVul row must be a JSON object')
            count+=1
    if known and known.get('rows') is not None and count!=known['rows']:
        partial.unlink(missing_ok=True)
        raise ValueError('registered DiverseVul payload row count mismatch')
    partial.replace(path)
    if known:
        return
    lock['sources'].append({'logical_name':logical,'release':'standalone','official_landing_url':OFFICIAL['diversevul'],
        'resolved_download_url':url,'upstream_revision':'official standalone release','retrieved_utc':datetime.now(timezone.utc).isoformat(),
        'bytes':path.stat().st_size,'sha256':sha256_file(path),'rows':count,'license_access_notes':'verify dataset upstream rights',
        'local_immutable_path':str(path.resolve())})
    atomic_write_json(lock_path,lock)


def acquire(dataset: str, destination: str | Path, *, manual_path: str | Path | None = None, url: str | None = None, expected_sha256: str | None = None) -> dict:
    if dataset not in OFFICIAL:
        raise ValueError(f"unknown dataset {dataset}")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if manual_path:
        source = Path(manual_path)
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copyfile(source, destination)
        resolved = str(source.resolve())
    elif url:
        with urllib.request.urlopen(url) as response, destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        resolved = url
    else:
        raise RuntimeError(f"No immutable payload URL is embedded. Obtain the official {dataset} release from {OFFICIAL[dataset]} and pass --manual-path.")
    checksum = sha256_file(destination)
    if expected_sha256 and checksum != expected_sha256:
        destination.unlink(missing_ok=True)
        raise ValueError(f"checksum mismatch: expected {expected_sha256}, got {checksum}")
    return {
        "logical_name": dataset, "official_landing_url": OFFICIAL[dataset], "resolved_download_url": resolved,
        "release": "user-specified", "upstream_revision": None,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(), "bytes": destination.stat().st_size,
        "sha256": checksum, "license_access_notes": "Verify upstream terms before redistribution",
        "local_immutable_path": str(destination.resolve()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=sorted(OFFICIAL))
    parser.add_argument("--release", default="original")
    parser.add_argument("--manual-path")
    parser.add_argument("--url")
    parser.add_argument("--sha256")
    parser.add_argument("--destination")
    parser.add_argument("--lock", default="sources.lock.json")
    args = parser.parse_args(argv)
    if args.dataset=='primevul' and args.release=='original' and not args.manual_path and not args.url:
        acquire_primevul(args.lock)
        return 0
    if args.dataset=='diversevul' and not args.manual_path and not args.url:
        acquire_diversevul(args.lock)
        return 0
    destination = args.destination or f"data/raw/{args.dataset}/{args.release}/payload.jsonl"
    entry = acquire(args.dataset, destination, manual_path=args.manual_path, url=args.url, expected_sha256=args.sha256)
    entry["release"] = args.release
    lock_path = Path(args.lock)
    lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.exists() else {"schema_version": 1, "sources": []}
    lock["sources"] = [x for x in lock["sources"] if not (x["logical_name"] == args.dataset and x["release"] == args.release)] + [entry]
    atomic_write_json(lock_path, lock)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
