import json
import math
import subprocess
import sys
from pathlib import Path
import pytest

from app.core.artifact.config import (
    ArtifactConfig,
    load_artifact_config,
    load_and_validate_artifact_config,
)
from app.core.artifact.models import (
    ALL_ARTIFACT_PROPERTIES,
    CANONICAL_SUBSTATS,
    VALID_MAIN_STATS,
)
from app.core.artifact.schema import (
    EvidenceLevel,
    FidelityMode,
    MainStatScalingConfigSchema,
    load_provenance_catalog,
)
from tools.import_artifact_datamine import (
    BOUNDARY_ANCHORS,
    extract_main_stat_scaling,
    run_importer,
    update_provenance_catalog,
    verify_substat_roll_tiers,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config" / "artifacts"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "datamine"


def test_stat_set_invariants():
    """Verify exact counts and relations of the 3 formal stat sets."""
    assert len(CANONICAL_SUBSTATS) == 10
    assert "FLAT_DEF" in CANONICAL_SUBSTATS

    assert len(VALID_MAIN_STATS) == 18
    assert "FLAT_DEF" not in VALID_MAIN_STATS

    assert len(ALL_ARTIFACT_PROPERTIES) == 19
    assert ALL_ARTIFACT_PROPERTIES == (CANONICAL_SUBSTATS | VALID_MAIN_STATS)


def test_main_stat_scaling_extraction_completeness_and_invariants():
    """Main stat scaling extracted from datamine covers exactly 18 stats and 21 levels."""
    scaling = extract_main_stat_scaling(FIXTURES_DIR)

    assert scaling["rarity"] == 5
    assert scaling["max_level"] == 20
    stats = scaling["stats"]
    assert set(stats.keys()) == VALID_MAIN_STATS
    assert "FLAT_DEF" not in stats

    expected_levels = {str(i) for i in range(21)}
    for stat_name, levels in stats.items():
        assert set(levels.keys()) == expected_levels

        # Strict monotonicity: V(l+1) > V(l)
        for lvl in range(20):
            cur = levels[str(lvl)]
            nxt = levels[str(lvl + 1)]
            assert nxt > cur, f"Monotonicity failed for {stat_name} between {lvl} and {lvl+1}: {cur} >= {nxt}"

        # Check secondary boundary anchors
        if stat_name in BOUNDARY_ANCHORS:
            exp_0, exp_20 = BOUNDARY_ANCHORS[stat_name]
            assert math.isclose(levels["0"], exp_0, abs_tol=1e-3), (
                f"Level 0 anchor mismatch for {stat_name}: got {levels['0']}, expected {exp_0}"
            )
            assert math.isclose(levels["20"], exp_20, abs_tol=1e-3), (
                f"Level 20 anchor mismatch for {stat_name}: got {levels['20']}, expected {exp_20}"
            )


def test_substat_roll_tier_ratio_verification():
    """5★ substat roll values in depot 501 strictly adhere to 0.70/0.80/0.90/1.00 ratios."""
    roll_vals = verify_substat_roll_tiers(
        input_dir=FIXTURES_DIR,
        roll_values_path=CONFIG_DIR / "roll_values.json",
    )

    assert set(roll_vals.keys()) == CANONICAL_SUBSTATS
    for stat, tiers in roll_vals.items():
        assert set(tiers.keys()) == {"70%", "80%", "90%", "100%"}
        v1, v2, v3, v4 = tiers["70%"], tiers["80%"], tiers["90%"], tiers["100%"]
        assert 0 < v1 < v2 < v3 < v4


def test_schema_validates_generated_main_stat_scaling_file():
    """Production config/artifacts/main_stat_scaling.json conforms strictly to Pydantic schema."""
    scaling_path = CONFIG_DIR / "main_stat_scaling.json"
    assert scaling_path.exists(), "main_stat_scaling.json must exist in config/artifacts"

    with open(scaling_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    validated = MainStatScalingConfigSchema.model_validate(raw)
    assert validated.rarity == 5
    assert validated.max_level == 20
    assert len(validated.stats) == 18


def test_schema_rejects_corrupted_scaling_configs():
    """MainStatScalingConfigSchema rejects invalid rarity, non-monotonic values, and wrong stats."""
    base_valid = extract_main_stat_scaling(FIXTURES_DIR)

    # 1. Invalid rarity
    bad_rarity = {**base_valid, "rarity": 4}
    with pytest.raises(ValueError, match="Rarity must be 5"):
        MainStatScalingConfigSchema.model_validate(bad_rarity)

    # 2. Invalid max_level
    bad_max = {**base_valid, "max_level": 16}
    with pytest.raises(ValueError, match="Max level must be 20"):
        MainStatScalingConfigSchema.model_validate(bad_max)

    # 3. Missing stat
    bad_missing = {
        **base_valid,
        "stats": {k: v for k, v in base_valid["stats"].items() if k != "CRIT_RATE"},
    }
    with pytest.raises(ValueError, match="Main stat scaling must define exactly the 18 valid main stats"):
        MainStatScalingConfigSchema.model_validate(bad_missing)

    # 4. Extra stat (e.g. FLAT_DEF incorrectly included as main stat)
    bad_extra = {
        **base_valid,
        "stats": {**base_valid["stats"], "FLAT_DEF": base_valid["stats"]["FLAT_HP"]},
    }
    with pytest.raises(ValueError, match="Main stat scaling must define exactly the 18 valid main stats"):
        MainStatScalingConfigSchema.model_validate(bad_extra)

    # 5. Non-monotonic level progression
    corrupted_stats = json.loads(json.dumps(base_valid["stats"]))
    corrupted_stats["CRIT_RATE"]["5"] = corrupted_stats["CRIT_RATE"]["4"]  # not strictly greater
    with pytest.raises(ValueError, match="not strictly greater than"):
        MainStatScalingConfigSchema.model_validate({**base_valid, "stats": corrupted_stats})


def test_provenance_catalog_contains_granular_verified_main_stat_scaling():
    """All 18 main stat scaling records in provenance.json have VERIFIED evidence and correct versions."""
    catalog = load_provenance_catalog(CONFIG_DIR / "provenance.json")

    assert "main_stat_scaling" in catalog
    sec = catalog["main_stat_scaling"]
    assert set(sec.keys()) == VALID_MAIN_STATS

    for stat, rec in sec.items():
        assert rec.evidence == EvidenceLevel.VERIFIED
        assert "ReliquaryLevel" in rec.source
        assert rec.retrieved_on.strip() != ""
        if stat == "DENDRO_DMG_BONUS":
            assert rec.valid_from_version == "3.0"
        else:
            assert rec.valid_from_version == "1.0"


def test_importer_cli_check_mode_success():
    """tools/import_artifact_datamine.py --check exits 0 on valid committed state."""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "import_artifact_datamine.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Importer --check failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    assert "CHECK PASSED" in result.stdout


def test_importer_cli_check_mode_fails_on_drift(tmp_path):
    """tools/import_artifact_datamine.py --check exits with code 1 if config is drifted or missing."""
    drift_output = tmp_path / "artifacts"
    drift_output.mkdir()

    # Empty dir should fail check
    code = run_importer(input_dir=FIXTURES_DIR, output_dir=drift_output, check_only=True)
    assert code != 0


def test_artifact_config_loads_main_stat_scaling():
    """ArtifactConfig properly populates main_stat_scaling with integer level keys."""
    config = load_artifact_config(CONFIG_DIR)
    assert config.main_stat_scaling is not None
    assert set(config.main_stat_scaling.keys()) == VALID_MAIN_STATS

    # Verify integer key access
    assert config.main_stat_scaling["CRIT_RATE"][0] == 4.7
    assert config.main_stat_scaling["CRIT_RATE"][20] == 31.1
    assert config.main_stat_scaling["FLAT_HP"][0] == 717.0
    assert config.main_stat_scaling["FLAT_HP"][20] == 4780.0
    assert config.main_stat_scaling["ELEMENTAL_MASTERY"][20] == 186.5


def test_load_and_validate_artifact_config_accepts_scaling_in_best_effort():
    """load_and_validate_artifact_config succeeds in best_effort mode with scaling present."""
    config = load_and_validate_artifact_config(CONFIG_DIR, fidelity_mode=FidelityMode.BEST_EFFORT)
    assert config.main_stat_scaling is not None
    assert len(config.main_stat_scaling) == 18
