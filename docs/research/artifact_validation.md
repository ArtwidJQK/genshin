# Artifact Research Validation

## 1. Research Scope & Epistemological Protocol

This document provides a hardened, 100%-auditable research record for all artifact mechanics, probability distributions, and configuration values implemented in **Artifact Foundation v1** of the Gacha & Artifact RNG Simulator.

### Epistemological Hierarchy
To ensure complete intellectual honesty and reproducibility, all claims are classified strictly by evidence tier:

| Evidence Level | Classification | Definition & Evidentiary Standard |
| :---: | :--- | :--- |
| **A** | **Official Source** | Primary HoYoverse sources: in-game UI, official in-game help tutorials, official patch announcements. |
| **B** | **Reverse-Engineering** | Direct inspection of extracted client metadata (`ExcelBinOutput` JSON configuration dumps). |
| **C** | **Large-Scale Player Data** | Crowdsourced empirical datasets and structured community theorycrafting studies. |
| **D** | **Community Observation** | Secondary wiki aggregators, community guides, and informal player observations. |
| **E** | **Speculation** | Unverified player impressions or hypotheses lacking empirical validation. |

### Core Epistemological Rule
The simulator maintains an unyielding separation between:
$$\text{Game Fact} \neq \text{Reverse-Engineered Fact} \neq \text{Empirical Observation} \neq \text{Community Consensus} \neq \text{Simulator Design Choice}$$

Secondary aggregators (e.g. Fandom Wiki) are never classified as Level A or B. Unverified numerical claims, speculative sample sizes, uncomputed error margins, and unverified statistical hypothesis claims are strictly prohibited.

---

## 2. Hardened Claim Matrix

| Claim # | Claim Description | Implementation in Simulator | Evidence Level | Epistemological Category | Status | Primary Auditable Source | Locator / Reference | Simulator Relationship |
|---|---|---|---|---|---|---|---|---|
| **1** | 5★ artifact has 4 conceptual substat slots | `len(substats) == 4` invariant on `Artifact` dataclass | **A** (Cap) / **Self** (Model) | Game Fact / Simulator Design Choice | **VERIFIED** | In-Game Client Help System | In-Game Menu: *Artifacts > Details* | Supported cap; 4-slot array invariant is an implementation detail |
| **2** | 3-line base artifact: 3 active substats, 4th unlocked at +4 without upgrade roll | Pre-generates 4th substat at +0 as `INACTIVE`; transitions to `ACTIVE` at +4 with `increment=0.0` | **A** (Game Rule) / **Self** (Pre-generation) | Game Fact / Simulator Design Choice | **VERIFIED** | In-Game Client Enhancement System | In-Game Menu: *Artifact Enhancement* | Game rule verified; +0 pre-generation is an implementation detail |
| **3** | 4-line base artifact: all 4 active at +0, +4 performs 1 upgrade roll | All 4 substats initialized as `ACTIVE`; +4 performs 1 uniform upgrade | **A** | Game Fact | **VERIFIED** | In-Game Client Enhancement System | In-Game Menu: *Artifact Enhancement* | Directly supported |
| **4** | +8, +12, +16, +20 each perform exactly 1 upgrade roll | Milestones 8, 12, 16, 20 trigger 1 `UPGRADE` event selecting an active substat | **A** | Game Fact | **VERIFIED** | In-Game Client Enhancement System | In-Game Menu: *Artifact Enhancement* | Directly supported |
| **5** | Initial substat selection: no duplicates, cannot match main stat | Filters `main_stat` from candidate pool; sequentially draws 4 distinct substats | **A** (Uniqueness) & **B** (Datamine Filter) | Game Fact & Reverse-Engineered Fact | **VERIFIED** | Dimbreath / `AnimeGameData` | `ExcelBinOutput/ReliquaryAffixExcelConfigData.json` | Directly supported |
| **6** | Initial substat weight ratios: 6 / 6 / 6 / 4 / 4 / 4 / 4 / 4 / 3 / 3 | `config/artifacts/substats.json` weights (Flat=6, %=4, Crit=3) | **C** | Empirical Observation / Community Consensus | **PARTIALLY VERIFIED** | NGA Research Thread (TID: 33220261) | Thread: *圣遗物词条分布汇总一图流* | Community model; server integer weights remain unrevealed |
| **7** | Initial line count distribution: 80% 3-line vs 20% 4-line | `config/artifacts/rules.json`: `{"3": 80, "4": 20}` | **C** (Domain Drops Only) | Empirical Observation (Source-Dependent) | **PARTIALLY VERIFIED** | Genshin Data Gathering Team | Sheet: *Drop Rates*, Tab: *Artifact Quality* | Models Domain drops only; Strongbox/Bosses (66/34) not yet modeled |
| **8** | Upgrade target selection: uniform 25% among 4 active substats | `prob_engine.weighted_choice([0,1,2,3], [1,1,1,1])` | **C / D** | Empirical Observation / Community Consensus | **PARTIALLY VERIFIED** | KeqingMains — Genshin Impact Artifacts Guide | `https://keqingmains.com/misc/artifacts/` (*Enhancing Artifacts*) | Community-supported modeling assumption |
| **9** | Roll tiers (70%, 80%, 90%, 100%) and 25% tier distribution | `config/artifacts/roll_values.json`: 4 discrete tiers, weights = 25 each | **B** (Tiers & Values) & **C / D** (Tier Probability) | Reverse-Engineered Fact (Values) / Empirical Consensus (Weights) | **PARTIALLY VERIFIED** | Dimbreath / `AnimeGameData` | `ExcelBinOutput/ReliquaryAffixExcelConfigData.json` | Tier existence & values directly supported; 25% equal weight is empirical |
| **10** | Main-stat distribution tables per slot | `config/artifacts/main_stats.json`: Flower/Plume fixed; Sands/Goblet/Circlet weighted | **A** (Flower/Plume) & **C** (Sands/Goblet/Circlet) | Game Fact (Fixed) / Empirical Approximation (Weights) | **PARTIALLY VERIFIED** | In-Game Client (Fixed) & NGA TID: 33220261 | Thread: *圣遗物词条分布汇总一图流* | Flower/Plume directly supported; decimal percentages are empirical approximations |

---

## 3. Strict Audit of High-Risk Claims (Claims 6, 7, 8, 9, 10)

### Audit of Claim 6: Initial Substat Weights (6 / 6 / 6 / 4 / 4 / 4 / 4 / 4 / 3 / 3)
- **Evidence Level**: **Level C** (Empirical Player Data / Reverse-Engineered Community Model).
- **Audit Findings**:
  1. This claim is **NOT Level A** (HoYoverse has never published internal drop weights).
  2. This claim is **NOT Level B** from client datamines: while `ReliquaryAffixExcelConfigData.json` lists candidate affix entries, the probability weights controlling random draws reside in **proprietary server-side configuration**.
  3. The integer ratio $6 : 6 : 6 : 4 : 4 : 4 : 4 : 4 : 3 : 3$ is an empirical model proposed by NGA theorycrafting researchers (Thread: 33220261) based on observed drops:
     - Flat HP, Flat ATK, Flat DEF: weight 6 (~13.6% each in a full pool)
     - HP%, ATK%, DEF%, Energy Recharge%, Elemental Mastery: weight 4 (~9.1% each)
     - CRIT Rate%, CRIT DMG%: weight 3 (~6.8% each)
- **What the Source Establishes**: Large-scale player drops consistently demonstrate that Flat stats are most frequent, Percentage/ER/EM stats are intermediate, and CRIT stats are least frequent, matching the 6:4:3 ratio.
- **What the Source Does NOT Establish**: Does not prove that the server's internal integer constants are literally $\{6, 4, 3\}$ (e.g. they could be $\{600, 400, 300\}$ or another scale).
- **Simulator Status**: **Empirically Inferred Model**.

### Audit of Claim 7: 80/20 Initial Line Count Distribution
- **Evidence Level**: **Level C** (Crowdsourced Drop Records).
- **Audit Findings**:
  1. The 80% (3-line) / 20% (4-line) distribution is **SOURCE-DEPENDENT** and must not be presented as a universal rule.
  2. **Domain of Blessing Drops**: The Genshin Data Gathering Team dataset records domain artifact drops matching approximately **80% 3-line vs 20% 4-line** (or a 4:1 ratio).
  3. **Artifact Strongbox, World Bosses, Weekly Bosses, and Spiral Abyss Reliquaries**: The same crowdsourced dataset records an initial distribution of approximately **66% 3-line vs 34% 4-line** (or a 2:1 ratio).
- **What the Source Establishes**: The initial line count distribution depends on the artifact's acquisition source.
- **What the Source Does NOT Establish**: No official developer rate has ever been published.
- **Simulator Status**: **Domain-Specific Approximation**. Current simulator configuration (`config/artifacts/rules.json`) strictly represents **Domain drops**. Multi-source drop differentiation remains an open feature gap.

### Audit of Claim 8: Uniform 25% Upgrade Target Selection
- **Evidence Level**: **Level C / D** (Community / Theorycrafting Documentation).
- **Primary Source**: KeqingMains — Genshin Impact Artifacts Guide
- **URL**: `https://keqingmains.com/misc/artifacts/`
- **Locator**: Section: *Enhancing Artifacts*, paragraph beginning with: *"An artifact with the maximum number of different substats..."*
- **Audit Findings**:
  1. The KeqingMains Artifact Guide explicitly documents the standard community model for substat upgrades: when an artifact has 4 different substats, each upgrade milestone (+4, +8, +12, +16, +20) rolls into one of those 4 substats at random with equal probability ($25\%$ each).
  2. The source explicitly establishes that previous upgrade counts on a substat do not alter future selection probabilities (independent uniform trials).
  3. No proprietary server source code or official developer disclosure is publicly accessible. The uniform $25\%$ assumption is an empirically observed community theorycrafting model supported by long-term player observation showing no systemic bias toward specific stats (e.g., DEF over CRIT).
- **What the Source Establishes**:
  - An artifact with 4 different substats rolls into one of those substats every 4 levels.
  - The upgraded substat is selected at random with equal probability for each substat ($25\%$ each).
  - Previous upgrade counts do not alter the selection probability.
- **What the Source Does NOT Establish**:
  - It does not expose HoYoverse's proprietary server RNG implementation or server-side probability constants.
- **Simulator Status**: **Community-Supported Modeling Assumption** (implemented as uniform choice `[1, 1, 1, 1]` across the 4 active slots).

### Audit of Claim 9: Roll Tiers (70%, 80%, 90%, 100%) and Tier Probabilities
- **Evidence Level**:
  - Existence of 4 tiers and numerical values: **Level B** (Client Datamine).
  - Equal 25% tier probability: **Level C / D** (Community Consensus).
- **Audit Findings**:
  1. **Level B Evidence**: In `ReliquaryAffixExcelConfigData.json`, every 5★ substat type defines exactly 4 affix entries with concrete numerical values corresponding to multipliers of $\approx 0.70, 0.80, 0.90, 1.00$ relative to the highest roll.
  2. **Level B Limitation**: The client JSON files **do NOT expose the server-side tier probability weights**.
  3. **Level C Evidence**: Community observation assumes an unweighted 1:1:1:1 ($25\%$ each) draw across the four tiers.
- **What the Source Establishes**: The 4 discrete numeric tiers exist in game client files.
- **What the Source Does NOT Establish**: Client files do not prove server-side equal probability across tiers.
- **Simulator Status**: **Datamined Values (Level B) + Community Equal-Weight Assumption (Level C)**.

### Audit of Claim 10: Main-Stat Distribution Tables
- **Evidence Level**:
  - Flower = Flat HP, Plume = Flat ATK: **Level A** (Official Game Rule).
  - Slot Main-Stat Pools: **Level A / B** (In-game restrictions & Client metadata).
  - Sands, Goblet, Circlet Decimal Frequencies: **Level C** (Empirical Player Data).
- **Audit Findings**:
  1. Flower of Life always possesses `FLAT_HP` main stat, and Plume of Death always possesses `FLAT_ATK` main stat (Level A).
  2. For Sands, Goblet, and Circlet, the decimal values stored in `config/artifacts/main_stats.json` (e.g., Sands: HP% 26.68, ATK% 26.66, DEF% 26.66) are **empirical sample frequencies**, not canonical server integer weights.
  3. The underlying server likely operates on integer weights (e.g., $800, 800, 800, 300, 300$, yielding $26.67\%$).
- **What the Source Establishes**: Establishes the relative rarity tiers of main stats (e.g., Goblet elemental bonuses $\approx 5\%$, EM $\approx 2.5\%$; Circlet CRIT $\approx 10\%$).
- **What the Source Does NOT Establish**: Does not provide exact server-side integer weights.
- **Simulator Status**: **Empirical Decimal Approximation of Server Tables**.

---

## 4. Simulator Design Choices vs Game Facts

To prevent confusion between Genshin Impact mechanics and our internal Python software architecture, the following distinctions are explicitly codified:

| Component | Genshin Impact Game Reality | Simulator Implementation Detail | Rationale & Architectural Purpose |
|---|---|---|---|
| **Substat Array Representation** | Displays 3 lines at +0 for 3-line artifacts; displays 4 lines at +4 | Fixed 4-element `List[Substat]` dataclass invariant (`len(substats) == 4`) | Avoids dynamic list memory re-allocation, maintains constant slot indexing (0–3), and supports previewing. |
| **Fourth Substat Chronology** | Server resolves the 4th substat invisibly (either at drop or upon reaching +4) | Pre-generated at +0 with `state = SubstatState.INACTIVE`; activated at +4 | Guarantees deterministic replayability from a single RNG seed and eliminates lazy-state initialization side effects. |
| **RNG Stream Consumption** | Proprietary backend server RNG pipeline (unobservable) | Sequential single-stream draws via isolated `ProbabilityEngine` | Ensures deterministic, thread-safe, seed-reproducible test execution without global Python `random` pollution. |
| **Progression Tracking** | Player inventory stores current numeric values | Append-only audit trail via `EnhancementEvent` and `SubstatRoll` dataclasses | Provides complete domain auditability and event replay for analysis and debugging. |

---

## 5. Unverified Claims, Approximations & Known Conflicts

The following items are explicitly acknowledged as empirical approximations or context-dependent models:

1. **Source Dependency of Line Count (Conflict)**:
   - Current simulator configuration (`config/artifacts/rules.json`) applies `{"3": 80, "4": 20}` universally.
   - This accurately models **Domain drops**, but does **NOT** model Strongbox, Boss, or Abyss Reliquary drops (~66% / ~34%).
   - *Status*: Documented gap; to be parameterized in a future multi-source drop engine.

2. **Empirical Main-Stat Decimals vs Server Integers (Approximation)**:
   - `config/artifacts/main_stats.json` stores empirical sample percentages (e.g. 26.68 / 26.66 / 26.66) rather than true server integer weights.
   - *Status*: Functionally sufficient for probabilistic simulation; documented as an approximation.

3. **Substat Float Rounding vs Client Truncation (Precision Discrepancy)**:
   - `config/artifacts/roll_values.json` stores values rounded to 2 decimal places (e.g., CRIT Rate 3.89%), whereas client metadata (`ReliquaryAffixExcelConfigData.json`) stores unrounded floating-point numbers ($\approx 3.887\%$).
   - Summing 2-decimal rounded floats can occasionally differ by $\pm 0.1\%$ from in-game display rounding after multiple rolls.
   - *Status*: Documented minor display discrepancy.

---

## 6. Source Provenance Catalog

Compact, auditable provenance records for all external sources cited in this research:

### Source 1: HoYoverse In-Game Client System
- **Source**: *Genshin Impact* Game Client (PC/Mobile/Console)
- **URL**: `https://genshin.hoyoverse.com/` (Game Client)
- **Evidence Level**: **A**
- **What Was Inspected**: In-game Artifact Help Tutorial, Inventory UI, and Artifact Enhancement Interface.
- **Locator**: In-game menu: *Artifacts > Details > Help (?) / Enhancement*.
- **Claims Supported**: Claim 1 (4-substat cap), Claim 2 (3-line +4 activation), Claim 3 (4-line +4 upgrade), Claim 4 (+8/+12/+16/+20 milestone upgrades), Claim 5 (main stat exclusion & substat uniqueness), Claim 10 (Flower=Flat HP, Plume=Flat ATK).
- **Limitations**: In-game client does not disclose hidden RNG drop tables, server-side weight constants, or roll probability distributions.

### Source 2: Dimbreath Game Data Extraction (`AnimeGameData` / `GenshinData`)
- **Source**: Dimbreath Game Data Extraction Repository
- **URL**: `https://gitlab.com/Dimbreath/animegamedata2` (Mirror: `https://github.com/DimbreathBot/AnimeGameData`)
- **Evidence Level**: **B**
- **What Was Inspected**: Client-side extracted JSON configuration dumps.
- **Locator**:
  - `ExcelBinOutput/ReliquaryAffixExcelConfigData.json`
  - `ExcelBinOutput/ReliquaryMainPropExcelConfigData.json`
  - `ExcelBinOutput/ReliquaryExcelConfigData.json`
- **Claims Supported**: Claim 5 (Candidate property groupings and exclusions), Claim 9 (Existence of 4 discrete tiers per substat and their exact numerical values), Claim 10 (Valid main stats per slot).
- **Limitations**: Client files only contain display values, asset IDs, and tier increments; they do NOT contain server-side drop weights or RNG generation algorithms.

### Source 3: NGA Research Thread *圣遗物词条分布汇总一图流*
- **Source**: NGA Forum Theorycrafting Post by 玫瑰黎明 (Rose Dawn)
- **URL**: `https://nga.178.com/read.php?tid=33220261`
- **Evidence Level**: **C**
- **What Was Inspected**: Empirical study consolidating community artifact drop records and proposing distribution models.
- **Locator**: Main post infographic & data tables: *圣遗物词条分布规律与概率汇总*.
- **Claims Supported**: Claim 6 (Initial substat weight ratio model 6/6/6/4/4/4/4/4/3/3), Claim 10 (Sands, Goblet, Circlet empirical distribution percentages).
- **Limitations**: Crowd-sourced player collection subject to reporting variance; does not represent official developer disclosure.

### Source 4: Genshin Data Gathering Team Drop Rates Dataset
- **Source**: Genshin Data Gathering Team
- **URL**: `https://docs.google.com/spreadsheets/d/10DF-Wqn-79SxTeSZPAY__RW1uGtpphAx4rG97akYskY/edit?gid=749900704#gid=749900704`
- **Evidence Level**: **C**
- **What Was Inspected**: Publicly maintained crowdsourced drop tracking spreadsheet.
- **Locator**: Sheet: `Drop Rates`, Tabs: `Artifact Quality` and `Initial Minor Affix`.
- **Claims Supported**: Claim 7 (80% 3-line vs 20% 4-line for Domain drops; 66% 3-line vs 34% 4-line for Strongbox, Bosses, and Reliquaries).
- **Limitations**: Empirical volunteer submissions; subject to sampling noise.

### Source 5: KeqingMains — Genshin Impact Artifacts Guide
- **Source**: KeqingMains (KQM) Theorycrafting Organization
- **URL**: `https://keqingmains.com/misc/artifacts/`
- **Evidence Level**: **C / D** (Community / Theorycrafting Documentation)
- **What Was Inspected**: Primary community artifact mechanics guide maintained by KQM.
- **Locator**: Section: *Enhancing Artifacts*, paragraph beginning with: *"An artifact with the maximum number of different substats..."*
- **Claims Supported**: Claim 8 (Uniform selection among the currently active 4 substats: an artifact with 4 substats upgrades one at random with equal probability each milestone; prior upgrades do not affect future odds).
- **Limitations**: Community documentation summarizing player observation and theorycrafting consensus; does not expose HoYoverse's proprietary server-side RNG implementation or server source code.

### Source 6: Genshin Impact Fandom Wiki
- **Source**: Fandom Community Wiki
- **URL**:
  - `https://genshin-impact.fandom.com/wiki/Artifact/Distribution`
  - `https://genshin-impact.fandom.com/wiki/Loot_System/Artifact_Drop_Distribution`
- **Evidence Level**: **D** (Secondary Community Aggregator)
- **What Was Inspected**: Community synthesis of NGA, Genshin Data Gathering, and in-game observations.
- **Locator**: Sections: *Main Affix*, *Minor Affix Attribute*, *Minor Affix Value*, *Initial Minor Affix Count Distribution*.
- **Claims Supported**: Corroborates community consensus across Claims 6, 7, 8, 9, 10.
- **Limitations**: Strictly a secondary wiki aggregator; cannot be used as primary proof for Level A or Level B assertions.

---

## 7. Configuration Provenance

Full provenance audit for files in `config/artifacts/`:

### 7.1 `config/artifacts/main_stats.json`
- **Source**: In-Game Rules (Flower/Plume) & NGA Thread TID: 33220261 (Sands/Goblet/Circlet).
- **Evidence Level**: **A** (Flower/Plume fixed stats) / **C** (Sands/Goblet/Circlet empirical percentages).
- **Confidence**: **HIGH** for slot rules; **MEDIUM** for exact decimal weight precision.
- **Status**: Empirical approximation of proprietary server drop tables.

### 7.2 `config/artifacts/substats.json`
- **Source**: Client metadata `ReliquaryAffixExcelConfigData.json` (canonical 10 stats) & NGA Thread TID: 33220261 (6/4/3 weights).
- **Evidence Level**: **B** (10 canonical keys) / **C** (6/6/6/4/4/4/4/4/3/3 integer weight ratios).
- **Confidence**: **MEDIUM-HIGH** (Qualitatively certain on relative tier weights; integer ratios are community models).
- **Status**: Reverse-engineered community consensus model.

### 7.3 `config/artifacts/roll_values.json`
- **Source**: Dimbreath extracted table `ReliquaryAffixExcelConfigData.json` (values) & Community Consensus (tier weights).
- **Evidence Level**: **B** (Exact 4 tiers & values) / **C** (Uniform 25% weight per tier).
- **Confidence**: **HIGH** for values; **MEDIUM** for uniform 25% tier distribution.
- **Status**: Canonical datamined tier values with community equal-probability configuration.

### 7.4 `config/artifacts/rules.json`
- **Source**: In-Game Rules (`rarity`, `max_level`, `milestone_levels`, `num_substat_slots`) & Genshin Data Gathering Team (`initial_line_count_weights`).
- **Evidence Level**: **A** (Rules and milestones) / **C** (Domain 80/20 initial line distribution).
- **Confidence**: **HIGH** for game rules; **MEDIUM** for 80/20 (Domain-specific).
- **Status**: Canonical for domain farming; lacks source-specific parameters for strongboxes and bosses.

---

## 8. Final Research Confidence Matrix

| Claim | Description | Evidence Level | Research Confidence | Simulator Implementation Usage |
|---|---|:---:|:---:|---|
| **Claim 1** | 5★ Artifact 4-substat cap | **A** / **Self** | **HIGH** | Invariant in domain model (`len(substats) == 4`) |
| **Claim 2** | 3-line base +4 activation without upgrade | **A** / **Self** | **HIGH** | State transition from `INACTIVE` to `ACTIVE` |
| **Claim 3** | 4-line base +4 upgrade roll | **A** | **HIGH** | Standard upgrade roll at +4 |
| **Claim 4** | +8, +12, +16, +20 milestone upgrades | **A** | **HIGH** | Standard upgrade roll at each milestone |
| **Claim 5** | Substat deduplication & main stat exclusion | **A** & **B** | **HIGH** | Candidate pool filtering before draw |
| **Claim 6** | Substat weights 6/6/6/4/4/4/4/4/3/3 | **C** | **MEDIUM-HIGH** | Directly configured in `substats.json` |
| **Claim 7** | Initial line distribution (80/20 vs 66/34) | **C** | **MEDIUM** | Approximates Domain drops (80/20) in `rules.json` |
| **Claim 8** | Uniform 25% upgrade target selection | **C / D** | **MEDIUM** | Uniform weighted choice in `engine.py` |
| **Claim 9** | Roll tier values & 25% tier distribution | **B** & **C** | **MEDIUM-HIGH** | Configured in `roll_values.json` |
| **Claim 10** | Main-stat distribution tables | **A** & **C** | **MEDIUM-HIGH** | Configured in `main_stats.json` |

---

## 9. Research Gaps for P2 (Character Gacha)

Prior to entering **P2 — Character Gacha Engine**, the following mechanics must be researched with the same auditable rigor:

1. **Base Published Probabilities (Level A)**:
   - Official base 5★ character drop rate: $0.6\%$ (in-game Wish Details).
   - Official base 4★ character drop rate: $5.1\%$ (in-game Wish Details).
   - Official consolidated 5★ rate with pity: $1.6\%$ (in-game Wish Details).
   - Official consolidated 4★ rate with pity: $13.0\%$ (in-game Wish Details).

2. **Soft Pity Curve (Level C)**:
   - Threshold where pull probability ramps up (community consensus: pull 74 on character banner).
   - Exact mathematical function or per-pull slope between pulls 74 and 90 (needs auditable empirical citation).

3. **50/50 Guarantee & Carryover Rules (Level A)**:
   - 50% chance of featured character on non-guaranteed 5★ pull.
   - 100% guarantee on subsequent 5★ pull if prior 5★ was non-featured (standard character).
   - Pity count and guarantee carryover across limited banners of the same type.

4. **Capturing Radiance Mechanic (Version 5.0+) (Level A / C)**:
   - Official mechanic introduced in Version 5.0 to boost 5★ win rate.
   - Exact trigger condition, probability adjustment, and interaction with 50/50 failure streaks.

5. **4★ Character Pity & Featured Unit Rules (Level A)**:
   - 10-pull hard pity for 4★ items.
   - 50% chance of featured 4★ with guarantee on non-featured pull.
   - Distribution across the 3 featured 4★ characters on the banner.
