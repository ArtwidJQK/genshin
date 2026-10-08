# Architecture Overview

## 1. Modular-Monolith Boundary & Dependency Direction

The Gacha & Artifact RNG Simulator is structured as a modular monolith. The system isolates core mathematical and business domains within clear module boundaries, enabling high cohesion, low coupling, and testability without the operational complexity of microservices.

The architectural dependency direction is strictly unidirectional:

```
        Core RNG (app.core.rng)
                   ↓
   Probability Engine (app.core.probability)
                   ↓
   Artifact Engine (app.core.artifact)
                   ↓
     Gacha Engine (Future Phase)
                   ↓
      Simulation / Analytics (Future)
                   ↓
            API / Frontend
```

### Module Responsibilities:
- **Core RNG (`app.core.rng`)**: Exclusively responsible for entropy generation, pseudo-random state mutation, isolation from Python's global random state, and deterministic reproducibility.
- **Probability Engine (`app.core.probability`)**: Exclusively responsible for probability-selection primitives, discrete distribution evaluation, and input contract enforcement. It depends on injected RNG abstractions rather than implementing raw randomness.
- **Artifact Engine (`app.core.artifact`)**: Implements the 5★ Artifact domain data model, initial generation pipeline, and enhancement state machine. All stochastic operations strictly consume the `ProbabilityEngine`.
- **API / Frontend**: Presentation and transport layers only. Business logic must never live in the frontend.

## 2. RNG Abstraction

All stochastic behavior across the entire application must pass through the `RNGInterface` (`app/core/rng/interface.py`). Direct calls to Python's global `random` module or unencapsulated random sources are strictly disallowed.

The default implementation `PythonRNG` encapsulates an isolated instance of `random.Random`.

### Why Random Logic Must Not Be Scattered Through the Codebase

- **Reproducibility & Auditability**: When random calls (`random.random()`, `random.choice()`, etc.) are scattered across services, maintaining deterministic behavior or reproducing specific test failures becomes impossible due to invisible global state mutation.
- **Test Isolation**: A centralized abstraction allows tests to inject seeded RNG instances or mock deterministic sequence generators without polluting global state.
- **Pluggability**: The underlying random number generator can be replaced or augmented (e.g., PCG, cryptographic RNG, hardware entropy) without modifying any domain or engine logic.

## 3. Probability Engine Design

The Probability Engine (`app.core.probability`) decouples probability selection from underlying RNG implementation details.

### Contract and Validation Rules
1. **Non-empty Collections**: `outcomes` and `weights` must not be empty.
2. **Dimension Parity**: `len(outcomes) == len(weights)`.
3. **Numeric and Finite**: All weights must be real numbers (`int` or `float`, excluding `bool`), non-NaN, and non-infinite.
4. **Non-negativity**: All individual weights must satisfy $w_i \ge 0$.
5. **Finite & Positive Total**: Cumulative weight must satisfy $\sum w_i > 0$ and remain finite (rejecting IEEE-754 float overflow to $\infty$).
6. **Zero-Weight Immunity**: Outcomes with weight $0$ can never be selected.
7. **Scale Invariance**: Normalization is handled inherently; weights do not need to sum to $1$.
8. **Dependency Injection**: Injects `RNGInterface` (defaults to isolated `PythonRNG`).
9. **Uniform RNG Stream Consumption**: Single-outcome selections delegate consistently through the underlying RNG, guaranteeing that each `weighted_choice` invocation advances the RNG stream predictably for event logging, replay, and step debugging.

## 4. Artifact Foundation v1 (`app.core.artifact`)

The Artifact Engine models 5★ artifacts adhering strictly to Artifact SPEC v1.

### 4.1 Artifact Entity & 4-Slot Invariant
- Every 5★ artifact strictly contains **four conceptual substat slots** at all times.
- Each substat slot possesses an activation state (`ACTIVE` or `INACTIVE`), a stat type, an initial value, an initial tier, and an audit trail of enhancement rolls.

### 4.2 3-Line vs 4-Line Base Model
- **3-Line Artifact at +0**:
  - Substats #1, #2, #3 are marked `ACTIVE`.
  - Substat #4 is pre-generated with a concrete stat type and initial value at generation time, but marked `INACTIVE` (previewed).
  - At milestone **+4**, substat #4 transitions from `INACTIVE` to `ACTIVE`. **No upgrade roll occurs, no values are changed, and no new stat is drawn.**
- **4-Line Artifact at +0**:
  - All four substats (#1 to #4) are marked `ACTIVE`.
  - At milestone **+4**, exactly one of the four active substats is upgraded.

### 4.3 Enhancement State Machine
- Enhancements occur at milestones: `+4`, `+8`, `+12`, `+16`, `+20`.
- **After +4**, all artifacts have exactly four active substats.
- At `+8`, `+12`, `+16`, and `+20`, exactly one active substat is selected **uniformly (25% each)** for an upgrade roll.
- Total upgrades:
  - 3-line base: 1 activation + 4 upgrades.
  - 4-line base: 5 upgrades.

### 4.4 Roll Value Tiers & Increments
- Each roll draws one of four quality tiers (`70%`, `80%`, `90%`, `100%`) using configured tier weights.
- The stat-specific numeric increment corresponding to that tier is retrieved from configuration and appended to the target substat's roll history.
- Current substat value is mathematically derived as:
  $$\text{value} = \text{initial\_value} + \sum \text{increment}_i$$

### 4.5 Configuration-Driven Mechanics
All drop rules and probabilities reside in `config/artifacts/`:
- `main_stats.json`: Main stat likelihoods per slot (e.g. Flower=FLAT_HP, Plume=FLAT_ATK, weighted pools for Sands/Goblet/Circlet).
- `substats.json`: Research-backed candidate weights for initial substat pool.
- `roll_values.json`: Tier probabilities and exact values for each of the 10 substat types.
- `rules.json`: Rarity constraints, max level (20), milestone levels, and 3-line vs 4-line drop rates.

## 5. Epistemological Classification of Mechanics

To maintain complete intellectual honesty, mechanics are categorized explicitly:

| Category | Mechanics Included |
| :--- | :--- |
| **VERIFIED / RESEARCH-BACKED** | 5★ artifact slots, main-stat restrictions (Flower=HP, Plume=ATK), 10 canonical substat types, no duplicate substats, substat cannot match main stat, enhancement milestones (+4, +8, +12, +16, +20), uniform 1/4 upgrade target selection. |
| **REVERSE-ENGINEERED** | Community-aggregated substat weights (6/6/6/4/4/4/4/4/3/3), main-stat weight distributions, roll quality tiers (70%, 80%, 90%, 100%). |
| **OUR IMPLEMENTATION DETAIL** | Pre-generating the hidden 4th substat at +0 and marking it `INACTIVE` so +4 is a pure state activation; sequential generation order: slot → main stat → lines (3 vs 4) → sub1 → sub2 → sub3 → sub4. |
| **OUR DESIGN CHOICE** | Dataclass domain models, `SubstatRoll` and `EnhancementEvent` audit trail recording, explicit dependency injection. |

> **Disclaimer**: We make no claim that the original game's proprietary backend uses this internal RNG chronology or class schema. Our design choices are chosen for deterministic replayability, testability, and clarity.

## 6. Current Project Boundaries (P1 + Artifact Foundation v1)

Current scope comprises:
- Core RNG engine with deterministic tests.
- Generic Probability Engine with dependency injection and input contracts.
- Artifact domain models, configuration loader, generation pipeline, and enhancement state machine.
- 87 deterministic automated unit tests (including strict config validation, enhancement level progression, and state corruption rejection).
- Minimal FastAPI service (`GET /health`).

Explicitly out of scope:
- Gacha banners, pity counters, and guarantees.
- Inventories, item locking, filtering, and databases.
- Multi-threaded Monte Carlo farming simulators.
- Frontend user interface.
