# P3 Artifact Loot Sources Specification

**Document Version:** 1.3.0 (Post-Cross-Review Resolution)  
**Target Game Version:** Genshin Impact Version 7.1 (Reaffirmed)  
**Status:** SPECIFICATION COMPLETE — AWAITING FINAL PROJECT LEAD ACCEPTANCE  
**Reference Documents:** `AGENTS.md`, `docs/PROJECT_PLAN.md` Section 4.5 & 6 (P3), `docs/SPEC_ARTIFACT.md`, `docs/research/artifact_validation.md`, `docs/adr/ADR-002-loot-sources-and-4star-abstraction.md`

---

## 1. Objective

This document formalizes the implementation specification for **Phase P3 — Artifact Loot Sources** (Domain of Blessing and Artifact Strongbox) in the Genshin Simulator, fully resolving cross-review findings (F1–F6).

The specification defines:
1. **Mathematical drop models** for Level 90 Domains of Blessing (20 Original Resin and 40 Condensed Resin) and Artifact Strongbox (Mystic Offering 3-to-1 sacrifice).
2. **Unified, consistent Fidelity Architecture** coordinating static configuration catalog checking with runtime execution, strictly prohibiting silent bypasses of unverified constants in `STRICT` mode (`AGENTS.md` Section 5.2).
3. **Rigorous Evidence Auditing** reclassifying 4★ fodder quantities and initial line count ratios to `INFERRED`, documenting exact locators, sample sizes, and source limitations.
4. **Three-Layer Decoupled Testing Architecture** separating determinism/PRNG tests, domain invariant tests, and statistical distribution tests.
5. **Dual-Gate Pre-Registered Statistical Acceptance Criteria** combining Bonferroni-corrected Chi-square tests (without requiring test independence) with strict $4\sigma$ univariate binomial boundaries.
6. **Sequential Single-PRNG Stream Policy** for Condensed Resin, formalizing reward aggregation and audit event ordering.
7. **P3.2 Deliverable Boundaries**: Explicitly specifying configuration schemas, keys, and provenance formats for implementation in Phase P3.2, with zero runtime configuration edits during Phase P3.1.

---

## 2. Scope & Non-Goals

### 2.1 In-Scope Capabilities
1. **Domain of Blessing (`run_domain_of_blessing`)**:
   - Supports Level 90 (Tier IV / highest difficulty) artifact domains.
   - Consumes 20 Original Resin (1 run) or 1 Condensed Resin (2 sequential independent runs).
   - Generates artifacts from exactly two configured 5★ sets with empirical 50/50 allocation ($p = 0.500$).
   - Computes and returns 4★ fodder counts (`count_4star_fodder: int`) using empirical distributions.
   - Generates 5★ artifacts with Domain-specific initial substat line count distribution ($80\%$ 3-line vs $20\%$ 4-line).
2. **Artifact Strongbox / Mystic Offering (`craft_strongbox`)**:
   - Implements 3-to-1 conversion ratio: exactly 3 5★ artifacts sacrificed yield 1 new 5★ artifact of the chosen target set.
   - Enforces strict input validation on `sacrifice_artifacts: List[Artifact]` (type, minimum count, multiple of 3, rarity 5★).
   - Generates 5★ artifacts with Strongbox-specific empirical initial substat line count distribution ($66\%$ 3-line vs $34\%$ 4-line, ~2:1 ratio).
   - Generates 100% of outputs from the selected `target_set`.
3. **Core Engine Integration**:
   - Reuses `ArtifactEngine.generate_artifact()` for generating concrete 5★ `Artifact` instances, ensuring full compliance with slot distributions, main stat tables, substat candidate weights, roll tiers, and state invariants defined in `SPEC_ARTIFACT.md`.
4. **Audit Logging & Deterministic PRNG Invariant**:
   - Every stochastic decision routes strictly through `RNGInterface` (`PythonRNG`).
   - Every transaction returns structured `LootAuditEvent` records capturing rolls, thresholds, outcomes, and evidence tiers.

### 2.2 Out-of-Scope (Non-Goals)
- **Runtime Configuration Modification in P3.1**: Creating `config/artifacts/loot_sources.json` or editing `config/artifacts/provenance.json` is strictly deferred to Phase P3.2 (F2). P3.1 provides only the declarative specification.
- **Full 4★ Artifact Entity Modeling**: 4★ artifacts are not modeled as full `Artifact` objects with substats, roll histories, enhancement tiers, or leveling mechanics. They are represented purely as an integer count of fodder units (`count_4star_fodder`) per Decision 1A.
- **World Bosses (40 Resin) & Weekly Bosses / Trounce Domains (30/60 Resin)**: Deferred to subsequent progression phases. Their drop pools contain character ascension materials, billets, and non-standardized artifact rates.
- **Spiral Abyss Reliquaries**: Deferred to endgame challenge simulation modules.
- **Artifact Transmuter & Sanctifying Elixir (Phase P4)**: Scheduled for Phase P4.
- **Artifact Reshaping & Hallowed Exegesis (Phase P4)**: Remains strictly **BLOCKED** per `docs/OPEN_QUESTIONS.md:OQ-03`.
- **Capturing Radiance (Phase P5)**: Remains strictly **BLOCKED** from the default engine per `docs/OPEN_QUESTIONS.md:OQ-01`.
- **Resin Timers / Account Economy**: Real-time accumulation and Primogem resin refreshes belong to account/session state layers.

---

## 3. Epistemological Boundary & Evidence Audit

Every game mechanic, parameter, and rule in Phase P3 is classified strictly according to `AGENTS.md` Section 5:

| Category | Definition | Mechanics in Phase P3 |
| :--- | :--- | :--- |
| **VERIFIED (Level A)** | Explicitly documented in official HoYoverse in-game help menus, domain descriptions, or official announcements. | - Domain resin cost: 20 Original Resin.<br>- Condensed Resin equivalence: 40 Original Resin = exactly 2x domain rewards.<br>- Domain Level 90 pool: exactly 2 5★ artifact sets.<br>- Domain Level 90 baseline drop: at least 1 5★ artifact guaranteed per 20 resin.<br>- Strongbox exchange ratio: 3 5★ artifacts consumed $\to$ 1 5★ artifact crafted.<br>- Strongbox sacrifice rule: 5★ artifacts only, exact multiple of 3.<br>- Strongbox set outcome: 100% of selected set.<br>- 4★ artifact inclusion: 4★ artifacts are confirmed present in the domain reward pool. |
| **INFERRED (Level C)** | Derived from large-scale crowdsourced community datasets; unconfirmed by server source code. | - Domain set distribution: 50% Set A / 50% Set B ($1:1$).<br>- Domain secondary 5★ drop rate: $\approx 6.54\%$ ($p \approx 0.0654$, mean $\approx 1.065$ 5★ per 20 resin).<br>- Domain 4★ fodder quantity: 2 to 3 per 20 resin (empirical baseline 2 + $\approx 48\%$ chance of 3rd, mean $\approx 2.48$).<br>- Domain initial line count distribution: $80\%$ 3-line vs $20\%$ 4-line ($4:1$).<br>- Strongbox initial line count distribution: $66\%$ 3-line vs $34\%$ 4-line (~$2:1$, empirical $65.8\% : 34.2\%$). Approximate empirical model.<br>- Slot distribution: uniform 20% across all 5 slots ($1:1:1:1:1$). |
| **ASSUMED** | Simulator engineering convention necessary to implement the simulator. | - 4★ Fodder Abstraction: integer counter `count_4star_fodder` instead of full entity graph (Decision 1A).<br>- Two-Layer Fidelity Policy: strict mode requires verified parameters; best_effort permits inferred empirical models.<br>- Condensed Resin single-PRNG stream advancement: executing 2 sequential cycles using one RNG stream.<br>- Strongbox input validation enforcing `List[Artifact]` with `len % 3 == 0` and `rarity == 5`. |
| **BLOCKED** | Disputed or unestablished internals prohibited from running in the default engine. | - Artifact Reshaping milestones (`OQ-03`).<br>- Capturing Radiance internal Markov transition kernel (`OQ-01`). |

### 3.1 Strict Separation of 4★ Fodder Mechanics (F3)
To ensure complete intellectual honesty:
1. **Official Reality (`VERIFIED`, Level A)**: In-game domain descriptions confirm that 4★ artifacts belong to the drop table. HoYoverse has **never published an exact guaranteed minimum number of 4★ drops per run**.
2. **Empirical Distribution (`INFERRED`, Level C)**: Large-scale player drop sheets (Genshin Data Gathering Team) observe that Level 90 domains drop either 2 or 3 4★ artifacts per 20 resin (baseline 2 + ~48% chance of a 3rd, average ~2.48). This numerical distribution is strictly **`INFERRED`**.
3. **Architectural Choice (`ASSUMED`)**: The decision to represent 4★ drops as an integer count (`count_4star_fodder: int`) rather than instantiating full 4★ `Artifact` entity graphs is an engineering abstraction (Option 1A) justified by the fact that endgame players use 4★ items solely as enhancement fodder.

### 3.2 Strongbox 66/34 Initial Line Model (F4)
- In-game rules for Mystic Offering specify ONLY the 3:1 exchange ratio, 5★ rarity constraint, and target set selection (`VERIFIED`, Level A).
- HoYoverse has **never published server-side line count weights for Strongbox**.
- The 66% (3-line) / 34% (4-line) ratio is an **explicitly rounded approximate empirical model** derived from player datasets ($N = 15,280$, observed $65.8\% : 34.2\%$, NGA TID: 33220261).
- It is prohibited in `STRICT` mode and permitted only in `BEST_EFFORT` and `EXPERIMENTAL` modes.

---

## 4. Fidelity Architecture & Strict-Mode Execution Policy (F1)

`AGENTS.md` Section 5.2 establishes:
> *"UNKNOWN is never usable by the engine. A rule whose evidence is below the active mode must be refused with a clear error, not silently defaulted."*

To guarantee complete consistency between static configuration loading and runtime execution without silent bypasses, the simulator defines a unified two-layer fidelity contract:

```
                      ┌───────────────────────────────────────────┐
                      │             FidelityMode                  │
                      └─────────────────────┬─────────────────────┘
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               ▼                            ▼                            ▼
      ┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
      │     STRICT      │          │   BEST_EFFORT   │          │  EXPERIMENTAL   │
      └────────┬────────┘          └────────┬────────┘          └────────┬────────┘
               │                            │                            │
      • Catalog checking:          • Catalog checking:          • Catalog checking:
        Refuses any INFERRED         Accepts VERIFIED +           Accepts VERIFIED +
        constant in config           INFERRED constants           INFERRED + ASSUMED
      • Runtime loot engine:       • Runtime loot engine:       • Runtime loot engine:
        REFUSES execution            Executes empirical           Executes custom/
        with FidelityViolationError  models (6.54% 2nd 5★,        research strategies
        if required drop or          80/20 & 66/34 lines,         • Label: EXPERIMENTAL
        affix rules are INFERRED     4★ fodder 2-3)
      • Label: N/A (Refused)       • Label: INFERRED
```

### 4.1 Layer 1: Configuration Catalog Fidelity Validation
- When `load_and_validate_artifact_config(config_dir, fidelity_mode="strict")` runs, `validate_config_provenance_fidelity` scans all records in `provenance.json`.
- Because `config/artifacts/loot_sources.json` contains `INFERRED` constants (such as `secondary_5star_probability = 0.0654`, `set_distribution_weights = 50/50`, `initial_line_count_weights = 80/20`), validating the configuration catalog in `STRICT` mode **will report violations**, exactly as it reports `substats.CRIT_RATE` (verified in `tests/test_config_schema.py:test_provenance_strict_mode_rejects_inferred_constants`).
- **Invariant:** The configuration loader will never silently bypass, downgrade, or ignore `INFERRED` constants in `STRICT` mode.

### 4.2 Layer 2: Runtime Execution & Refusal Contract
- At runtime, `run_domain_of_blessing` and `craft_strongbox` receive `fidelity_mode: LootFidelityMode`.
- **Behavior in `LootFidelityMode.STRICT`**:
  - In the real game, an artifact drop requires drawing a set (50/50), an initial line count (80/20 or 66/34), and candidate substats (6/4/3). None of these server parameters have ever been officially disclosed by HoYoverse.
  - **Contract Invariant:** Strict mode **cannot and must not silently bypass catalog validation failures** or synthesize unverified numbers.
  - **Availability:** Strict runtime execution is **UNAVAILABLE** in the standard engine until a verified-only configuration baseline is formally supplied.
  - If a caller invokes `run_domain_of_blessing` or `craft_strongbox` with `fidelity_mode=LootFidelityMode.STRICT` against production configurations containing `INFERRED` parameters, the engine **must raise an explicit domain exception**:
    ```python
    class FidelityViolationError(ValueError):
        """Raised when execution cannot proceed within the requested fidelity constraints."""
        pass
    ```
    ```python
    raise FidelityViolationError(
        f"Cannot execute {source_type.value} in STRICT fidelity mode: required parameters "
        f"(set_distribution, initial_lines, substat_weights) have evidence level INFERRED. "
        f"STRICT mode permits only VERIFIED rules. Use BEST_EFFORT mode for empirical simulation."
    )
    ```
  - **Entity Internals Labeling Rule (F1):** Even if a verified drop-count baseline is supplied in a future phase (e.g. guaranteeing exactly 1 5★ drop), **artifact entity internals (substat types, roll tiers, main stat draws) remain INFERRED**. The overall result payload must **NEVER be described as fully VERIFIED**; its `weakest_evidence_level` must honestly reflect the weakest constituent parameter (`INFERRED`). This rule eliminates any contradiction between a verified drop quantity and unverified entity internals, ensuring strict fidelity mode integrity.
- **Behavior in `LootFidelityMode.BEST_EFFORT` (Default Operational Mode)**:
  - Permits `VERIFIED` and `INFERRED` evidence levels.
  - Per 20 Original Resin in Level 90 Domain: yields 1 guaranteed 5★ artifact plus an independent Bernoulli trial ($p = 0.0654$) for a second 5★ artifact (yielding 1 or 2 5★ artifacts, average $\approx 1.065$).
  - 4★ fodder count: 2 baseline plus a Bernoulli trial ($p = 0.48$) for a 3rd fodder unit (yielding 2 or 3 4★ fodder, average $\approx 2.48$).
  - Domain initial line count: 80% 3-line vs 20% 4-line.
  - Strongbox initial line count: 66% 3-line vs 34% 4-line (~2:1 ratio).
  - Reports `weakest_evidence_level = "INFERRED"`.
- **Behavior in `LootFidelityMode.EXPERIMENTAL`**:
  - Permits `VERIFIED`, `INFERRED`, and `ASSUMED` levels.
  - Allows research parameter overrides. Reports `weakest_evidence_level = "EXPERIMENTAL"` or `"ASSUMED"`.

---

## 5. Domain Model & Schemas

### 5.1 Enums & Types

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any

class LootFidelityMode(str, Enum):
    STRICT = "STRICT"
    BEST_EFFORT = "BEST_EFFORT"
    EXPERIMENTAL = "EXPERIMENTAL"

class LootSourceType(str, Enum):
    DOMAIN_OF_BLESSING = "DOMAIN_OF_BLESSING"
    ARTIFACT_STRONGBOX = "ARTIFACT_STRONGBOX"
```

### 5.2 Audit Event Schema

```python
@dataclass(frozen=True)
class LootAuditEvent:
    """Audit record capturing an atomic stochastic step in a loot transaction."""
    cycle_index: int                       # 0 (or 1 for condensed resin second cycle)
    source_type: LootSourceType            # DOMAIN_OF_BLESSING or ARTIFACT_STRONGBOX
    event_type: str                        # "SET_SELECTION", "SECONDARY_5STAR_ROLL", "FODDER_ROLL", "LINE_COUNT_ROLL"
    roll_value: Optional[float]            # Drawn uniform random float in [0, 1), if applicable
    threshold: Optional[float]             # Probability threshold tested against, if applicable
    outcome: Any                           # Chosen outcome (e.g. set_id, initial_lines, count)
    evidence_level: str                    # Evidence tier of the evaluated rule
```

### 5.3 Domain Drop Result Schema

```python
@dataclass(frozen=True)
class DomainDropResult:
    """Represents the complete reward output of a Domain of Blessing run."""
    domain_id: str
    artifacts: List[Artifact]              # Concrete 5★ Artifact instances generated
    count_4star_fodder: int                # Abstracted count of 4★ fodder artifacts (Decision 1A)
    resin_spent: int                       # 20 (normal) or 40 (condensed)
    runs_executed: int                     # 1 (normal) or 2 (condensed)
    fidelity_mode: LootFidelityMode
    weakest_evidence_level: str            # "INFERRED" in best_effort, "EXPERIMENTAL" in experimental
    source_type: LootSourceType = LootSourceType.DOMAIN_OF_BLESSING
    audit_events: List[LootAuditEvent] = field(default_factory=list)
```

### 5.4 Strongbox Result Schema

```python
@dataclass(frozen=True)
class StrongboxResult:
    """Represents the complete output of an Artifact Strongbox craft."""
    target_set: str
    artifacts: List[Artifact]              # Concrete 5★ Artifact instances generated
    sacrificed_count: int                  # Total 5★ artifacts consumed (multiple of 3)
    fidelity_mode: LootFidelityMode
    weakest_evidence_level: str            # "INFERRED" (due to 66/34 line distribution)
    source_type: LootSourceType = LootSourceType.ARTIFACT_STRONGBOX
    audit_events: List[LootAuditEvent] = field(default_factory=list)
```

---

## 6. Execution Logic & State Machines

### 6.1 Domain of Blessing Execution Flow (F6)

The function `run_domain_of_blessing` executes according to the following deterministic flow:

```
                     run_domain_of_blessing()
                                │
               ┌────────────────┴────────────────┐
               ▼                                 ▼
      use_condensed = False             use_condensed = True
         (runs = 1)                        (runs = 2)
         (resin = 20)                      (resin = 40)
               │                                 │
               └────────────────┬────────────────┘
                                │
                        Check Fidelity Mode:
               ┌────────────────┴────────────────┐
               ▼                                 ▼
         [STRICT mode]                  [BEST_EFFORT mode]
     Raise FidelityViolationError     Execute Empirical Pipeline
                                                 │
                                     Single Injected RNG Stream:
                                     Cycle 0 runs sequentially,
                                     followed by Cycle 1 (if condensed)
                                                 │
                                                 ▼
                                     Aggregate into DomainDropResult
```

#### Detailed Execution Steps:
1. **Input Validation**:
   - `sets` must be a tuple/list of exactly 2 distinct set identifiers (`len(set(sets)) == 2`). If invalid, raise `ValueError("Domain requires exactly 2 distinct 5★ sets.")`.
   - `fidelity_mode`: If `LootFidelityMode.STRICT`, raise `FidelityViolationError` immediately per Section 4.2.
   - `engine` must be an initialized `ArtifactEngine`. If `None`, instantiate default engine.
2. **Run Count & Resin Resolution**:
   - If `use_condensed=True`: `runs = 2`, `resin_spent = 40`.
   - If `use_condensed=False`: `runs = 1`, `resin_spent = 20`.
3. **Sequential Single-PRNG Stream Policy (F6)**:
   - For Condensed Resin (`runs = 2`), the engine advances **one continuous injected PRNG stream** sequentially across Cycle 0 (`cycle_index = 0`) and Cycle 1 (`cycle_index = 1`).
   - The PRNG is **never re-seeded or cloned between cycles**. Cycle 1 consumes entropy directly from where Cycle 0 left off.
   - *Epistemological Boundary*: This sequential advancement is a simulator implementation decision (`ASSUMED`) guaranteeing determinism and auditability; it does not claim to prove server-internal RNG dispatch.
4. **Per-Cycle Evaluation (executed for `cycle_index = 0` to `runs - 1`)**:
   - **5★ Quantity Resolution**:
     - Guaranteed baseline: 1.
     - Draw uniform float $r_5 \in [0, 1)$ via `prob_engine.rng.random_float()`.
     - If $r_5 < 0.0654$: `count_5star = 2`, else `1`.
     - Log event: `LootAuditEvent(cycle_index, DOMAIN_OF_BLESSING, "SECONDARY_5STAR_ROLL", r_5, 0.0654, count_5star, "INFERRED")`.
   - **4★ Fodder Quantity Resolution**:
     - Baseline: 2.
     - Draw uniform float $r_4 \in [0, 1)$ via `prob_engine.rng.random_float()`.
     - If $r_4 < 0.48$: `fodder = 3`, else `2`.
     - Log event: `LootAuditEvent(cycle_index, DOMAIN_OF_BLESSING, "SECONDARY_FODDER_ROLL", r_4, 0.48, fodder, "INFERRED")`.
   - **5★ Artifact Generation**:
     - For $i = 1 \dots \text{count\_5star}$:
       - **Set Choice**: Draw uniform float $r_{\text{set}} \in [0, 1)$. If $r_{\text{set}} < 0.50$, `chosen_set = sets[0]`, else `sets[1]`.
         - Log event: `LootAuditEvent(cycle_index, DOMAIN_OF_BLESSING, "SET_SELECTION", r_set, 0.50, chosen_set, "INFERRED")`.
       - **Initial Line Count**: Draw uniform float $r_{\text{lines}} \in [0, 1)$. If $r_{\text{lines}} < 0.80$, `chosen_lines = 3`, else `4`.
         - Log event: `LootAuditEvent(cycle_index, DOMAIN_OF_BLESSING, "LINE_COUNT_ROLL", r_lines, 0.80, chosen_lines, "INFERRED")`.
       - **Generate Entity**: Call `engine.generate_artifact(set_id=chosen_set, initial_lines=chosen_lines)`.
5. **Exact Reward Aggregation & Audit Event Ordering (F6)**:
   - `artifacts = cycle_0.artifacts + cycle_1.artifacts` (Cycle 0 artifacts strictly precede Cycle 1 artifacts).
   - `count_4star_fodder = cycle_0.fodder + cycle_1.fodder`.
   - `resin_spent = 40` (or 20 for single run).
   - `runs_executed = runs` (2 or 1).
   - `audit_events = cycle_0.audit_events + cycle_1.audit_events` (chronological order).
   - Return `DomainDropResult` with `weakest_evidence_level = "INFERRED"`.

### 6.2 Artifact Strongbox Execution Flow

The function `craft_strongbox` executes according to the following deterministic flow:

```
                       craft_strongbox()
                                │
                     Validate Sacrifice Inputs:
                     1. isinstance(sacrifice_artifacts, list)
                     2. len(sacrifice_artifacts) >= 3
                     3. len(sacrifice_artifacts) % 3 == 0
                     4. all(a.rarity == 5 for a in sacrifice_artifacts)
                     5. target_set is valid
                     6. Check fidelity_mode != STRICT
                                │
                                ▼
                     Calculate Output Quantity:
                     Q = len(sacrifice_artifacts) // 3
                                │
                     For each of the Q outputs:
                     1. Set: Strictly target_set (100%)
                     2. Initial lines: 66% 3-line / 34% 4-line (~2:1 empirical)
                     3. Delegate to ArtifactEngine
                                │
                                ▼
                     Aggregate into StrongboxResult
```

#### Detailed Execution Steps:
1. **Input Validation (Decision 3A)**:
   - `sacrifice_artifacts` must be a list of `Artifact` instances. If not, raise `TypeError("sacrifice_artifacts must be a list of Artifact instances.")`.
   - If `len(sacrifice_artifacts) < 3`: raise `ValueError(f"Strongbox requires at least 3 artifacts to craft, got {len(sacrifice_artifacts)}.")`.
   - If `len(sacrifice_artifacts) % 3 != 0`: raise `ValueError(f"Sacrifice count ({len(sacrifice_artifacts)}) must be an exact multiple of 3.")`.
   - For every `artifact` in `sacrifice_artifacts`:
     - If `artifact.rarity != 5`: raise `ValueError(f"Strongbox only accepts 5★ artifacts; artifact '{artifact.id}' has rarity {artifact.rarity}.")`.
   - If `target_set` is empty or whitespace: raise `ValueError("target_set must not be empty.")`.
   - If `fidelity_mode == LootFidelityMode.STRICT`: raise `FidelityViolationError` per Section 4.2.
2. **Output Count**:
   - $Q = \text{len}(sacrifice\_artifacts) // 3$.
3. **Artifact Generation**:
   - For $j = 1 \dots Q$:
     - **Set**: Strictly `target_set` (100% deterministic).
     - **Initial Line Count**: Draw uniform float $r_{\text{lines}} \in [0, 1)$ via `prob_engine.rng.random_float()`.
       - If $r_{\text{lines}} < 0.66$: `chosen_lines = 3`, else `4`.
       - Log event: `LootAuditEvent(j, ARTIFACT_STRONGBOX, "LINE_COUNT_ROLL", r_lines, 0.66, chosen_lines, "INFERRED")`.
     - **Generate Entity**: Call `engine.generate_artifact(set_id=target_set, initial_lines=chosen_lines)`.
4. **Aggregate & Return**:
   - Return `StrongboxResult` containing the $Q$ crafted artifacts, `sacrificed_count = len(sacrifice_artifacts)`, and weakest evidence level (`INFERRED`).

---

## 7. Configuration Specification (Phase P3.2 Deliverables Specification) (F2)

> **Important Boundary Rule (F2):** No configuration files are created or modified during Phase P3.1. The definitions below specify the required schema, keys, types, and provenance fields to be implemented in Phase P3.2.

### 7.1 Required Schema for `config/artifacts/loot_sources.json` (P3.2 Deliverable)
```json
{
  "domain_of_blessing": {
    "cost_original_resin": 20,
    "cost_condensed_resin": 40,
    "condensed_multiplier": 2,
    "featured_set_count": 2,
    "set_distribution_weights": {
      "set_a": 50,
      "set_b": 50
    },
    "guaranteed_5star_quantity": 1,
    "secondary_5star_probability": 0.0654,
    "fodder_4star_baseline": 2,
    "fodder_4star_secondary_probability": 0.48,
    "initial_line_count_weights": {
      "3": 80,
      "4": 20
    }
  },
  "artifact_strongbox": {
    "sacrifice_ratio": 3,
    "allowed_sacrifice_rarity": 5,
    "initial_line_count_weights": {
      "3": 66,
      "4": 34
    }
  }
}
```

### 7.2 Required Provenance Catalog Entries for `config/artifacts/provenance.json` (P3.2 Deliverable)

| Parameter Key | Value | Evidence Level | Primary Source | Exact Locator / Reference | Valid From Version | What the Source Proves vs Does NOT Prove |
| :--- | :---: | :---: | :--- | :--- | :---: | :--- |
| `domain.cost_original_resin` | 20 | `VERIFIED` | In-Game Client UI | Domain Entrance / Claim Rewards Prompt | 1.0 | **Proves:** Fixed resin cost to claim domain rewards.<br>**Does NOT prove:** Internal server transaction scheduling. |
| `domain.cost_condensed_resin` | 40 | `VERIFIED` | In-Game Client UI | Alchemy Crafting / Domain Claim Prompt | 1.1 | **Proves:** 1 Condensed Resin crafted from 40 Original Resin + 1 Crystal Core. |
| `domain.condensed_multiplier` | 2 | `VERIFIED` | In-Game Tutorial | Help Menu: *Condensed Resin* | 1.1 | **Proves:** Consuming 1 Condensed Resin yields exactly double the reward drops of a 20-resin run. |
| `domain.featured_set_count` | 2 | `VERIFIED` | In-Game Domain Details | Domain Entrance: *Artifacts* reward list | 1.0 | **Proves:** Every Level 90 Domain of Blessing drops exactly 2 distinct 5★ sets. |
| `domain.set_distribution_weights` | 50 / 50 | `INFERRED` | Genshin Data Gathering Team | Google Sheet: *Artifact Drop Rates*, Tab: *Domain Rewards*, Section *Set Distribution* ($N > 100,000$) | 1.0 | **Proves:** Empirical parity across $>100,000$ recorded drops ($49.98\% : 50.02\%$).<br>**Does NOT prove:** Internal server integer weights (e.g. 50/50 vs 1/1 vs 100/100). |
| `domain.guaranteed_5star_quantity` | 1 | `VERIFIED` | In-Game Client UI | Level 90 Domain of Blessing Description & Reward Preview | 1.0 | **Proves:** At least one 5★ artifact is guaranteed per 20 Original Resin at highest difficulty. |
| `domain.secondary_5star_probability` | 0.0654 | `INFERRED` | Genshin Data Gathering Team | Google Sheet: *Artifact Drop Rates*, Tab: *Artifact Quantity*, column *2x 5★ Rate* ($N = 48,932$) | 1.0 | **Proves:** Empirical secondary drop rate ($\approx 6.54\% \pm 0.22\%$, mean $\approx 1.065$ 5★ per 20 resin).<br>**Does NOT prove:** Server drop roll formula; prohibited in `STRICT` mode. |
| `domain.fodder_4star_baseline` | 2 | `INFERRED` | Genshin Data Gathering Team | Google Sheet: *Artifact Drop Rates*, Tab: *Artifact Quantity*, column *4★ Drops* | 1.0 | **Proves:** Minimum 2 4★ artifacts observed per 20 resin at Level 90 in player datasets.<br>**Does NOT prove:** Official developer guarantee (official text only declares 4★ in pool). Reclassified to `INFERRED` (F3). |
| `domain.fodder_4star_secondary_probability` | 0.48 | `INFERRED` | Genshin Data Gathering Team | Google Sheet: *Artifact Drop Rates*, Tab: *Artifact Quantity*, column *4★ Drops* | 1.0 | **Proves:** $\approx 48\%$ chance of a 3rd 4★ artifact (mean $\approx 2.48$). |
| `domain.initial_line_count_weights` | 80 / 20 | `INFERRED` | Genshin Data Gathering Team | Sheet: *Artifact Quality & Affixes*, Tab: *Artifact Quality (Domains)* ($N = 34,228$) | 1.0 | **Proves:** Empirical 80% 3-line vs 20% 4-line for Domain drops ($79.9\% : 20.1\%$).<br>**Does NOT prove:** Universal rule for all sources. |
| `slot_distribution` | Uniform 20% | `INFERRED` | Genshin Data Gathering Team | Google Sheet: *Artifact Drop Rates*, Tab: *Slot Distribution* ($N > 100,000$) | 1.0 | **Proves:** Equal $20.0\% \pm 0.2\%$ frequency across all 5 slots (1:1:1:1:1).<br>**Does NOT prove:** Server integer weights. |
| `strongbox.sacrifice_ratio` | 3 | `VERIFIED` | In-Game Mystic Offering UI | Crafting Bench: *Mystic Offering* | 2.0 | **Proves:** Exactly 3 5★ artifacts consumed per 1 crafted artifact. |
| `strongbox.allowed_sacrifice_rarity` | 5 | `VERIFIED` | In-Game Mystic Offering UI | Crafting Bench: *Mystic Offering* | 2.0 | **Proves:** Only 5★ rarity artifacts can be placed into Mystic Offering. |
| `strongbox.initial_line_count_weights` | 66 / 34 | `INFERRED` | NGA Research Thread / Genshin Data Gathering | NGA TID: 33220261 (*圣遗物词条分布汇总一图流*) / Sheet: *Strongbox Quality* ($N = 15,280$) | 2.0 | **Proves:** Empirical $\approx 2:1$ ratio ($65.8\% : 34.2\%$). Rounded empirical parameter; NOT an official game rule. Prohibited in `STRICT` mode (F4). |

---

## 8. Dual-Gate Pre-Registered Statistical Acceptance Criteria (F5)

### 8.1 Dual-Gate Architecture
Statistical verification requires satisfying **two independent, co-equal, mandatory acceptance gates** ($\text{PASS} = \text{Gate}_1 \land \text{Gate}_2$). Neither gate is diagnostic; a failure on either gate constitutes an immediate test FAIL:

```
               Simulation Output Dataset (N runs)
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       [GATE 1: Chi-Square]             [GATE 2: 4σ Bounds]
       Multivariate Omnicategorical     Univariate Binomial Bounds
       Goodness-of-Fit                  Strict Frequency Bounds
       (Bonferroni α_adj = 0.000333)    (|p̂ - p| ≤ 4 * SE)
               │                               │
               └───────────────┬───────────────┘
                               │
                               ▼
                    PASS = Gate 1 AND Gate 2
```

### 8.2 Gate 1: Chi-Square Goodness-of-Fit Gate (Omnicategorical)
- **Purpose**: Evaluates overall distribution shape across multi-bin categorical outcomes.
- **Formula**:
  $$\chi^2 = \sum_{i=1}^{k} \frac{(O_i - E_i)^2}{E_i}$$
  where $O_i$ is observed count, $E_i = N \times p_i$ is expected theoretical count.
- **Hypothesis Family**: $M = 3$ multi-categorical distributions evaluated simultaneously:
  1. 5 Artifact Slots ($k = 5, df = 4$, expected $p_i = 0.20$ each)
  2. Domain Set Allocation ($k = 2, df = 1$, expected $p_1 = 0.50, p_2 = 0.50$)
  3. Domain Initial Line Count ($k = 2, df = 1$, expected $p_3 = 0.80, p_4 = 0.20$)
- **Family-Wise Error Rate & Bonferroni Control (F5)**:
  - By Boole's inequality (union bound):
    $$P\left(\bigcup_{i=1}^M \{ \text{Reject } H_{0,i} \mid H_{0,i} \text{ true}\} \right) \le \sum_{i=1}^M P(\text{Reject } H_{0,i} \mid H_{0,i} \text{ true}) = M \cdot \alpha_{\text{adj}}$$
  - Setting $\alpha_{\text{adj}} = \frac{\alpha_{\text{family}}}{M} = \frac{0.001}{3} \approx 0.0003333$ guarantees family-wise error rate $\le 0.001$ **without requiring statistical independence between tests**.
- **Pre-Registered Critical Thresholds**:
  - For $df = 4$ (5 slots): $\chi^2_{\text{crit}}(4, 0.000333) = 21.110$. Requirement: $\chi^2_{\text{calc}} < 21.110$.
  - For $df = 1$ (2 bins): $\chi^2_{\text{crit}}(1, 0.000333) = 12.870$. Requirement: $\chi^2_{\text{calc}} < 12.870$.

### 8.3 Gate 2: $4\sigma$ Local Binomial Boundary Gate (`PROJECT_PLAN.md:180`)
- **Purpose**: Strictly enforces that no individual proportion deviates by more than $4$ standard errors from specification:
  $$|\hat{p} - p| \le 4 \times \text{SE}(p) = 4 \times \sqrt{\frac{p(1-p)}{N}}$$
- **Four Scalar Targets Evaluated**:
  1. Domain 50/50 Set Drop Rate ($p = 0.500$)
  2. Domain 4-Line Initial Rate ($p = 0.200$)
  3. Strongbox 4-Line Initial Rate ($p = 0.340$)
  4. Secondary 5★ Drop Rate in `BEST_EFFORT` ($p = 0.0654$)

### 8.4 Pre-Registered Sample Sizes, Seeds & Tolerances

| Metric Evaluated | Expected Proportion $p$ | Fast Suite ($N = 100,000$, `seed = 20261020`) | Heavy Suite ($N = 1,000,000$, `seed = 20261021`) |
| :--- | :---: | :---: | :---: |
| **Domain 50/50 Set** | $0.500000$ | $4\sigma = \pm 0.006325 \implies [49.3675\%, 50.6325\%]$ | $4\sigma = \pm 0.002000 \implies [49.8000\%, 50.2000\%]$ |
| **Domain 4-Line Count** | $0.200000$ | $4\sigma = \pm 0.005060 \implies [19.4940\%, 20.5060\%]$ | $4\sigma = \pm 0.001600 \implies [19.8400\%, 20.1600\%]$ |
| **Strongbox 4-Line Count** | $0.340000$ | $4\sigma = \pm 0.005992 \implies [33.4008\%, 34.5992\%]$ | $4\sigma = \pm 0.001895 \implies [33.8105\%, 34.1895\%]$ |
| **Secondary 5★ (`BEST_EFFORT`)** | $0.065400$ | $4\sigma = \pm 0.003127 \implies [6.2273\%, 6.8527\%]$ | $4\sigma = \pm 0.000989 \implies [6.4411\%, 6.6389\%]$ |
| **Gate 1: Chi-Square 5 Slots** | $0.20$ each | $\chi^2_{\text{calc}} < 21.110$ ($df = 4, p > 0.000333$) | $\chi^2_{\text{calc}} < 21.110$ ($df = 4, p > 0.000333$) |
| **Gate 1: Chi-Square Set Split** | $0.50$ each | $\chi^2_{\text{calc}} < 12.870$ ($df = 1, p > 0.000333$) | $\chi^2_{\text{calc}} < 12.870$ ($df = 1, p > 0.000333$) |
| **Gate 1: Chi-Square Lines** | $0.80 / 0.20$ | $\chi^2_{\text{calc}} < 12.870$ ($df = 1, p > 0.000333$) | $\chi^2_{\text{calc}} < 12.870$ ($df = 1, p > 0.000333$) |

---

## 9. Three-Layer Decoupled Testing Architecture (F5)

To prevent conflation between statistical convergence and algorithmic correctness, test suites are strictly decoupled into three layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   THREE-LAYER TESTING ARCHITECTURE                     │
├────────────────────────────────┬───────────────────────────────────────┤
│ Layer 1: Determinism & PRNG    │ Bit-for-bit replayability from seed;  │
│ Reproducibility Tests          │ state save/restore; global isolation  │
├────────────────────────────────┼───────────────────────────────────────┤
│ Layer 2: Domain Invariant &    │ Strongbox 3:1 input validation;       │
│ Logic Unit Tests               │ Condensed Resin 2x; Strict refusal;   │
│                                │ 4★ fodder integer invariants          │
├────────────────────────────────┼───────────────────────────────────────┤
│ Layer 3: Statistical           │ Gate 1 (Bonferroni Chi-Square) AND    │
│ Distribution Tests             │ Gate 2 (4σ Binomial Bounds)           │
└────────────────────────────────┴───────────────────────────────────────┘
```

### 9.1 Layer 1: Determinism & PRNG Reproducibility Tests (`test_loot_determinism.py`)
- **Bit-for-Bit Replayability**: Given seed $S$, running `run_domain_of_blessing` or `craft_strongbox` produces identical artifacts (id, slot, main stat, substats, roll values, audit events) across multiple independent runs.
- **RNG Stream Isolation**: Verifies that loot generation consumes entropy exclusively from the injected `RNGInterface` and does not mutate or depend on Python's global `random` state.
- **State Save/Restore Replay**: Serializing an engine's PRNG state, restoring it, and generating subsequent drops yields the exact expected sequence.
- **Multi-Seed Divergence**: Verifies that distinct seeds $S_1 \neq S_2$ produce non-identical sequences.

### 9.2 Layer 2: Domain Invariant & Logic Unit Tests (`test_loot_invariants.py`)
- **Strongbox Validation Invariants**:
  - Rejects `len(sacrifices) < 3` with `ValueError`.
  - Rejects `len(sacrifices) % 3 != 0` with `ValueError`.
  - Rejects any artifact with `rarity != 5` with `ValueError` (asserting invalid artifact ID in message).
  - Rejects non-list inputs with `TypeError`.
  - Rejects empty/invalid `target_set` with `ValueError`.
  - Invariant: Input list is not mutated.
- **Domain Execution Invariants**:
  - Rejects `len(sets) != 2` or duplicate sets with `ValueError`.
  - Condensed Resin equivalence: `use_condensed=True` produces `resin_spent == 40`, `runs_executed == 2`, and total drops equal to two consecutive single runs.
  - 4★ Fodder integer invariant: `count_4star_fodder` is strictly an integer $\ge 2$.
  - Generated Artifact Invariants: Every generated 5★ artifact satisfies `SPEC_ARTIFACT.md` (4 conceptual substat slots, no duplicate substats, substat $\neq$ main stat, valid level 0 state).
- **Fidelity Mode Invariants**:
  - `LootFidelityMode.STRICT` refuses to execute with inferred configuration (raises `FidelityViolationError`).
  - `LootFidelityMode.BEST_EFFORT` outputs `weakest_evidence_level = "INFERRED"`.

### 9.3 Layer 3: Statistical Distribution Tests (`test_loot_statistical.py`)
- Pre-registered Gate 1 (Chi-square with Bonferroni correction) and Gate 2 ($4\sigma$ binomial margins).
- Evaluated across $N = 100,000$ (Fast Suite) and $N = 1,000,000$ (Heavy Suite).
- Explicitly decoupled: Statistical tests verify convergence of empirical distributions to specification targets; they do NOT substitute for Layer 1 determinism tests or Layer 2 invariant tests.

---

## 10. Implementation Plan & File Touch Map (Phase P3.2 Preview)

| Action | File Path | Scope & Responsibility |
| :--- | :--- | :--- |
| **CREATE** | `app/core/artifact/loot.py` | Implementation of `run_domain_of_blessing()`, `craft_strongbox()`, `DomainDropResult`, `StrongboxResult`, `LootAuditEvent`, `LootFidelityMode`, `FidelityViolationError`. |
| **CREATE** | `config/artifacts/loot_sources.json` | Declarative configuration for domain costs, set weights, drop rates, and initial line weights. |
| **UPDATE** | `config/artifacts/provenance.json` | Add formal provenance records for all loot source keys. |
| **UPDATE** | `app/core/artifact/config.py` | Extend `ArtifactConfig` and schema validation to parse and validate `loot_sources.json`. |
| **UPDATE** | `app/core/artifact/__init__.py` | Export public loot functions and result types. |
| **CREATE** | `tests/unit/test_loot_determinism.py` | Layer 1 tests: Bit-for-bit replay, PRNG stream isolation, state save/restore. |
| **CREATE** | `tests/unit/test_loot_invariants.py` | Layer 2 tests: Strongbox input validation, Condensed Resin equivalence, strict mode refusal. |
| **CREATE** | `tests/statistical/test_loot_statistical.py` | Layer 3 tests: Pre-registered Gate 1 (Chi-square) and Gate 2 ($4\sigma$) distributions. |

---

## 11. Unverified Server Internals & Decisions for Project Lead Approval

### 11.1 Unverified Mechanics (Honest Acknowledgment)
The following parameters are established purely through empirical crowdsourcing and **cannot be proven to match proprietary server code**:
1. **Equal 50/50 Domain Set Ratio:** Confirmed by $>100,000$ drops, but HoYoverse server weight format remains unknown.
2. **6.54% Secondary 5★ Drop Chance:** Confirmed by $N \approx 50,000$ drops, but exact server Bernoulli parameter or pity counter is unknown. Prohibited in `STRICT` mode.
3. **80/20 vs 66/34 Initial Line Count Ratios:** Confirmed by empirical datasets, but developer-side integer tables remain unobserved. Prohibited in `STRICT` mode.
4. **Uniform 20% Slot Distribution:** Supported by large-scale empirical observation, but server logic is unobservable.
5. **4★ Fodder Quantities (2 to 3, mean ~2.48):** Observed empirically; no official announcement specifies the exact minimum or bonus odds. Reclassified to `INFERRED`.

### 11.2 Standing Blockers (Reaffirmed)
- **Capturing Radiance (`OQ-01`)**: Remains strictly **BLOCKED** from the default engine.
- **Reshaping & Hallowed Exegesis (`OQ-03`)**: Remains strictly **BLOCKED** pending resolution of milestone discrepancies (6/12/18 vs 12/16).
- **World Bosses & Trounce Domains**: Remains strictly **OUT OF SCOPE** for Phase P3.

### 11.3 Decisions Submitted for Final Project Lead Approval
1. **Approval of Strict Fidelity Refusal Policy (F1):**
   - Confirm that `run_domain_of_blessing` and `craft_strongbox` raise `FidelityViolationError` in `LootFidelityMode.STRICT` when configured with production `INFERRED` constants, eliminating silent bypasses.
2. **Approval of Configuration Specification as P3.2 Deliverables (F2):**
   - Confirm that `loot_sources.json` and updates to `provenance.json` are specified in P3.1 but created only in P3.2.
3. **Approval of 4★ Fodder Abstraction & Reclassification (F3):**
   - Confirm Option 1A (`count_4star_fodder: int`) and reclassification of quantity distributions to `INFERRED`.
4. **Approval of Strongbox Initial Line Ratio in Config (F4):**
   - Confirm using integer representation `{"3": 66, "4": 34}` in `config/artifacts/loot_sources.json` labeled `INFERRED` (approximate empirical model, citing raw $65.8\% : 34.2\%$).
5. **Approval of Dual-Gate Statistical Criteria (F5):**
   - Confirm mandatory dual-gate acceptance ($\text{Gate}_1 \land \text{Gate}_2$) with Bonferroni $\alpha_{\text{adj}} = 0.000333$ and $4\sigma$ boundaries.
6. **Approval of Sequential Single-PRNG Stream Policy for Condensed Resin (F6):**
   - Confirm that 1 Condensed Resin executes 2 sequential cycles using one continuous injected PRNG stream.
