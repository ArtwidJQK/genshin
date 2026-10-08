# Gacha & Artifact RNG Simulator

A probabilistic game simulation engine inspired by Genshin-like artifact and gacha mechanics, designed with deterministic replayability, strict mathematical isolation, and a modular architecture.

## Current Development Phase

**Phase: P1 — RNG & Probability Engine Hardening**

This phase delivers the hardened probability layer:
- Clean modular-monolith repository structure.
- Isolated RNG abstraction (`RNGInterface`, `PythonRNG`) wrapping Python's `random.Random`.
- Generic Probability Engine (`ProbabilityEngineInterface`, `ProbabilityEngine`) with explicit dependency injection for RNG providers.
- Strict input validation on all probability operations (empty checks, length matching, non-negativity, finite bounds, zero-weight immunity).
- Deterministic seed reproduction, state save/restore, and global random state isolation.
- Minimal FastAPI service with `/health` endpoint.
- Complete deterministic pytest test suite with edge case coverage and lightweight statistical sanity verification.

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

Run the test suite via pytest:

```bash
python -m pytest -v
```

All tests are deterministic and assert exact reproducibility under seeded conditions.

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

## Current Scope (P1)

- RNG interface definition and engine (`app/core/rng/`)
- Probability engine interface and implementation with dependency injection (`app/core/probability/`)
- Deterministic seeding, state serialization, bounds-checked numeric sampling, and weighted choice
- Minimal health check API route (`app/main.py`)
- Architectural documentation and 33 deterministic automated tests

## Explicitly NOT Implemented Yet

To maintain strict incremental discipline, the following features are intentionally out of scope for P1:
- Artifact generation, main stats, substat rolls, and enhancement
- Gacha banners, pity counters, and pull guarantees
- Game-specific probability tables and drop rates
- Inventories, persistence, or database storage
- Frontend client interface
- Authentication, authorization, or user accounts
- Monte Carlo multi-threaded batch simulators
