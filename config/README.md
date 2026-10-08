# Configuration System

This directory is reserved for static configuration, probability definitions, and rule definitions for future development phases.

## Data & Config-Driven Design

In line with the project architecture, all future game mechanics, probability tables, drop rates, and stat distributions will be strictly **data- and config-driven**:

- **Decoupled Business Rules**: Mechanics logic will not hardcode arbitrary constants (such as 0.6% base 5-star rates or specific substat weights). Instead, schemas and configurations will declare the distributions, enabling testing, tuning, and multi-game rule definitions.
- **Drop Tables & Weight Configurations**: Static configurations mapping item IDs, sets, and rarities to probabilities and weights.
- **Affix & Stat Definitions**: Schema and rules for artifact slot types, main-stat likelihoods, initial substat count distributions, and upgrade affix rolls.
- **Gacha Pool Tables**: Probability curves, soft pity / hard pity thresholds, rate-up guarantees, and rarity pools.

## Current Phase (P0 Foundation)

No game-specific configuration data or probability tables are active in P0. All configuration data systems will be introduced incrementally in subsequent phases after the core probability and domain engines are validated.
