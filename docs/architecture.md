# Architecture Overview

## 1. Modular-Monolith Boundary & Dependency Direction

The Gacha & Artifact RNG Simulator is structured as a modular monolith. The system isolates core mathematical and business domains within clear module boundaries, enabling high cohesion, low coupling, and testability without the operational complexity of microservices.

The architectural dependency direction is strictly unidirectional:

```
        Core RNG (app.core.rng)
                   ↓
   Probability Engine (app.core.probability)
                   ↓
  Artifact / Gacha Engines (Future Domain)
                   ↓
      Simulation / Analytics (Future)
                   ↓
            API / Frontend
```

### Module Responsibilities:
- **Core RNG (`app.core.rng`)**: Exclusively responsible for entropy generation, pseudo-random state mutation, isolation from Python's global random state, and deterministic reproducibility.
- **Probability Engine (`app.core.probability`)**: Exclusively responsible for probability-selection primitives, discrete distribution evaluation, and input contract enforcement. It depends on injected RNG abstractions rather than implementing raw randomness.
- **Artifact / Gacha Engines (Future)**: Will consume the Probability Engine for domain-specific drop tables, pity rules, and affix enhancements.
- **API / Frontend**: Presentation and transport layers only. Business logic must never live in the frontend.

## 2. RNG Abstraction

All stochastic behavior across the entire application must pass through the `RNGInterface` (`app/core/rng/interface.py`). Direct calls to Python's global `random` module or unencapsulated random sources are strictly disallowed.

The default implementation `PythonRNG` encapsulates an isolated instance of `random.Random`.

### Why Random Logic Must Not Be Scattered Through the Codebase

- **Reproducibility & Auditability**: When random calls (`random.random()`, `random.choice()`, etc.) are scattered across services, maintaining deterministic behavior or reproducing specific test failures becomes impossible due to invisible global state mutation.
- **Test Isolation**: A centralized abstraction allows tests to inject seeded RNG instances or mock deterministic sequence generators without polluting global state.
- **Pluggability**: The underlying random number generator can be replaced or augmented (e.g., PCG, cryptographic RNG, hardware entropy) without modifying any domain or engine logic.

## 3. Probability Engine Design (P1)

The Probability Engine (`app.core.probability`) decouples probability selection from underlying RNG implementation details.

### Contract and Validation Rules

The primary selection primitive is `weighted_choice(outcomes, weights)`:

1. **Non-empty Collections**: `outcomes` and `weights` must not be empty.
2. **Dimension Parity**: `len(outcomes) == len(weights)`.
3. **Numeric and Finite**: All weights must be real numbers (`int` or `float`, excluding `bool`), non-NaN, and non-infinite.
4. **Non-negativity**: All individual weights must satisfy $w_i \ge 0$.
5. **Finite & Positive Total**: Cumulative weight must satisfy $\sum w_i > 0$ and remain finite (rejecting IEEE-754 float overflow to $\infty$).
6. **Zero-Weight Immunity**: Outcomes with weight $0$ can never be selected.
7. **Scale Invariance**: Normalization is handled inherently; weights do not need to sum to $1$.
8. **Dependency Injection**: Injects `RNGInterface` (defaults to isolated `PythonRNG`).
9. **Uniform RNG Stream Consumption**: Single-outcome selections delegate consistently through the underlying RNG, guaranteeing that each `weighted_choice` invocation advances the RNG stream predictably for event logging, replay, and step debugging.

### Deterministic Replay and State Restoration

- Providing an identical seed to the injected RNG guarantees identical output sequences.
- Saving the RNG state before probability calls and restoring it later guarantees exact sequence replication.
- Probability calls produce zero side-effects on Python's global random state.

## 4. Future Domain Engines (Artifact & Gacha)

Future phases will build atop the Probability Engine:
- **Artifact Engine (Future)**: Will model slot selection, main-stat likelihoods, initial substat count distributions, and affix upgrade enhancements.
- **Gacha Engine (Future)**: Will encapsulate banner states, 4-star and 5-star pity progression, 50/50 guarantee tracking, and epitomized paths.

> **Status Notice**: Game-specific mechanics, pity rules, and artifact formulas are **NOT** implemented in P1.

## 5. Frontend as Presentation Layer

The frontend is strictly a presentation and interaction layer:
- **No Client-Side Business Logic**: Probabilistic calculations, pity counters, roll outcomes, and stat rolls must never be computed in the client.
- **Integrity & Consistency**: Centralizing mechanics in the core engine guarantees consistent calculations across interactive sessions, batch CLI simulations, and analytics pipelines.
- **Mechanic Classification**: Any future game mechanics must be categorized explicitly:
  - `VERIFIED GAME MECHANIC`
  - `REVERSE-ENGINEERED MECHANIC`
  - `COMMUNITY INFERENCE`
  - `OUR ASSUMPTION`
  - `OUR DESIGN CHOICE`

## 6. Current Project Boundaries (P1 Hardening)

P1 scope encompasses:
- Core RNG engine and deterministic tests.
- Generic Probability Engine abstraction and implementation with dependency injection.
- Complete edge case testing (empty, non-finite, mismatched, zero-weight, scale variance).
- Deterministic sequence and state save/restore testing across probability calls.
- Lightweight statistical sanity verification.
- Minimal FastAPI service (`GET /health`).

Artifact generation, Gacha logic, database integration, Monte Carlo batch systems, and UI remain explicitly out of scope.
