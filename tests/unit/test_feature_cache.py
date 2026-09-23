import uuid
from pathlib import Path

import pytest

from astguard.data.cache import FeatureCache
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import object_hash


def test_feature_cache_reuses_valid_entry_and_rejects_stale_content():
    sample="cache-test-"+uuid.uuid4().hex
    root=Path(__file__).resolve().parents[2]/"artifacts"/"test"/"cache"
    cache=FeatureCache(root,"preprocess-v1")
    calls=[]
    value={"sample_id":sample,"source_sha256":"source","preprocessing_hash":"preprocess-v1","payload":1}
    first=cache.get_or_build("source",lambda:(calls.append(1) or value),sample_id=sample)
    second=cache.get_or_build("source",lambda:(_ for _ in ()).throw(AssertionError("cache miss")),sample_id=sample)
    assert first==second and len(calls)==1
    key=object_hash(["source","preprocess-v1",sample])
    target=root/key[:2]/(key+".json")
    atomic_write_json(target,value|{"preprocessing_hash":"stale"})
    with pytest.raises(ValueError,match="stale"):
        cache.get_or_build("source",lambda:value,sample_id=sample)
