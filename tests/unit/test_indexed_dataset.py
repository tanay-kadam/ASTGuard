from pathlib import Path

from astguard.train import _FeatureDataset


def test_feature_dataset_indexes_jsonl_without_retaining_rows():
    path=Path(__file__).resolve().parents[1]/"fixtures"/"joined_train.jsonl"
    dataset=_FeatureDataset(path,role="train",manifest_hash="split",preprocessing_hash="pre")
    assert len(dataset)==2
    assert dataset.positives==1
    assert dataset.max_input_length==3
    assert not hasattr(dataset,"rows")
    assert dataset[1]["sample_id"]=="b"
