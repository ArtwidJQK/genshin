# Architecture Overview

## 1. Core Engine Concept

The Gacha & Artifact RNG Simulator is structured as a modular monolith. The core engine is designed as an isolated, deterministic computational core responsible for all game logic, statistical evaluations, and state transitions.

```
CORE ENGINE
    ├── RNG ENGINE (P0)
    ├── PROBABILITY ENGINE (Future)
    ├── STATE MANAGEMENT (Future)
    ├── CONFIG/DATA SYSTEM (Future)
    │
    ├── ARTIFACT ENGINE (Future)
    ├── GACHA ENGINE (Future)
    └── SIMULATION / ANALYTICS (Future)
             │
        API/SERVICE (FastAPI)
             │
      PRESENTATION LAYER (Frontend)
```

## 2. RNG Abstraction

All stochastic behavior across the system must pass through the `RNGInterface` (`app/core/rng/interface.py`). Direct calls to Python's global `random` module or unencapsulated random sources are strictly disallowed.

Key benefits:
- **Isolation**: Prevents ambient side effects or third-party libraries from perturbing simulation sequences.
- **Pluggability**: Enables alternative RNG engines (e.g., PCG, cryptographic RNG, or custom algorithms) without impacting domain logic.
- **Auditability**: All random draws (uniform, integer, weighted choice, shuffles) are centrally routed and traceable.

## 3. Deterministic Mode

The simulator enforces strict determinism:
- Supplying identical seeds produces identical sequences (`seed -> sequence`).
- The RNG engine supports full state capture (`get_state`) and restoration (`set_state`) to enable replay, backtracking, and checkpointing for Monte Carlo analyses.

## 4. Separation of Concerns: Frontend as Presentation Layer

The frontend is strictly a presentation and interaction layer:
- **No Client-Side Business Logic**: Probabilistic calculations, pity counters, roll outcomes, and stat rolls must never be computed in the client.
- **Integrity & Consistency**: Centralizing mechanics in the core engine guarantees consistent calculations across interactive sessions, batch CLI simulations, and analytics pipelines.
- **Mechanic Classification**: Any future game mechanics must be categorized explicitly (Verified Game Mechanic, Reverse-Engineered Mechanic, Community Inference, Our Assumption, or Our Design Choice).

## 5. Current Boundaries (P0)

P0 establishes only the core foundational components:
- Repository structure and packaging.
- Deterministic RNG interface and `random.Random` encapsulation.
- Input-validated generic weighted choice primitive.
- Minimal FastAPI service with `/health` verification.
- Deterministic automated test suite.

Artifact generation, Gacha logic, database integration, and UI remain explicitly out of scope for P0.
