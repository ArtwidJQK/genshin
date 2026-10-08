# Configuration System

All probabilistic drop rates, weight tables, and quality tiers across the simulator are strictly **data- and config-driven**.

## Artifact Configuration (`config/artifacts/`)

Established for **Artifact Foundation v1**:

- [`main_stats.json`](file:///d:/side_project/genshin/config/artifacts/main_stats.json): Declares main stat pools and relative probability weights for each artifact slot (`FLOWER`, `PLUME`, `SANDS`, `GOBLET`, `CIRCLET`).
- [`substats.json`](file:///d:/side_project/genshin/config/artifacts/substats.json): Research-backed initial selection weights for the 10 canonical substats.
- [`roll_values.json`](file:///d:/side_project/genshin/config/artifacts/roll_values.json): Quality tiers (`70%`, `80%`, `90%`, `100%`), tier distribution weights, and exact numeric increment values for every substat type.
- [`rules.json`](file:///d:/side_project/genshin/config/artifacts/rules.json): Artifact rules including 5★ rarity constraint, max level (20), milestone levels (`[4, 8, 12, 16, 20]`), 4-slot invariant, and initial 3-line vs 4-line drop weights.

## Gacha Configuration (Future Phase)

Reserved for upcoming Gacha banner pool tables, soft/hard pity curves, and 50/50 guarantee rules.
