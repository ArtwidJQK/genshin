# Architecture Overview

## 1. Modular-Monolith Boundary

The Gacha & Artifact RNG Simulator is structured as a modular monolith. The system isolates core mathematical and business domains within clear module boundaries, enabling high cohesion, low coupling, and easy testing without the operational overhead of microservices:

```
CORE ENGINE
    ├── RNG ENGINE (P0: Foundation)
    ├── PROBABILITY ENGINE (Future: Distributions, CDF/PDF)
    ├── STATE MANAGEMENT (Future: Pity counters, roll history)
    ├── CONFIG / DATA (Future: Static tables, affix weights)
    │
    ├── ARTIFACT ENGINE (Future: Drop, roll, enhance)
    ├── GACHA ENGINE (Future: Banners, guarantees)
    └── SIMULATION / ANALYTICS (Future: Monte Carlo batch runs)
             │
        API / SERVICE (FastAPI)
             │
     PRESENTATION LAYER (Frontend)
```

## 2. RNG Abstraction

All stochastic behavior across the entire application must pass through the `RNGInterface` (`app/core/rng/interface.py`). Direct calls to Python's global `random` module or unencapsulated random sources are strictly disallowed.

The default implementation `PythonRNG` encapsulates an isolated instance of `random.Random`.

### Why Random Logic Must Not Be Scattered Through the Codebase

- **Reproducibility & Auditability**: When random calls (`random.random()`, `random.choice()`, etc.) are scattered across services, maintaining deterministic behavior or reproducing specific test failures becomes impossible due to invisible global state mutation.
- **Test Isolation**: A centralized abstraction allows tests to inject seeded RNG instances or mock deterministic sequence generators without polluting global state.
- **Pluggability**: The underlying random number generator can be replaced or augmented (e.g., PCG, cryptographic RNG, hardware entropy) without modifying any domain or engine logic.

## 3. Deterministic RNG Mode

The simulator enforces strict determinism:
- Supplying identical seeds produces identical sequences (`seed -> sequence`).
- The RNG engine supports full state capture (`get_state`) and restoration (`set_state`) to enable replay, backtracking, and checkpointing for Monte Carlo analyses.

## 4. Future Probability, Artifact, and Gacha Engines

- **Probability Engine (Future)**: Will define mathematical primitives for discrete probability mass functions, pity curves, and drop evaluations independent of specific game rules.
- **Artifact Engine (Future)**: Will model slot selection, main-stat attribution, initial substat roll distributions, and level-up affix enhancements.
- **Gacha Engine (Future)**: Will encapsulate banner states, 4-star and 5-star pity progression, 50/50 guarantee tracking, and epitomized paths.

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

## 6. Current Project Boundaries (P0 Foundation)

P0 establishes only the core foundational components:
- Repository structure and packaging.
- Deterministic RNG interface and `random.Random` encapsulation.
- Input-validated generic weighted choice primitive.
- Minimal FastAPI service with `/health` verification.
- Deterministic automated test suite.

Artifact generation, Gacha logic, database integration, and UI remain explicitly out of scope for P0.
