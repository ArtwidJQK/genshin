# P2 Step 3 — Expose Artifact Main-Stat Scaling

## Goal
Expose exact 5★ main stat values across all levels 0–20 from verified datamine configuration (`config/artifacts/main_stat_scaling.json`) via a clean domain API, preserving unrounded internal floating-point values without presentation rounding.

## Files
- `app/core/artifact/scaling.py`: new module implementing `get_main_stat_value(target, level=None, *, config=None) -> float` with strict type and boundary validation.
- `app/core/artifact/config.py`: add slot-scaling consistency check in `ArtifactConfig.validate()` and add `ArtifactConfig.get_main_stat_value(target, level=None)`.
- `app/core/artifact/engine.py`: add `ArtifactEngine.get_main_stat_value(target, level=None)`.
- `app/core/artifact/models.py`: add convenience delegation method `Artifact.get_main_stat_value(config=None)`.
- `app/core/artifact/__init__.py`: export `get_main_stat_value`.
- `tests/test_artifact_scaling.py`: 40 comprehensive tests covering exact 18 × 21 matrix against source JSON, boundary levels 0 and 20, invalid level/type/stat rejections, corrupted config handling, domain precision vs display formatting, and Hypothesis property tests (immutability, monotonicity, determinism).
- `.genshin/state/project-state.md`: update project state to reflect P2 Step 3 completion on branch `agent/p2-step3-main-stat-scaling`.

## API Contract
```python
def get_main_stat_value(
    target: Union[Artifact, str],
    level: Optional[int] = None,
    *,
    config: Optional[ArtifactConfig] = None,
) -> float
```
- **Inputs:**
  - `target`: either an `Artifact` instance or a canonical 5★ main stat string from `VALID_MAIN_STATS`.
  - `level`: integer in `[0, 20]`. Must be `None` when `target` is an `Artifact` (`artifact.level` is used automatically). Required when `target` is `str`.
  - `config`: optional `ArtifactConfig` instance; defaults to `load_artifact_config()`.
- **Return Value:**
  - `float`: Exact internal numeric value from datamine scaling curve. Unrounded and unformatted.
- **Error Behavior:**
  - `TypeError`: raised on non-integer level (including `bool`), target is `bool` or unsupported type, `level` provided with `Artifact`, or `level` omitted with stat string.
  - `ValueError`: raised if level is out of bounds (`< 0` or `> 20`), stat is invalid (e.g. `FLAT_DEF` or unknown), stat/level is missing from config, or scaling data is non-finite / non-positive. No fallback or interpolation is ever performed.

## Verification
- Total tests: **178 passed, 2 warnings** (`python -m pytest -v`, execution duration ~3.5s).
- Importer verification: `python tools/import_artifact_datamine.py --check` passed with exit code 0.
- Whitespace/diff check: `git diff --check` passed with 0 errors.
- Exact lookup: $18 \times 21 = 378$ values compared and verified identical to `config/artifacts/main_stat_scaling.json`.
- Immutability: Hypothesis property test verifies neither `Artifact` nor `ArtifactConfig` is mutated during lookup.
- Monotonicity: Hypothesis property test verifies $V(l_2) > V(l_1)$ for all $0 \le l_1 < l_2 \le 20$.

## Adversarial Review
**RESULT: PASS**
- **Domain vs Display Separation:** Domain API returns raw `float` with full precision; display formatting is strictly delegated to `format_stat_value` at the presentation boundary.
- **Lookup Correctness:** Direct comparison against production JSON for all 18 stats across all 21 levels.
- **Robust Error Handling:** Missing config, missing stat, missing level, out-of-bounds level, boolean inputs, and `FLAT_DEF` (which is in `CANONICAL_SUBSTATS` but not `VALID_MAIN_STATS`) are strictly rejected with explicit exceptions.
- **Scope Discipline:** Zero modifications to RNG, probabilities, drop weights, wish system, or blocked features (Capturing Radiance, Reshaping).

## Evidence and Risks
- Main stat scaling curve data is directly sourced from client datamine extractions (`ReliquaryLevelExcelConfigData.json` rank 5), verified in P2 Step 1.
- No remaining mechanics blockers exist for main stat scaling.
