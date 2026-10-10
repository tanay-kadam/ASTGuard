# Submission strategy (verified 2026-10-05)
> Current evidence (2026-10-10): the historical planning notes below are retained
> as history. Use [the 2026-10-09 submission audit](../docs/PAPER_SUBMISSION_AUDIT_20261009.md)
> and [the corrected artifact](../artifact/README.md) for the revised manuscript.
> The corrected 42-job campaign is complete; the scientific scope remains the
> development/tune cohort and includes failed centered synthetic controls.
> Superseded integrity gate (2026-10-06): NO-GO for the historical manuscript pending corrected-split reruns. The Stage 0 manifest filtered IDs without filtering parallel roles/components, causing 10,619 role mismatches. The positive-control campaign remains separate and numerically valid. The new strengthening protocol and split-integrity report describe required repairs; no acceptance probability is promised.


## Completed go/no-go audit (2026-10-06)

**Project decision: GO. Current SANER submission decision: NO-GO as-is.**

The empirical core is real, reproducible, and worth publishing. The present
manuscript should not, however, be rushed into SANER in its current form. The
main risk is not numerical correctness; it is that the study evaluates one local
model family without a trained positive control, while the closest ICSE 2025
framework evaluates five independent detectors. SANER explicitly evaluates the
depth and breadth of the empirical study and warns that an underpowered negative
result is not a strong submission.

The five internal conditions below were checked as follows:

1. **PASS — final interventions.** All three reports are complete on 10,566 tune
   examples and Table 6 is populated.
2. **PASS — evidence integrity.** Raw-prediction AP recomputation again matched
   all nine campaign runs and all three interventions within `1e-12`; all scores
   were finite; all 14 targeted unit tests passed; and the three final selected
   checkpoints rehashed to the SHA-256 values printed in the manuscript. The
   official test role remains unopened.
3. **NOT MET — venue-formatted length.** The Markdown draft has 5,012 words
   through the conclusion, six result tables (52 Markdown rows), and 6,723 words
   before the references when the appendices are included. There is no compiled
   IEEE `10pt,conference` PDF proving compliance with the 10-page limit, which
   includes appendices.
4. **NOT MET — positive-control sensitivity.** The finite constructed example
   proves an algebraic property, but it is not a trained positive-control model or
   task demonstrating that the complete audit detects deliberately present
   topology reliance. The current text mentions this limitation, but disclosure
   does not supply the missing sensitivity evidence.
5. **PARTIAL — closest-work differentiation.** The novelty audit identifies the
   ICSE 2025 conflict, but the paper gives only a short narrative paragraph. It
   does not yet make a reviewer-visible comparison across perturbation target,
   nuisance preservation, training-time versus inference-time intervention,
   models, datasets, and metrics.

This is therefore a **go for a strengthened negative-results paper**, with EASE
2027 RENE as the realistic target under the user's goal of building the strongest
paper and portfolio signal. SANER remains rational only if, by 2026-10-15, a
trained positive control passes, the closest-work comparison is explicit, and a
compiled anonymous IEEE PDF fits ten pages. For a materially stronger paper, add
at least one independently published graph detector under the same audit before
submission. Keep the official test locked until that protocol is frozen.

## Recommendation

The original strategy was to submit first to the **SANER 2027 Reproducibility
Studies and Negative Results (RENE) Track** and, if rejected, use the reviews to
strengthen the artifact for the **EASE 2027 Reproducibility and Negative Results
Track**. The completed check above supersedes an automatic SANER submission: use
SANER only if every remaining gate is genuinely closed by 2026-10-15. Otherwise,
prepare the stronger EASE submission. Do not submit to both simultaneously.

This ordering maximizes the number of legitimate publication opportunities and gives an earlier career signal. SANER's track explicitly accepts new negative/null results and publishes accepted papers in the conference proceedings. The paper deadline is close, so the internal go/no-go date should be 2026-10-15.

EASE is the stronger fallback for a more complete empirical paper. Its call explicitly solicits AI/ML sensitivity analyses involving random seeds, ablations showing components do not contribute as expected, simple baselines matching complex methods, and unstable effects. Its website describes EASE as CORE A. The later deadline leaves enough time to add a positive-control structural task or detector, one external detector/dataset, and a cleaner artifact.

## SANER 2027 RENE

- Mandatory abstract: 2026-10-19 (AoE)
- Full paper: 2026-10-23 (AoE)
- Notification: 2026-12-08
- Format: up to 10 pages plus up to 2 reference-only pages
- Accepted papers: SANER 2027 proceedings
- Attendance: at least one author must pay full registration (not student registration) and attend in Richmond, Virginia
- Official call: <https://conf.researchr.org/track/saner-2027/saner-2027-reproducibility-studies-and-negative-results-rene-track>

## EASE 2027 RENE

- Abstract: 2027-02-22
- Full paper: 2027-03-01
- Notification: 2027-04-12
- Format: 10 main-text pages including appendices, plus up to 2 reference-only pages; ACM format
- Conference: 2027-06-15 through 2027-06-18, Hanoi, Vietnam
- Official call: <https://conf.researchr.org/track/ease-2027/ease-2027-reproducibility-and-negative-results>

## SANER go/no-go conditions

Proceed with SANER only if all are complete by 2026-10-15:

1. Final intervention reports are in the artifact and Table 6 is filled.
2. The artifact manifest and checksums verify locally.
3. The paper is reduced to the 10-page format without removing seed-level evidence.
4. At least one positive-control experiment shows that the audit detects structural reliance when it is deliberately present, or the absence of that control is made a central, explicit limitation.
5. The related-work comparison with the ICSE 2025 feature-evaluation framework is explicit enough that reviewers can see what this study adds.

If conditions 4--5 cannot be completed convincingly, keep the current draft as the evidence base and target EASE after adding them. A rushed weak submission does less for the project than a later defensible one.
