"""Layer 1: Determinism and PRNG reproducibility tests for Artifact Loot Sources.

Satisfies:
- P3 Spec Section 9.1
- AGENTS.md Section 11 (RNG purity and bit-for-bit replay)
"""

import random
from typing import List

import pytest

from app.core.artifact.engine import ArtifactEngine
from app.core.artifact.loot import (
    DomainDropResult,
    LootAuditEvent,
    LootFidelityMode,
    LootSourceType,
    StrongboxResult,
    craft_strongbox,
    run_domain_of_blessing,
)
from app.core.artifact.models import Artifact, ArtifactSlot
from app.core.artifact.scaling import get_main_stat_value
from app.core.rng.engine import PythonRNG


def _create_sacrifices(engine: ArtifactEngine, count: int = 6) -> List[Artifact]:
    """Helper to generate valid 5★ artifacts for Strongbox sacrifice."""
    return [engine.generate_artifact(set_id="gladiators_finale") for _ in range(count)]


def test_domain_bit_for_bit_replay_from_seed():
    """Identical seeds produce bit-for-bit identical Domain of Blessing results."""
    seed = 20261020

    engine_a = ArtifactEngine(rng=PythonRNG(seed=seed))
    engine_b = ArtifactEngine(rng=PythonRNG(seed=seed))

    res_a = run_domain_of_blessing(
        domain_id="spire_of_solitary_enlightenment",
        sets=("deepwood_memories", "gilded_dreams"),
        use_condensed=False,
        engine=engine_a,
    )
    res_b = run_domain_of_blessing(
        domain_id="spire_of_solitary_enlightenment",
        sets=("deepwood_memories", "gilded_dreams"),
        use_condensed=False,
        engine=engine_b,
    )

    assert res_a.domain_id == res_b.domain_id
    assert res_a.count_4star_fodder == res_b.count_4star_fodder
    assert res_a.resin_spent == res_b.resin_spent == 20
    assert res_a.runs_executed == res_b.runs_executed == 1
    assert res_a.weakest_evidence_level == res_b.weakest_evidence_level == "INFERRED"
    assert len(res_a.artifacts) == len(res_b.artifacts)

    for art_a, art_b in zip(res_a.artifacts, res_b.artifacts):
        assert art_a.slot == art_b.slot
        assert art_a.set_id == art_b.set_id
        assert art_a.main_stat == art_b.main_stat
        assert get_main_stat_value(art_a) == get_main_stat_value(art_b)
        assert len(art_a.substats) == len(art_b.substats)
        for s_a, s_b in zip(art_a.substats, art_b.substats):
            assert s_a.stat_type == s_b.stat_type
            assert s_a.value == s_b.value
            assert s_a.state == s_b.state

    assert len(res_a.audit_events) == len(res_b.audit_events)
    for ev_a, ev_b in zip(res_a.audit_events, res_b.audit_events):
        assert ev_a.cycle_index == ev_b.cycle_index
        assert ev_a.source_type == ev_b.source_type
        assert ev_a.event_type == ev_b.event_type
        assert ev_a.roll_value == ev_b.roll_value
        assert ev_a.threshold == ev_b.threshold
        assert ev_a.outcome == ev_b.outcome


def test_condensed_resin_bit_for_bit_replay():
    """Condensed Resin execution is bit-for-bit reproducible given the same seed."""
    seed = 987654321

    engine_a = ArtifactEngine(rng=PythonRNG(seed=seed))
    engine_b = ArtifactEngine(rng=PythonRNG(seed=seed))

    res_a = run_domain_of_blessing(use_condensed=True, engine=engine_a)
    res_b = run_domain_of_blessing(use_condensed=True, engine=engine_b)

    assert res_a.resin_spent == res_b.resin_spent == 40
    assert res_a.runs_executed == res_b.runs_executed == 2
    assert res_a.count_4star_fodder == res_b.count_4star_fodder
    assert len(res_a.artifacts) == len(res_b.artifacts)

    for art_a, art_b in zip(res_a.artifacts, res_b.artifacts):
        assert art_a.slot == art_b.slot
        assert art_a.set_id == art_b.set_id
        assert art_a.main_stat == art_b.main_stat
        assert [s.stat_type for s in art_a.substats] == [s.stat_type for s in art_b.substats]


def test_condensed_resin_matches_two_sequential_normal_runs():
    """1 Condensed Resin run exactly matches 2 sequential normal runs on the same RNG stream."""
    seed = 555666777

    # Case 1: 1 Condensed Resin run (runs 2 sequential cycles)
    engine_condensed = ArtifactEngine(rng=PythonRNG(seed=seed))
    res_condensed = run_domain_of_blessing(use_condensed=True, engine=engine_condensed)

    # Case 2: 2 sequential normal runs on a single un-reset RNG stream
    engine_sequential = ArtifactEngine(rng=PythonRNG(seed=seed))
    res_run1 = run_domain_of_blessing(use_condensed=False, engine=engine_sequential)
    res_run2 = run_domain_of_blessing(use_condensed=False, engine=engine_sequential)

    # 1. Total artifacts match concatenated runs
    expected_artifacts = res_run1.artifacts + res_run2.artifacts
    assert len(res_condensed.artifacts) == len(expected_artifacts)
    for c_art, exp_art in zip(res_condensed.artifacts, expected_artifacts):
        assert c_art.slot == exp_art.slot
        assert c_art.set_id == exp_art.set_id
        assert c_art.main_stat == exp_art.main_stat
        assert get_main_stat_value(c_art) == get_main_stat_value(exp_art)
        assert [s.stat_type for s in c_art.substats] == [s.stat_type for s in exp_art.substats]
        assert [s.value for s in c_art.substats] == [s.value for s in exp_art.substats]

    # 2. Total 4★ fodder matches sum
    assert res_condensed.count_4star_fodder == (res_run1.count_4star_fodder + res_run2.count_4star_fodder)

    # 3. Audit events match
    assert len(res_condensed.audit_events) == len(res_run1.audit_events) + len(res_run2.audit_events)
    cycle0_events = [ev for ev in res_condensed.audit_events if ev.cycle_index == 0]
    cycle1_events = [ev for ev in res_condensed.audit_events if ev.cycle_index == 1]

    for ev_c, ev_seq in zip(cycle0_events, res_run1.audit_events):
        assert ev_c.event_type == ev_seq.event_type
        assert ev_c.roll_value == ev_seq.roll_value
        assert ev_c.outcome == ev_seq.outcome

    for ev_c, ev_seq in zip(cycle1_events, res_run2.audit_events):
        assert ev_c.event_type == ev_seq.event_type
        assert ev_c.roll_value == ev_seq.roll_value
        assert ev_c.outcome == ev_seq.outcome


def test_strongbox_bit_for_bit_replay_from_seed():
    """Identical seeds produce identical Strongbox crafts."""
    seed = 424242

    engine_prep = ArtifactEngine(rng=PythonRNG(seed=100))
    sacrifices_a = _create_sacrifices(engine_prep, count=9)
    sacrifices_b = _create_sacrifices(engine_prep, count=9)

    engine_a = ArtifactEngine(rng=PythonRNG(seed=seed))
    engine_b = ArtifactEngine(rng=PythonRNG(seed=seed))

    res_a = craft_strongbox("noblesse_oblige", sacrifices_a, engine=engine_a)
    res_b = craft_strongbox("noblesse_oblige", sacrifices_b, engine=engine_b)

    assert res_a.target_set == res_b.target_set == "noblesse_oblige"
    assert res_a.sacrificed_count == res_b.sacrificed_count == 9
    assert len(res_a.artifacts) == len(res_b.artifacts) == 3

    for art_a, art_b in zip(res_a.artifacts, res_b.artifacts):
        assert art_a.set_id == "noblesse_oblige"
        assert art_a.slot == art_b.slot
        assert art_a.main_stat == art_b.main_stat
        assert [s.stat_type for s in art_a.substats] == [s.stat_type for s in art_b.substats]
        assert [s.value for s in art_a.substats] == [s.value for s in art_b.substats]

    assert len(res_a.audit_events) == len(res_b.audit_events) == 3
    for ev_a, ev_b in zip(res_a.audit_events, res_b.audit_events):
        assert ev_a.source_type == LootSourceType.ARTIFACT_STRONGBOX
        assert ev_a.event_type == "LINE_COUNT_ROLL"
        assert ev_a.roll_value == ev_b.roll_value
        assert ev_a.outcome == ev_b.outcome


def test_prng_stream_isolation_from_global_random():
    """Loot generation is completely isolated from Python's global random module state."""
    seed = 777888999

    # 1. First run with arbitrary global random state
    random.seed(12345)
    _ = [random.random() for _ in range(100)]
    engine_1 = ArtifactEngine(rng=PythonRNG(seed=seed))
    res_1 = run_domain_of_blessing(use_condensed=True, engine=engine_1)

    # 2. Second run with violently altered global random state
    random.seed(999999)
    _ = [random.randint(0, 1000) for _ in range(500)]
    engine_2 = ArtifactEngine(rng=PythonRNG(seed=seed))
    res_2 = run_domain_of_blessing(use_condensed=True, engine=engine_2)

    assert len(res_1.artifacts) == len(res_2.artifacts)
    assert res_1.count_4star_fodder == res_2.count_4star_fodder
    for a1, a2 in zip(res_1.artifacts, res_2.artifacts):
        assert a1.slot == a2.slot
        assert a1.main_stat == a2.main_stat
        assert [s.stat_type for s in a1.substats] == [s.stat_type for s in a2.substats]


def test_multi_seed_divergence():
    """Different seeds produce divergent simulation outputs."""
    engine_a = ArtifactEngine(rng=PythonRNG(seed=1001))
    engine_b = ArtifactEngine(rng=PythonRNG(seed=9999))

    res_a = run_domain_of_blessing(use_condensed=True, engine=engine_a)
    res_b = run_domain_of_blessing(use_condensed=True, engine=engine_b)

    # High probability of divergence across 2 cycles of secondary 5★, fodder, sets, lines, and stats
    has_diff = (
        len(res_a.artifacts) != len(res_b.artifacts)
        or res_a.count_4star_fodder != res_b.count_4star_fodder
        or any(a.slot != b.slot for a, b in zip(res_a.artifacts, res_b.artifacts))
        or any(a.main_stat != b.main_stat for a, b in zip(res_a.artifacts, res_b.artifacts))
    )
    assert has_diff, "Independent seeds unexpectedly generated identical outputs."
