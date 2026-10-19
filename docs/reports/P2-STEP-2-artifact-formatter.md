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
- The preceding reported baseline was 123 passed with 2 dependency deprecation warnings.
- Local commands cannot be run through the GitHub connector. The branch must pass the existing GitHub Actions matrix on Python 3.11 and 3.12 before merge.
- The formatter and tests intentionally do not implement loot-source rules, main-stat state transitions, Gacha, or Reshaping.

## Evidence and risks
- Display precision follows docs/SPEC_ARTIFACT.md section 3.4.
- ROUND_HALF_UP is a documented presentation-only engineering convention; not asserted as verified internal game behavior.
- Adversarial review must verify that 3-line +4 creates an activation event without a roll, that unrounded values remain internal, and that Hypothesis is installed in CI.
