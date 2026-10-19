# P2 Step 2 — Artifact Display Formatter and Property Tests

## Goal
Separate internal roll-value accumulation from display rounding and property-test the existing Artifact engine invariants.

## Files
- app/core/artifact/models.py: remove four-decimal rounding from Substat.value.
- app/core/artifact/formatting.py: add pure stat-value presentation formatter.
- app/core/artifact/__init__.py: export format_stat_value.
- tests/test_artifact_properties.py: add Hypothesis properties for valid slots, non-duplicate and main-stat exclusions, 3/4-line activation behavior, milestone counts, roll tiers, and same-seed replay; add formatter and input-validation tests.
- requirements.txt and pyproject.toml: declare Hypothesis for test execution.
- docs/adr/ADR-001-display-rounding.md: record the presentation-only rounding decision.
- .genshin/state/project-state.md: reconcile stale Git status and handoff.

## Verification
- GitHub Actions run 39294411756: Python 3.11 — 138 passed, 1 Starlette deprecation warning; Python 3.12 — 138 passed, 1 Starlette deprecation warning. Both jobs succeeded after the final code/test change.
- Local commands were not run through the GitHub connector; the passing Actions matrix is the test evidence for this branch.
- The formatter and tests do not implement loot-source rules, Gacha, or Reshaping. The imported main-stat curve still needs to be exposed through the Artifact domain contract as the next P2 task.

## Adversarial review
**RESULT: PASS**

- Internal value precision: Substat.value now returns the sum without presentation rounding; formatting has no reference to or mutation of the artifact state.
- Slot and stat exclusions: property tests cover all five slots; assert four distinct substats, main stat exclusion, and slot-specific main-stat membership.
- 3-line/4-line boundary: property tests assert that +4 activation on a 3-line artifact has no tier/increment and reduces the random upgrade count by one; other crossed milestones create exactly one upgrade each.
- Determinism: same seed and identical inputs produce equal artifact objects and event traces across generated property cases.
- Formatter boundary: all recognized artifact properties obey expected output shape; nonnumeric, unknown and non-finite inputs are rejected.
- Dependency/CI: Hypothesis is installed by requirements.txt; both configured CI Python versions pass.

## Evidence and risks
- Display precision follows docs/SPEC_ARTIFACT.md section 3.4.
- ROUND_HALF_UP is a documented presentation-only engineering convention; it is not asserted as verified internal game behavior.
- The existing CI workflow only runs pytest, not Ruff/mypy; lint/type-check automation remains a separate repository-quality follow-up.
