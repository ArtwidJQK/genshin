# SPEC_ARTIFACT — 5★ Artifact System Specification

**Document Version:** 1.0.0  
**Target Game Version:** Genshin Impact 7.1 (Reaffirmed)  
**Status:** ACTIVE  
**Reference Document:** `docs/PROJECT_PLAN.md` Section 4 & `docs/research/artifact_validation.md`

---

## 1. Domain Overview

This specification formalizes the core mathematical rules, state machines, probability distributions, roll tiers, and data schemas governing the 5★ Artifact generation and enhancement system in the Genshin Simulator.

Every parameter and rule in this specification carries an explicit **Evidence Level** according to `AGENTS.md` Section 5:
- `VERIFIED`: Directly supported by official HoYoverse sources or client configuration extractions.
- `INFERRED`: Strongly established through large-scale community empirical data.
- `ASSUMED`: Simulator engineering assumption made where internals are unobservable.
- `UNKNOWN`: Unestablished or disputed; requires isolation.

---

## 2. 5★ Artifact Structure & Invariants

### 2.1 Conceptual Slots and Basic Properties
* **Five Artifact Slots:**
  - `FLOWER` (Flower of Life): Fixed Main Stat = `FLAT_HP` (`VERIFIED`, Official in-game rule).
  - `PLUME` (Plume of Death): Fixed Main Stat = `FLAT_ATK` (`VERIFIED`, Official in-game rule).
  - `SANDS` (Sands of Eon): Weighted Main Stat pool (`VERIFIED`, Official in-game rule).
  - `GOBLET` (Goblet of Eonothem): Weighted Main Stat pool (`VERIFIED`, Official in-game rule).
  - `CIRCLET` (Circlet of Logos): Weighted Main Stat pool (`VERIFIED`, Official in-game rule).
* **Rarity:** Exclusively 5★ in this phase (`VERIFIED`).
* **Level Progression:** Minimum Level $0$, Maximum Level $20$ (`VERIFIED`).
* **Four Substat Slots Invariant:**
  - Every 5★ artifact strictly contains **four conceptual substat slots** from generation (`VERIFIED` cap; 4-slot array is `ASSUMED` internal structural design choice).
  - Substat types must be distinct (no duplicate substat types on a single artifact) (`VERIFIED`, In-game rule).
  - No substat can match the artifact's main stat (`VERIFIED`, In-game rule). Note: `FLAT_ATK` substat is valid when `ATK_PERCENT` is the main stat.

### 2.2 3-Line vs. 4-Line Base State Machine
* **Initial Line Count Distribution (Domain Drops):**
  - $80\%$ probability of 3 initial substats (`INFERRED`, Level C Crowdsourced Domain drops).
  - $20\%$ probability of 4 initial substats (`INFERRED`, Level C Crowdsourced Domain drops).
* **3-Line Base Artifact Mechanics:**
  - At Level $0$, substats 1, 2, and 3 are in state `ACTIVE`.
  - Substat 4 is pre-generated at Level $0$ with concrete stat type and initial roll value, but placed in state `INACTIVE` (`ASSUMED` simulator implementation detail; mathematically equivalent to revealing on milestone).
  - At milestone **+4**, Substat 4 transitions from `INACTIVE` to `ACTIVE`.
  - **No upgrade roll occurs, no values change, and no new stat is drawn at +4 for a 3-line artifact** (`VERIFIED`, Official in-game rule).
* **4-Line Base Artifact Mechanics:**
  - At Level $0$, all 4 substats are in state `ACTIVE`.
  - At milestone **+4**, exactly one active substat is chosen for an upgrade roll (`VERIFIED`, Official in-game rule).
* **Upgrade Milestone Cadence:**
  - Enhancement milestones occur strictly at levels: `+4`, `+8`, `+12`, `+16`, `+20` (`VERIFIED`, Official in-game rule).
  - Intermediate levels (e.g. 0 → 7, 7 → 15) trigger rolls only when passing through milestone boundaries (`VERIFIED`).
  - Total upgrade rolls across Level 0 → 20:
    - 4-line base: exactly **5 random upgrade rolls** (`VERIFIED`).
    - 3-line base: exactly **4 random upgrade rolls** (after +4 activation) (`VERIFIED`).

### 2.3 Upgrade Target Selection Rule
* When an upgrade milestone occurs on an artifact with 4 active substats:
  - Exactly one substat is selected **uniformly at random** ($\frac{1}{4} = 25\%$ probability per slot) (`INFERRED`, Level C/D Community consensus; KeqingMains Artifact Guide).
  - Previous upgrade history does not bias future target selections (`INFERRED`).

---

## 3. Roll Tiers and Numerical Values

### 3.1 Four Discrete Roll Tiers
Each substat roll (initial generation and subsequent upgrades) selects from 4 discrete quality tiers (`VERIFIED` existence from client datamine `ReliquaryAffixExcelConfigData.json`):
* `70%` tier: multiplier $\approx 0.70$
* `80%` tier: multiplier $\approx 0.80$
* `90%` tier: multiplier $\approx 0.90$
* `100%` tier: multiplier $1.00$

### 3.2 Tier Probability Weights
* Each tier has equal $25\%$ probability ($1:1:1:1$) (`INFERRED`, Level C/D Community consensus).

### 3.3 5★ Substat Value Tables (Max & Tiers)

| Substat Key | Display Name | 70% Tier | 80% Tier | 90% Tier | 100% (Max) | Evidence Level |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `CRIT_RATE` | CRIT Rate% | 2.72 | 3.11 | 3.50 | 3.89 | `VERIFIED` (B) |
| `CRIT_DMG` | CRIT DMG% | 5.44 | 6.22 | 6.99 | 7.77 | `VERIFIED` (B) |
| `ATK_PERCENT` | ATK% | 4.08 | 4.66 | 5.25 | 5.83 | `VERIFIED` (B) |
| `HP_PERCENT` | HP% | 4.08 | 4.66 | 5.25 | 5.83 | `VERIFIED` (B) |
| `DEF_PERCENT` | DEF% | 5.10 | 5.83 | 6.56 | 7.29 | `VERIFIED` (B) |
| `ENERGY_RECHARGE` | Energy Recharge% | 4.53 | 5.18 | 5.83 | 6.48 | `VERIFIED` (B) |
| `ELEMENTAL_MASTERY` | Elemental Mastery | 16.32 | 18.65 | 20.98 | 23.31 | `VERIFIED` (B) |
| `FLAT_HP` | HP | 209.13 | 239.00 | 268.88 | 298.75 | `VERIFIED` (B) |
| `FLAT_ATK` | ATK | 13.62 | 15.56 | 17.51 | 19.45 | `VERIFIED` (B) |
| `FLAT_DEF` | DEF | 16.20 | 18.52 | 20.83 | 23.15 | `VERIFIED` (B) |

### 3.4 Numerical Precision & Presentation Rule
* **Internal Storage:** Values are stored as full-precision IEEE-754 floating point numbers (or exact fixed-point decimals) (`ASSUMED` engineering standard). Cumulative value is:
  $$\text{value} = \text{initial\_value} + \sum_{i} \text{increment}_i$$
* **Display Layer Rule:**
  - Flat stats (`FLAT_HP`, `FLAT_ATK`, `FLAT_DEF`) and `ELEMENTAL_MASTERY`: rounded to nearest integer (`VERIFIED`, In-game UI).
  - Percentage stats (`CRIT_RATE`, `CRIT_DMG`, `ATK_PERCENT`, `HP_PERCENT`, `DEF_PERCENT`, `ENERGY_RECHARGE`): formatted to 1 decimal place (`VERIFIED`, In-game UI).
  - Rounding occurs **only at the presentation/API boundary**, never during internal state mutation.

---

## 4. Substat Candidate Pools & Selection Weights

When generating substats (both initial pool and drawing new slots), candidate stats are drawn without replacement from the 10 canonical substats, excluding the artifact's current main stat.

### 4.1 Substat Weights Ratio (6 / 6 / 6 / 4 / 4 / 4 / 4 / 4 / 3 / 3)
* **Evidence Level:** `INFERRED` (Level C Empirical player data, NGA Thread 33220261).
* **Weights:**
  - `FLAT_HP`: weight 6
  - `FLAT_ATK`: weight 6
  - `FLAT_DEF`: weight 6
  - `HP_PERCENT`: weight 4
  - `ATK_PERCENT`: weight 4
  - `DEF_PERCENT`: weight 4
  - `ENERGY_RECHARGE`: weight 4
  - `ELEMENTAL_MASTERY`: weight 4
  - `CRIT_RATE`: weight 3
  - `CRIT_DMG`: weight 3
* **Normalization:** Upon filtering out the current main stat, the remaining weights are normalized to sum to $1.0$ within the `ProbabilityEngine`.

---

## 5. Main-Stat Distributions per Slot

### 5.1 Fixed Slots (`VERIFIED`, Level A)
* `FLOWER`: 100% `FLAT_HP`
* `PLUME`: 100% `FLAT_ATK`

### 5.2 Sands of Eon (`INFERRED`, Level C)
* `HP_PERCENT`: 26.68%
* `ATK_PERCENT`: 26.66%
* `DEF_PERCENT`: 26.66%
* `ENERGY_RECHARGE`: 10.00%
* `ELEMENTAL_MASTERY`: 10.00%

### 5.3 Goblet of Eonothem (`INFERRED`, Level C)
* `HP_PERCENT`: 19.25%
* `ATK_PERCENT`: 19.25%
* `DEF_PERCENT`: 19.00%
* `PYRO_DMG_BONUS`: 5.00%
* `HYDRO_DMG_BONUS`: 5.00%
* `CRYO_DMG_BONUS`: 5.00%
* `ELECTRO_DMG_BONUS`: 5.00%
* `ANEMO_DMG_BONUS`: 5.00%
* `GEO_DMG_BONUS`: 5.00%
* `DENDRO_DMG_BONUS`: 5.00%
* `PHYSICAL_DMG_BONUS`: 5.00%
* `ELEMENTAL_MASTERY`: 2.50%

### 5.4 Circlet of Logos (`INFERRED`, Level C)
* `HP_PERCENT`: 22.00%
* `ATK_PERCENT`: 22.00%
* `DEF_PERCENT`: 22.00%
* `CRIT_RATE`: 10.00%
* `CRIT_DMG`: 10.00%
* `HEALING_BONUS`: 10.00%
* `ELEMENTAL_MASTERY`: 4.00%

---

## 6. Advanced Upgrade Systems (Roadmap Alignment)

The following modules are planned for subsequent phases and require strict gate sign-offs per `docs/PROJECT_PLAN.md` Section 4.5:
1. **Loot Sources (Phase P3):** Domain drops (80/20 initial lines, 20 resin, 50/50 set distribution) vs Strongbox (66/34 initial lines, 3-to-1 sacrifice).
2. **Sanctifying Elixir & Artifact Transmuter (Phase P4):** Custom craft with 2 chosen substats, guaranteed minimum 2 upgrade rolls.
3. **Artifact Reshaping & Hallowed Exegesis (Phase P4):** Redistribution of rolls using Dust of Enlightenment on +20 artifacts. Blocked until Hallowed Exegesis milestone conflict (6/12/18 vs 12/16) is formally resolved.
