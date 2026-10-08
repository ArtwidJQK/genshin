# Gacha & Artifact RNG Simulator

A probabilistic game simulation engine inspired by Genshin-like artifact and gacha mechanics, designed with deterministic replayability, strict mathematical isolation, and a modular architecture.

## Current Development Phase

**Phase: Artifact Foundation v1**

This phase delivers the core 5★ Artifact generation and enhancement state machine:
- Clean modular-monolith repository structure.
- Isolated RNG abstraction (`RNGInterface`, `PythonRNG`) wrapping Python's `random.Random`.
- Generic Probability Engine (`ProbabilityEngineInterface`, `ProbabilityEngine`) with explicit dependency injection.
- 5★ Artifact domain data model with 4 conceptual substat slots invariant (`app/core/artifact/models.py`).
- Pre-generated hidden 4th substat for 3-line artifacts at +0 (`INACTIVE` state).
- Configurable generation pipeline obeying slot restrictions and non-duplication rules.
- Complete enhancement state machine (+4, +8, +12, +16, +20):
  - +4 for 3-line base activates the hidden 4th substat (no roll, no value change).
  - +4 for 4-line base and all subsequent milestones (+8, +12, +16, +20) perform uniform 1/4 upgrade rolls.
- Full audit history retained for every roll increment and milestone event.
- Data-driven configurations (`config/artifacts/`) for main stats, substat weights, roll tiers, and rules.
- 67 deterministic automated unit tests across RNG, Probability, API, and Artifact domains.

## Tech Stack

- **Language**: Python (3.11+)
- **API Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Testing**: pytest, httpx

## Installation

1. Ensure Python 3.11+ is installed.
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running Tests

Run the complete test suite via pytest:

```bash
python -m pytest -v
```

All 67 tests are deterministic and assert exact reproducibility under seeded conditions.

## Starting the FastAPI Application

Start the development server with Uvicorn:

```bash
python -m uvicorn app.main:app --reload
```

Access the health check endpoint:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:
```json
{"status": "ok"}
```

## Current Scope (Artifact Foundation v1)

- RNG interface definition and engine (`app/core/rng/`)
- Probability engine interface and implementation with dependency injection (`app/core/probability/`)
- Artifact domain models, configuration loader, and enhancement engine (`app/core/artifact/`)
- Configuration tables for main stats, substats, roll values, and rules (`config/artifacts/`)
- Minimal health check API route (`app/main.py`)
- Architectural documentation and 67 deterministic automated tests

## Explicitly NOT Implemented Yet

To maintain strict incremental discipline, the following features are intentionally out of scope:
- Gacha banners, pity counters, and pull guarantees
- Inventories, item locking, filtering, or database storage
- Batch farming pipelines or Monte Carlo analytics
- Frontend client interface
- Authentication, authorization, or user accounts
- Artifact Transmuter, custom artifact crafting, or Strongbox exchange
