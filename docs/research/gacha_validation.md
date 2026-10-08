# Gacha Research Validation

## Status
P2 research initialization only. No engine/config implementation is authorized by this document.

## Scope
Audit character-event wish mechanics before P2 Character Gacha Engine specification.

## Required claims to research
1. Published base and consolidated 5★/4★ rates.
2. Hard pity thresholds.
3. Soft-pity onset and per-pull probability curve.
4. Featured 5★ / 50-50 / guarantee behavior.
5. Pity and guarantee carry-over across banners.
6. 4★ featured-unit distribution and guarantee behavior.
7. Capturing Radiance: introduction, trigger conditions, probability effect, and interaction with guarantee state.
8. Banner/state-machine semantics.
9. History/state persistence semantics relevant to simulation.
10. Source-specific or banner-type exceptions.

## Evidence protocol
Use the existing project hierarchy:
- A = Official
- B = Reverse Engineering / datamine
- C = Large-scale player data
- D = Community observation
- E = Speculation

Never promote C/D consensus into A/B. Separate game facts, reverse-engineered facts, empirical observations, community consensus, and simulator design choices.

## Exit criteria
No P2 engine implementation until each claim has an auditable source, exact locator, evidence tier, what the source establishes, limitations, and simulator relationship. Unsupported numerical assertions must be removed or downgraded.

## Implementation gate
This file is a research scaffold only. Do not modify application code, configuration, RNG, probability engine, API, FE, DB, or tests as part of research initialization.
