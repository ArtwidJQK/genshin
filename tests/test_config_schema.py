from pathlib import Path
import json
import pytest

from app.core.artifact.config import (
    load_artifact_config,
    load_and_validate_artifact_config,
)
from app.core.artifact.schema import (
    EvidenceLevel,
    FidelityMode,
    MainStatsConfigSchema,
    ProvenanceRecord,
    RollValuesConfigSchema,
    RulesConfigSchema,
    SubstatsConfigSchema,
    load_provenance_catalog,
    validate_config_provenance_fidelity,
)

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config" / "artifacts"


def test_pydantic_schemas_validate_current_config_files():
    """All 4 production artifact configuration files conform strictly to Pydantic schemas."""
    with open(CONFIG_DIR / "main_stats.json", "r", encoding="utf-8") as f:
        main_stats = MainStatsConfigSchema.model_validate(json.load(f))
        assert main_stats.FLOWER["FLAT_HP"] == 100.0
        assert main_stats.PLUME["FLAT_ATK"] == 100.0

    with open(CONFIG_DIR / "substats.json", "r", encoding="utf-8") as f:
        substats = SubstatsConfigSchema.model_validate(json.load(f))
        assert len(substats.weights) == 10
        assert substats.weights["CRIT_RATE"] == 3.0

    with open(CONFIG_DIR / "roll_values.json", "r", encoding="utf-8") as f:
        roll_values = RollValuesConfigSchema.model_validate(json.load(f))
        assert len(roll_values.values) == 10
        assert roll_values.values["CRIT_DMG"]["100%"] == 7.77

    with open(CONFIG_DIR / "rules.json", "r", encoding="utf-8") as f:
        rules = RulesConfigSchema.model_validate(json.load(f))
        assert rules.rarity == 5
        assert rules.num_substat_slots == 4
        assert rules.max_level == 20


def test_provenance_catalog_contains_all_constants_with_required_fields():
    """Every constant in the provenance catalog has mandatory fields per AGENTS.md 5.1."""
    catalog = load_provenance_catalog(CONFIG_DIR / "provenance.json")

    assert "main_stats" in catalog
    assert "substats" in catalog
    assert "roll_values" in catalog
    assert "rules" in catalog

    for section_name, entries in catalog.items():
        assert len(entries) > 0, f"Section {section_name} is empty"
        for key, record in entries.items():
            assert isinstance(record, ProvenanceRecord)
            assert record.source.strip() != "", f"Empty source in {section_name}.{key}"
            assert record.retrieved_on.strip() != "", f"Empty retrieved_on in {section_name}.{key}"
            assert isinstance(record.evidence, EvidenceLevel)


def test_fidelity_modes_allowance_logic():
    """Unit test for ProvenanceRecord fidelity permission matrix (AGENTS.md 5.2)."""
    rec_verified = ProvenanceRecord(
        value=1.0, evidence=EvidenceLevel.VERIFIED, source="Official", retrieved_on="2026-10-11"
    )
    rec_inferred = ProvenanceRecord(
        value=1.0, evidence=EvidenceLevel.INFERRED, source="Community", retrieved_on="2026-10-11"
    )
    rec_assumed = ProvenanceRecord(
        value=1.0, evidence=EvidenceLevel.ASSUMED, source="Hypothesis", retrieved_on="2026-10-11"
    )
    rec_unknown = ProvenanceRecord(
        value=1.0, evidence=EvidenceLevel.UNKNOWN, source="Unknown", retrieved_on="2026-10-11"
    )

    # STRICT: only VERIFIED
    assert rec_verified.is_allowed_in_fidelity(FidelityMode.STRICT) is True
    assert rec_inferred.is_allowed_in_fidelity(FidelityMode.STRICT) is False
    assert rec_assumed.is_allowed_in_fidelity(FidelityMode.STRICT) is False
    assert rec_unknown.is_allowed_in_fidelity(FidelityMode.STRICT) is False

    # BEST_EFFORT: VERIFIED + INFERRED
    assert rec_verified.is_allowed_in_fidelity(FidelityMode.BEST_EFFORT) is True
    assert rec_inferred.is_allowed_in_fidelity(FidelityMode.BEST_EFFORT) is True
    assert rec_assumed.is_allowed_in_fidelity(FidelityMode.BEST_EFFORT) is False
    assert rec_unknown.is_allowed_in_fidelity(FidelityMode.BEST_EFFORT) is False

    # EXPERIMENTAL: VERIFIED + INFERRED + ASSUMED
    assert rec_verified.is_allowed_in_fidelity(FidelityMode.EXPERIMENTAL) is True
    assert rec_inferred.is_allowed_in_fidelity(FidelityMode.EXPERIMENTAL) is True
    assert rec_assumed.is_allowed_in_fidelity(FidelityMode.EXPERIMENTAL) is True
    assert rec_unknown.is_allowed_in_fidelity(FidelityMode.EXPERIMENTAL) is False  # UNKNOWN is NEVER allowed


def test_provenance_satisfies_best_effort_mode():
    """Production artifact constants satisfy best_effort fidelity mode (VERIFIED and INFERRED)."""
    violations = validate_config_provenance_fidelity(
        CONFIG_DIR / "provenance.json", mode=FidelityMode.BEST_EFFORT
    )
    assert violations == [], f"Unexpected violations in best_effort mode: {violations}"


def test_provenance_strict_mode_rejects_inferred_constants():
    """In strict mode, unverified community models (e.g. 6/4/3 weights) are rejected with clear error."""
    violations = validate_config_provenance_fidelity(
        CONFIG_DIR / "provenance.json", mode=FidelityMode.STRICT
    )
    # Substat candidate weights and weighted main stats are INFERRED, so strict mode must flag them
    assert len(violations) > 0
    assert any("substats.CRIT_RATE" in v for v in violations)


def test_load_and_validate_artifact_config_success_in_best_effort():
    """load_and_validate_artifact_config succeeds when fidelity_mode is best_effort."""
    config = load_and_validate_artifact_config(config_dir=CONFIG_DIR, fidelity_mode=FidelityMode.BEST_EFFORT)
    assert config.rarity == 5
    assert len(config.substat_weights) == 10


def test_load_and_validate_artifact_config_raises_in_strict_mode():
    """load_and_validate_artifact_config raises ValueError when strict mode rejects INFERRED rules."""
    with pytest.raises(ValueError, match="does not satisfy fidelity mode 'strict'"):
        load_and_validate_artifact_config(config_dir=CONFIG_DIR, fidelity_mode=FidelityMode.STRICT)


def test_schema_rejects_corrupted_main_stats():
    """MainStatsConfigSchema rejects invalid stat identifiers and negative weights."""
    invalid_data = {
        "FLOWER": {"FLAT_HP": 100.0},
        "PLUME": {"FLAT_ATK": 100.0},
        "SANDS": {"INVALID_STAT_NAME": 50.0},
        "GOBLET": {"HP_PERCENT": 100.0},
        "CIRCLET": {"HP_PERCENT": 100.0},
    }
    with pytest.raises(ValueError, match="Invalid main stat identifier"):
        MainStatsConfigSchema.model_validate(invalid_data)


def test_schema_rejects_missing_substats():
    """SubstatsConfigSchema rejects incomplete substat sets."""
    with pytest.raises(ValueError, match="must define exactly the 10 canonical substats"):
        SubstatsConfigSchema.model_validate({"weights": {"FLAT_HP": 6, "CRIT_RATE": 3}})


def test_schema_rejects_invalid_rules():
    """RulesConfigSchema rejects non-5-star rarity."""
    with pytest.raises(ValueError, match="Only 5-star artifacts are supported"):
        RulesConfigSchema.model_validate({
            "rarity": 4,
            "max_level": 20,
            "milestone_levels": [4, 8, 12, 16, 20],
            "num_substat_slots": 4,
            "initial_line_count_weights": {"3": 80, "4": 20},
        })
