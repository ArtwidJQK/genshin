# P2 Character Gacha Research Validation

## Status
**RESEARCH COMPLETE — IMPLEMENTATION NOT YET AUTHORIZED**

This document validates the current Character Event Wish research boundary. It distinguishes official rules from empirical/community models and simulator design choices.

## Evidence hierarchy
- **A — Official:** HoYoverse / in-game Wish Details.
- **B — Reverse engineering / datamine:** client data or equivalent technical extraction.
- **C — Large-scale player data:** aggregate wish datasets used to infer hidden probability behavior.
- **D — Community observation:** guides, calculators, community consensus.
- **E — Speculation:** unsupported hypotheses.

C/D evidence must never be presented as official fact.

## Claim Matrix

| # | Claim | Evidence | Status | Simulator consequence |
|---|---|---|---|---|
| 1 | Character Event Wish base 5★ rate is 0.6%; consolidated 5★ rate including guarantee is 1.6% | A | **VERIFIED** | Configurable base/consolidated metadata |
| 2 | Character Event Wish base 4★ rate is 5.1%; consolidated 4★ rate including guarantee is 13.0% | A | **VERIFIED** | Separate 4★ pity counter |
| 3 | A 5★ is guaranteed by the 90th wish | A | **VERIFIED** | 5★ hard cap = 90 |
| 4 | A 4★ or higher is guaranteed at least once every 10 wishes | A | **VERIFIED** | 4★ hard cap = 10; 5★ may satisfy the guarantee |
| 5 | On a non-guaranteed 5★ event-character outcome, promotional vs standard character is 50/50; losing makes the next 5★ promotional | A | **VERIFIED** | Featured-5★ guarantee state |
| 6 | Character Event Wish and Character Event Wish-2 share the same wish guarantee count | A | **VERIFIED** | One shared character-event pity/guarantee state |
| 7 | Pity/guarantee carries between successive character-event banners of the same wish family | A + corroboration | **VERIFIED FOR SIMULATOR SCOPE** | Persist state across banner rotation |
| 8 | Soft pity starts at pull 74 with linear +6 percentage-point increments through pull 89 | C | **PARTIALLY VERIFIED / EMPIRICAL MODEL ONLY** | If implemented, isolate as empirical configurable curve |
| 9 | Large-scale 9.45M-wish estimation supports the strong increase from pull 74 onward | C | **PARTIALLY VERIFIED** | Calibration/regression only; not authoritative rule text |
| 10 | Every 4★ item has a 50% chance to be one of the three featured 4★ characters; after a non-featured 4★, next 4★ is guaranteed featured; featured characters are equal among the three | A | **VERIFIED** | Featured-4★ guarantee + equal featured selection |
| 11 | Capturing Radiance was added with Version 5.0 | A | **VERIFIED** | Versioned rule set |
| 12 | Capturing Radiance base trigger probability is 0.018%; consolidated promotional-character probability on a 5★ event-wish outcome is 55% including Capturing Radiance | A | **VERIFIED** | Explicit CR logic; do not fake it as generic 55/45 |
| 13 | If the promotional 5★ is the second 5★ character obtained on three consecutive occasions, Capturing Radiance is guaranteed on the next applicable 5★ | A | **VERIFIED** | Dedicated CR streak state |
| 14 | Capturing Radiance applies only where the ordinary 50/50 applies and does not alter existing guarantees | A | **VERIFIED** | Evaluate CR only on non-guaranteed 5★ |
| 15 | Exact soft-pity curve is an official published rule | — | **NOT VERIFIED** | Never label the empirical curve as official |
| 16 | Exact hidden distribution of non-featured 4★ character vs weapon outcomes follows simplified UI wording | C/D | **NOT VERIFIED AS INTERNAL SERVER RULE** | Do not overfit hidden sub-distributions |

## Source Provenance

### A1 — HoYoverse: Capturing Radiance
**Source:** HoYoverse, “Capturing Radiance” Mechanic: You Ask, I Answer!  
**URL:** https://genshin.hoyoverse.com/en/news/detail/125274  
**Locator:** Published Aug 16, 2024; February 10, 2025 update.  
**Supports:** Version 5.0 introduction; 0.018% base trigger probability; 55.000% consolidated promotional probability including Capturing Radiance; three-consecutive-occasion condition; applicability clarification.  
**Evidence tier:** A.

### A2 — HoYoverse: Event Wish notices
Representative notices explicitly state that Character Event Wish and Character Event Wish-2 share and accumulate the wish guarantee count and that this count is independent of other wish types.

Sources:
- Version 5.3 Event Wishes Notice — Phase I: https://genshin.hoyoverse.com/en/news/detail/127690
- Version 5.6 Event Wishes Notice — Phase II: https://genshin.hoyoverse.com/news/detail/155991
- Version “Luna V” Event Wishes Notice — Phase I: https://genshin.hoyoverse.com/en/news/detail/162721
- Version “Luna V” Event Wishes Notice — Phase II: https://genshin.hoyoverse.com/en/news/detail/163094

**Locator:** Event Wish Details sections and the notes beginning “This is for Character Event Wish...” / “This is for Character Event Wish-2...”.

**Supports:** Shared Character Event Wish / Character Event Wish-2 guarantee count; current banner structure; three featured 4★ characters; event-exclusive 5★ is unavailable in Standard Wish.

### A3 — Official/in-game Wish Details snapshot
A historical official HoYoverse webstatic Wish system record establishes:
- 5★ promotional character: first 5★ has 50.000% chance to be promotional; losing guarantees next 5★ promotional.
- 4★ base probability: 5.100%.
- 4★ consolidated probability: 13.000%.
- 4★ or higher guaranteed at least once per 10 attempts.
- Featured 4★ chance: 50.000%; if not featured, next 4★ is guaranteed featured.
- Each featured 4★ has equal probability among the three.

**Evidence tier:** A.  
**Limitation:** historical official payload rather than a current 2026 page snapshot; current HoYoverse notices confirm current banner structure and shared character-event guarantee count.

### C1 — Community aggregate estimate: 9.45M wishes
The commonly cited large-scale dataset models 0.6% through pull 73, then approximately +6 percentage points per pull from 74–89, with 100% at 90.

**Evidence tier:** C.  
**Important:** the curve is **not** an official published probability table.

### D1 — Community documentation
Community guides corroborate 90 hard pity, approximate soft-pity region around 74–75, 50/50 + guarantee, and banner carry-over. Use as corroboration only.

**Evidence tier:** D.

## Critical Research Boundaries

### Soft pity
**Do not claim:** “HoYoverse officially says soft pity starts at 74 and rises by 6% each pull.”

**Allowed statement:** “A large-scale community dataset is commonly modeled as 0.6% through pull 73, then a linear increase from pull 74 to 89, with hard pity at 90.”

### Capturing Radiance
This is an **officially documented mechanic**. Model it explicitly.

Official clarification:
- base trigger probability = 0.018%;
- consolidated promotional probability when obtaining a 5★ = 55%;
- if the promotional 5★ is the second 5★ character obtained on three consecutive occasions, Capturing Radiance is guaranteed on the next 5★;
- it only applies when the normal 50/50 is active and does not replace existing guarantees.

### Banner carry-over
Official notices explicitly state shared guarantee count between Character Event Wish and Character Event Wish-2. For the simulator, pity/guarantee state belongs to the **character-event wish family**, not an individual banner instance.

### 4★ mechanics
Official Wish Details establish:
- 4★ or higher at least once per 10 attempts;
- 50% featured 4★ group chance;
- non-featured 4★ causes next 4★ to be featured;
- equal probability among the three featured 4★ characters.

Do not infer undocumented hidden non-featured character/weapon sub-distributions from simplified UI wording.

## Simulator Design Choices — NOT Game Facts

1. Internal GachaState schema.
2. Exact RNG call order.
3. Single-pull vs ten-pull internal execution.
4. Seed/state serialization format.
5. Pity counter representation.
6. Capturing Radiance streak-counter representation.
7. Banner configuration JSON schema.
8. API request/response schema.
9. History record schema.
10. Monte Carlo/statistical output schema.

## P2 Research Exit Criteria

Research is signed off only when:
- official rules are separated from empirical soft-pity modeling;
- all numerical claims have source provenance;
- Capturing Radiance is an explicit state-machine feature;
- Character Event Wish and Character Event Wish-2 shared state is represented;
- 4★ pity and featured guarantee are represented;
- unsupported hidden probability assumptions are excluded;
- no application code is changed before the P2 engine SPEC is approved.

## Current Recommendation

**RECOMMENDED:** Proceed to **P2 Character Gacha Engine SPEC**, not implementation.

**WHY:** The MVP mechanics needed for a testable state machine are sufficiently sourced; the unresolved soft-pity curve can be isolated behind an explicitly empirical probability model.

**TRADE-OFF:** Research honesty vs. claiming an undocumented exact server curve.

**RISK:** Future game-version changes may alter Wish mechanics. Keep configuration/versioning explicit.

**NEXT:** Write the P2 Gacha Engine SPEC, including state machine, RNG chronology, config schema, invariants, deterministic test vectors, statistical tests, and acceptance criteria. Do not implement yet.
