# Graph reliance paper: reproducibility artifact

This package supports *When Do Vulnerability Detectors Rely on Their Graphs?
Evidence from Attention Biases, Adapters, and ReGVD* ([manuscript](../main.pdf)).
The supplied manuscript is a PDF; its LaTeX source was not available in this
workspace and is not claimed to be part of this package.
The canonical release is
[graph-reliance-artifact-20261009-v1](https://github.com/tanay-kadam/ASTGuard/releases/tag/graph-reliance-artifact-20261009-v1).
The Git repository contains compact evidence and executable verification code;
large checkpoint and processed-input files are separate release assets.

## Start with the saved results

From the repository root, use Python 3.11:

```sh
python -m venv .venv-review
# Linux/macOS: source .venv-review/bin/activate
# Windows: .venv-review\Scripts\Activate.ps1
python -m pip install -r artifact/requirements-metrics.txt
python artifact/verify.py
```

This needs no GPU, server access, raw data, or pretrained model download. It checks
the packaged SHA256 hashes and independently recomputes 42 selected tune APs,
156 intervention AP/ROC-AUC/logit-change conditions, selected epoch consistency,
paired seed contrasts, and the frozen synthetic success rules. It writes
`results/artifact_verification.json`. A successful exit means evidence integrity
and metric agreement; scientific criteria that fail are reported as failures of
those criteria, rather than hidden as a software error.

## Check weights against saved logits

```sh
python -m pip install -r artifact/requirements-inference.txt
python artifact/download.py --checkpoints synthetic_attention_authentic_s42 synthetic_centered_authentic_s42 regvd_native_s42
python artifact/infer.py --jobs synthetic_attention_authentic_s42 synthetic_centered_authentic_s42 regvd_native_s42 --device cpu
```

The selected three checkpoints need approximately 1.1 GiB of downloads. This
reconstructs each architecture from saved backbone configurations and checks
four stored inputs per model against FP32 intervention logits. It works offline
after downloading the weights; it does not fetch Hugging Face models. The default
absolute logit tolerance is `1e-4`. This is a small inference smoke, not full-cohort
re-evaluation or training reproducibility. Original CodeBERT checkpoint selection
used BF16, whereas the intervention evidence uses FP32 raw logits.

Add `--interventions` to check every stored graph condition on the smoke inputs.
After downloading data, use `--full --interventions --device cuda` for complete
synthetic audit / real tune re-evaluation from weights. That command checks each
logit against saved evidence and reports newly computed APs; it can be slow.

For all 42 checkpoint hashes (about 16.6 GiB of weights):

```sh
python artifact/download.py --all-checkpoints
python artifact/verify.py --checkpoints artifact/downloads/checkpoints
```

All asset URLs, byte sizes, and SHA256 hashes are in `manifest.json`. Downloaded
files go to ignored `artifact/downloads/`; no SSH access is needed by reviewers.
Release assets can also be downloaded manually and supplied with
`artifact/download.py --local-assets PATH --all-checkpoints --data`.

## Training inputs and repeat runs

```sh
python artifact/download.py --data
python artifact/prepare_synthetic.py
```

The data assets contain the exact processed real train/tune features, ReGVD
train/tune token features, and normalized development records used in the
corrected campaign. Synthetic train/tune/audit inputs are already in Git as gzip
files. Real inputs expand to approximately 6.6 GiB; allow additional space for
compressed downloads and newly trained models. They contain no official test
evaluation. `real_inputs_manifest.json`, `corrected_manifest.json.gz`, and the
population audits document the component-disjoint development split.

For training, use a CUDA-capable Linux host, install the repository research
dependencies (`python -m pip install -e ".[research,test]"`), and compare its
versions with `environment-remote.freeze.txt`. The original server used Python
3.10.12, Torch 2.5.1+cu121, Transformers 4.49.0 and L40S GPUs. The supported package
installation and compact verifier use Python 3.11. The freeze is an environment
record including Ubuntu system packages, not a cross-platform pip requirements
file. Pinned pretrained backbones must be downloadable or cached for training.
Saved model configurations retain original hashes and paths as provenance;
the command-line feature arguments below supply the portable paths.

```sh
python -m astguard.train --config artifact/evidence/real_attention_authentic_s42/config.json --features artifact/downloads/inputs/real/train.jsonl --tune-features artifact/downloads/inputs/real/tune.jsonl --seed 42 --runs-root results/retraining --require-cuda
python -m astguard.train --config artifact/evidence/synthetic_centered_authentic_s42/config.json --features artifact/downloads/inputs/synthetic/train.jsonl --tune-features artifact/downloads/inputs/synthetic/tune.jsonl --seed 42 --runs-root results/retraining --require-cuda
python scripts/run_regvd_strengthening.py --train artifact/downloads/inputs/real/regvd_train.jsonl --tune artifact/downloads/inputs/real/regvd_tune.jsonl --condition native --seed 42 --output results/retraining/regvd_native_s42
```

Use the other saved per-job configurations and seeds (42, 123, 456) to repeat the
remaining conditions. `jobs.json` gives the complete 42-job matrix, and
`summary.json` gives original selections. Full retraining is computationally
expensive and is not performed by the compact verifier. The native ReGVD runner
records explicit common-cohort changes from its pinned upstream implementation.
Local intervention evaluation is implemented in
`scripts/evaluate_strengthening_checkpoint.py`; the synthetic audit split is
held out from checkpoint selection.

## Evidence and provenance

`evidence/<job>/` contains selected predictions, all retained local epoch
predictions, resolved configuration, training history, interventions, and
available provenance/selection records. ReGVD includes its four intervention
prediction files and original checksum record. `manifest.json` maps compressed
evidence back to original uncompressed hashes and selected checkpoint hashes.
`runtime_source.tar.gz` preserves the retrieved runtime source; its per-file
hashes are in `runtime_source_manifest.json`. `import_inventory.json` records the
SHA256-verified 1,378-file SSH import; large originals are represented by release
assets rather than duplicated inside Git. Six older synthetic runs have less
complete start/seed provenance than later runs. This snapshot does not establish
an exact historical execution image for every run.

The local retrieval mirror is `artifacts/ssh_import_20261009/snapshot/` and is
deliberately ignored by Git. Maintainers can resume retrieval with
`scripts/pull_corrected_artifact.py` using their own trusted SSH configuration.
Reviewers use the public release instead. Private credentials, optimizer/resume
states, quarantined historical runs, and smoke checkpoints are excluded.

## Claims supported and limits

All real-data numbers use the 10,566-example checkpoint-selection tune cohort
(330 positives). They are development-cohort observations, not estimates on an
independent real test set. The attention synthetic control passes its frozen
rules; the centered synthetic control fails the authentic-versus-shuffled rule
for seeds 123 and 456. The package retains those failed controls. A small
intervention effect establishes checkpoint sensitivity under that intervention;
it does not establish universal graph irrelevance or out-of-distribution behavior.

Historical real results under `archive/invalid_results_20261007/` are excluded.
See [the submission audit](../docs/PAPER_SUBMISSION_AUDIT_20261009.md) and
[corrected protocol](../docs/SUBMISSION_STRENGTHENING_PROTOCOL_20261006.md).
Packaging does not remove these scientific limitations. This public GitHub
repository identifies its authors; a venue requiring anonymous artifacts needs
an anonymous mirror and manuscript link appropriate to that review policy.

## Licenses

Root `LICENSE` covers original project code. Preserve the pinned upstream notices
under `third_party/` and consult `sources.lock.json` for source provenance.
PrimeVul-derived features and pretrained-model-derived weights retain applicable
upstream terms; the underlying projects' licenses are not replaced by the root
MIT license. See [third-party notices](../third_party/LICENSES/README.md).
