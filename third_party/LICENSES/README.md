# Third-party notices

Pinned upstream source files are retained under `third_party/sources/`.
`sources.lock.json` records their URLs, revisions, hashes, and access notes.
CodeBERT, CodeXGLUE, LineVul, and PrimeVul have upstream LICENSE files beside
their snapshots; those terms apply to the respective upstream files.

The retained ReGVD snapshot has an upstream README describing its terms but no
standalone LICENSE. Preserve that notice; the repository's root MIT license
does not relicense upstream ReGVD material. The local implementation and common
cohort adaptations are described in `astguard/baselines/regvd.py` and
`scripts/run_regvd_strengthening.py`.

Pretrained CodeBERT/GraphCodeBERT-derived weights and dataset-derived assets
remain subject to their upstream terms. PrimeVul's MIT license does not replace
the licenses of the underlying C/C++ projects. The release includes processed
token/graph features and derived model weights, rather than claiming ownership
of all underlying source code. See `artifact/README.md` for scope and provenance.

