# Gacha & Artifact RNG Simulator

A probabilistic game simulation engine inspired by Genshin-like artifact and gacha mechanics, designed with deterministic replayability, strict mathematical isolation, and a modular architecture.

## Current Development Phase

**Phase: P0 Foundation**

This phase delivers the foundational scaffolding:
- Clean modular-monolith repository structure.
- Isolated RNG abstraction (`RNGInterface`, `PythonRNG`) wrapping Python's `random.Random`.
- Deterministic seed reproduction and state save/restore capabilities.
- Generic, input-validated weighted choice primitive.
- Minimal FastAPI service with `/health` endpoint.
- Deterministic pytest test suite covering RNG operations and API readiness.

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
uvicorn app.main:app --reload
```

Access the health check endpoint:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:
```json
{"status": "ok"}
```

## Current Scope (P0)

- RNG interface definition (`app/core/rng/interface.py`)
- Encapsulated `random.Random` engine (`app/core/rng/engine.py`)
- Deterministic seeding, state serialization, bounds-checked numeric sampling, and weighted choice
- Minimal health check API route
- Architectural documentation and test harness

## Explicitly NOT Implemented Yet

To maintain strict incremental discipline, the following features are intentionally out of scope for P0:
- Artifact generation, main stats, substat rolls, and enhancement
- Gacha banners, pity counters, and pull guarantees
- Game-specific probability tables and drop rates
- Inventories, persistence, or database storage
- Frontend client interface
- Authentication, authorization, or user accounts
- Monte Carlo multi-threaded batch simulators
