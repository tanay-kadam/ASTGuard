# Completed five-seed follow-up: evidence and preservation

The seven-day campaign completed 66 new training runs and 45 external evaluations.
Nine earlier ReGVD checkpoints were reused with unchanged recipe/input hashes;
the primary real evaluation has 45 checkpoints, not 45 additional training runs.
The external population contains 56,571 functions, 4,135 positive labels and 881
specified-rule components. It is not certified project/semantic/pretraining
independent, and the historical original-test exposure remains disclosed.

## Portable evidence

`artifact/followup_20261012/` contains the complete anonymous saved-score package:
labels and consistent role-namespaced IDs, scores, component membership, numerical
configs, histories, seed-level results, checksums, metric verification, paired
bootstrap analysis, and table/figure regeneration. Install its requirements in a
Python 3.11 environment, then run from the repository root:

```sh
python artifact/followup_20261012/verify.py --root artifact/followup_20261012
python artifact/followup_20261012/reproduce.py --root artifact/followup_20261012 --output results/followup_regenerated
python artifact/followup_20261012/verify.py --root artifact/followup_20261012 --bootstrap
```

The first command rechecks 66 selected streams, 45 external evaluations and 429
intervention streams. The optional last command reproduces all five 10,000-resample
component and hierarchical comparisons. Previously executed checks passed; this
does not imply independent-team retraining or human validation of vulnerability
labels. Never substitute selected TUNE probability scores for external logits.

All five primary hierarchical intervals contain zero. ReGVD native-minus-self
is positive in all five seeds, but population uncertainty remains. The synthetic
selection diagnostic changes selected epochs with matching loss/step trajectories;
four audit APs fall and one remains perfect. Its mechanism is only partly explained.

## Runtime source and large assets

The root implementation, campaign scripts and frozen protocols document execution.
The supplementary `implementation_reference/*.py.txt` files are reference logic,
not a complete runnable training distribution. Raw benchmark function bodies and
model weights are excluded from this Git repository. Upstream redistribution
terms remain applicable. No public full implementation/checkpoint release is
committed by the supplementary README.

The author-side preservation directory is the ignored
`archive/ssh_campaign_20261020/`. Its inventory records original paths, sizes,
SHA256 digests, selected checkpoint coverage and omissions. The shutdown workflow
keeps all selected campaign weights and nine reused ReGVD checkpoint records,
inputs, source, predictions, configs, histories and operational logs. Unselected
last/optimizer/smoke checkpoints and disposable caches are not needed for the
reported selected-checkpoint results. Duplicate October17 exports already have a
separate verified local mirror. Consult the private transfer report for actual
backup/deletion completion; this guide alone is not a completion certificate.

The remote cleanup target is only the isolated `/tmp/astguard_seven_day_20261012`
campaign. The original `/home/tkadam/ASTGuard` project is outside that scope.
Remote deletion is permitted only after every inventory file is locally verified
and this portable evidence/source change has been pushed successfully.
