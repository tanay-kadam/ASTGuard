# Experiments

`protocol/experiment_manifest.jsonl` contains 200 finite training jobs. Inference
analyses reuse checkpoints. Test inference is refused until the protocol lock
contains hashes for sources, split, preprocessing, protocol, and manifest.

