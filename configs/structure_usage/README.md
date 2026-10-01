# Structure-usage study configs

These configs are for the structure-usage analysis study
(`docs/STRUCTURE_USAGE_PROTOCOL.md`), not the original 200-job campaign.

They intentionally live outside `configs/base.yaml` and `configs/models/` so
that changing the structural-layer placement here never mutates the frozen
protocol inputs for the original campaign (`protocol/experiment_manifest.jsonl`).

- `base.yaml` overrides `model.structural_layers` from the campaign default
  `(2,5,8,11)` to `(2,5,8,10)`. Layer 11 cannot influence the CLS logit
  because the classification head only reads the CLS token, no edges route
  into CLS, and there is no later token-mixing layer to move that
  information into position 0 before the head reads it
  (see `tests/unit/test_edge_gating.py::test_final_layer_structure_cannot_change_cls_logits`).
  `(2,5,8,10)` keeps the same "distributed across depth" spirit as the
  campaign's E3 `distributed` setting while ensuring every active layer can
  reach the classification decision.
- The historical placement `(2,5,8,11)` remains available as a named
  ablation via `configs/experiments/layers.yaml` (`distributed`) for anyone
  who wants to reproduce or compare against the original campaign's layer
  choice; it is deliberately not the default here.
