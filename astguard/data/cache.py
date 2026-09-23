"""Atomic sparse feature caches with process-safe per-key locks."""
import json
from pathlib import Path
from filelock import FileLock
from astguard.utils.hashing import object_hash
from astguard.utils.atomic_io import atomic_write_json


class FeatureCache:
    def __init__(self,root,preprocessing_hash):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.preprocessing_hash=preprocessing_hash

    def get_or_build(self,source_hash,builder,*,sample_id):
        # sample_id is included because registered topology controls seed their
        # frozen rewiring by sample identity even when canonical source repeats.
        key=object_hash([source_hash,self.preprocessing_hash,sample_id])
        target=self.root/key[:2]/(key+'.json');target.parent.mkdir(parents=True,exist_ok=True)
        with FileLock(str(target)+'.lock',timeout=120):
            if target.exists():
                value=json.loads(target.read_text(encoding='utf-8'))
                if value['preprocessing_hash']!=self.preprocessing_hash or value['source_sha256']!=source_hash:
                    raise ValueError('stale or corrupted feature cache')
                if value['sample_id']!=sample_id:
                    raise ValueError('cache sample identity mismatch')
                return value
            value=builder()
            if value['preprocessing_hash']!=self.preprocessing_hash:
                raise ValueError('builder preprocessing hash differs from cache')
            if value['source_sha256']!=source_hash or value['sample_id']!=sample_id:
                raise ValueError('builder returned the wrong source/sample identity')
            atomic_write_json(target,value)
            return value
