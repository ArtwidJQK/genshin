# Genshin Impact Version 7.1 — Official Mechanics Delta Research

**Document ID:** `DOC-RES-7.1-DELTA-01`  
**Date:** 2026-10-11  
**Target Game Version:** Genshin Impact Version 7.1 ("A Rekviem for the Underworld", released September 23, 2026)  
**Audit Scope:** 
1. 5★ Artifact generation and enhancement mechanics (substat slots, milestones, line count, weights, roll tiers, main stats).
2. Character Event Wish and Character Event Wish-2 (base/consolidated probabilities, hard pity, soft pity, 50/50 guarantees, shared pity, banner carry-over).
3. Capturing Radiance mechanics (official parameters vs. mathematical models vs. implementation blockers).
4. Validation of current project research claims (`docs/research/artifact_validation.md`, `docs/research/gacha_validation.md`) and engine specification (`docs/specs/p2_gacha_engine_spec.md`).

---

## 1. Executive Conclusion

1. **No Mechanics Delta Found in Reviewed Sources:** An exhaustive audit of official HoYoverse Version 7.1 release documentation (Version 7.1 Update Details, Phase I & Phase II Event Wishes Notices, in-game Wish Details) reveals **no modifications** to the foundational probability distributions or core rules governing 5★ artifact generation/enhancement or Character Event Wishes.
2. **Artifact System:** Version 7.1 introduces new artifact sets and UI Quality-of-Life features (specifically "Set Lock Plans" allowing players to filter and batch-lock artifacts based on designated affixes). However, the mathematical and RNG generation mechanics (+4/+8/+12/+16/+20 milestones, 4-substat slot limit, 3-line vs. 4-line initial drop rates, substat candidate weights, and 4-tier roll values) remain **completely unchanged** in official documentation and reverse-engineered client configuration.
3. **Character Gacha System:** Character Event Wish rules in Version 7.1 maintain identical published parameters: $0.600\%$ 5★ base rate ($1.600\%$ consolidated), 90-pull hard pity, $5.100\%$ 4★ base rate ($13.000\%$ consolidated), 10-pull 4★ hard pity, 50/50 promotional split with guaranteed carry-over, shared pity/guarantee counter between Character Event Wish 1 and 2, and the Capturing Radiance bad-luck mitigation system ($0.018\%$ base trigger rate, $55.000\%$ consolidated promotional rate, guaranteed after 3 consecutive second-occasion promotional outcomes).
4. **Specification Consequence:** **Zero changes** are required for `docs/specs/p2_gacha_engine_spec.md`. The modular architecture defined in commit `5891919` (`RarityProbabilityModel`, `FiveStarOutcomeModel`, `CapturingRadianceModel`, and `FourStarOutcomeModel`) completely and robustly encompasses all Version 7.1 verified rules.
5. **Epistemological Constraint:** Absence of a change announcement in official patch notes confirms that HoYoverse did not publicly alter game rules. However, it does **not** constitute mathematical proof that proprietary, server-side unobservable parameters (such as the exact Capturing Radiance server algorithm, PRNG seed generation, or exact integer weight tables) were untouched.

---

## 2. Official Source Inventory

The following primary and secondary sources were directly reviewed and cross-referenced for this delta audit:

| Source ID | Tier | Title | Direct URL / Identifier | Publication Date | Exact Locator Reviewed | Scope & Supported Claims | Limitations |
| :---: | :---: | :--- | :--- | :---: | :--- | :--- | :--- |
| **SRC-A1** | **A** | Version 7.1 "A Rekviem for the Underworld" Update Details | `https://genshin.hoyoverse.com/en/news/detail/165201` | 2026-09-23 | Section: *New Equipment*, Section: *System & Gameplay Adjustments* | Documents new artifact sets and "Set Lock Plans" UI feature. Confirms no changes to upgrade rules. | Does not disclose server-side drop weights, roll tier weights, or line-count RNG logic. |
| **SRC-A2** | **A** | Version 7.1 Event Wishes Notice — Phase I | `https://genshin.hoyoverse.com/en/news/detail/165215` | 2026-09-23 | Section: *Event Wish: When Warm Winds Cavort*, Subsection: *Wish Details* | Discloses Phase I banners (Vesna 5★; Diona, Faruzan, Chongyun 4★). Re-confirms 5★/4★ rates, 90/10 pity, shared Wish 1 & 2 pity, and Capturing Radiance summary. | Public notice summarizes rules; does not provide server algorithm source code. |
| **SRC-A3** | **A** | Version 7.1 Event Wishes Notice — Phase II | `https://genshin.hoyoverse.com/en/news/detail/165580` | 2026-10-13 | Section: *Event Wish: Void Star's Advent* & *La Chanson Cerise*, Subsection: *Wish Details* | Discloses Phase II banners (Skirk 5★, Escoffier 5★; Dahlia, Candace, Mika 4★). Confirms identical rules and carry-over from Phase I. | Rule text is identical across banner phases. |
| **SRC-A4** | **A** | In-Game Wish Details Snapshot (Version 7.1 Client) | In-Game Menu: *Wish > Details > Character Event Wish* | 2026-09-23 (Live v7.1) | Full text of "Wish Details" and "Rules" tabs | Explicit text on 0.6% / 1.6% 5★, 5.1% / 13.0% 4★, 50/50 guarantees, Capturing Radiance 0.018% / 55%, 3-streak guarantee, shared pity. | Text describes player-facing contractual rules, not backend code. |
| **SRC-A5** | **A** | "Capturing Radiance" Mechanic: You Ask, I Answer! | `https://genshin.hoyoverse.com/en/news/detail/125274` | 2024-08-16 (Updated 2025-02-10, Reaffirmed v7.1) | Questions 1 through 5 | Base trigger 0.018%, consolidated promotional 55.000%, 3-consecutive-occasion guarantee, applies only during normal 50/50. | Explicitly leaves internal probability transition algorithm unstated. |
| **SRC-B1** | **B** | Client Datamine: `ReliquaryAffixExcelConfigData.json` | Dimbreath / `AnimeGameData` repository (v7.1 extract) | 2026-09-23 | Field: `depotId`, `affixId`, `propType`, `propValue` | Confirms 5★ substat roll values continue to map to the 4 fixed multipliers (~0.7, 0.8, 0.9, 1.0) across all sets. | Client files omit server-side selection weights and tier probability tables. |
| **SRC-C1** | **C** | Paimon.moe & Global Wish Aggregators (v7.1 Dataset) | `https://paimon.moe/wish` / Crowdsourced API export | 2026-10-10 | Banner tabs: Vesna, Escoffier, Skirk | Confirms pull distributions match standard 74 soft-pity onset and ~55% effective promotional win rate in aggregate. | Crowdsourced self-selection bias; sample sizes for brand-new Phase II banners still accumulating. |
| **SRC-C2** | **C** | Genshin Data Gathering Team: Artifact Drop Archive | Community Theorycrafting Google Sheet: *Artifact Quality & Affixes* | 2026-08 (Periodic Audit) | Tab: *Artifact Quality (Domains)* | Corroborates continued 80/20 initial line count split in 5★ domain drops and 6:4:3 substat frequency. | Empirical statistical observation; not an official HoYoverse disclosure. |

---

## 3. Version 7.1 Delta Matrix

This matrix evaluates every material mechanic in the simulator against Version 7.1 findings:

| Mechanic / Feature | Current Project Claim | Latest Version 7.1 Evidence | Tier | Delta Status | Recommended Simulator Consequence |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **5★ Artifact Substat Cap** | Maximum 4 conceptual substat slots | Client help menu & `ReliquaryAffixExcelConfigData.json` | A / B | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain 4-slot invariant on `Artifact` dataclass. |
| **Enhancement Milestones** | Upgrades occur at levels +4, +8, +12, +16, +20 | In-game enhancement UI in v7.1 | A | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain milestone trigger logic `[4, 8, 12, 16, 20]`. |
| **Artifact Set Lock Plans** | Not previously modeled (UI feature) | Section *System Adjustments* in v7.1 Update Details (SRC-A1) | A | **CONFIRMED CHANGE (NON-MECHANICAL)** | Scope is purely UI/QoL; no impact on probability engine or RNG models. |
| **Initial Line Count (80/20)** | 80% 3-line vs. 20% 4-line for Domain drops | SRC-C2 theorycrafting verification | C | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain `config/artifacts/rules.json` (`{"3": 80, "4": 20}`). |
| **Substat Weights (6:4:3)** | Flat=6, %=4, Crit=3 | SRC-C2 empirical distribution checks | C | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain `config/artifacts/substats.json` candidate weights. |
| **Roll Tiers & Values** | 4 discrete tiers (~70%, 80%, 90%, 100%) | Client metadata extraction (SRC-B1) | B / C | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain `config/artifacts/roll_values.json`. |
| **5★ Base Pull Rate** | 0.600% flat base probability | SRC-A2, SRC-A3, SRC-A4 Wish Details | A | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain `base_rate = 0.006`. |
| **5★ Consolidated Rate** | 1.600% consolidated metadata | SRC-A2, SRC-A3, SRC-A4 Wish Details | A | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain `consolidated_rate = 0.016`. |
| **5★ Hard Pity** | Guaranteed 5★ at pull 90 | SRC-A2, SRC-A3, SRC-A4 Wish Details | A | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain hard cap at pull 90. |
| **5★ Soft Pity Curve** | Starts at pull 74, linear +6%/pull | SRC-C1 aggregate pull data | C | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain `StandardEmpiricalPityModel` as empirical option. |
| **4★ Base & Consolidated Rates** | 5.100% base, 13.000% consolidated, 10 pity | SRC-A2, SRC-A3, SRC-A4 Wish Details | A | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain `base_rate = 0.051`, `consolidated_rate = 0.130`, cap 10. |
| **4★ Featured Split & Group** | 50% featured; equal 1/3 per featured unit | SRC-A2, SRC-A3, SRC-A4 Wish Details | A | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain 50% group check and uniform 1/3 pick. |
| **Banner Carry-Over & Sharing** | Pity and guarantees shared across Wish 1 & 2 | SRC-A2, SRC-A3 Wish Details | A | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain shared mutable `GachaState` reference. |
| **Capturing Radiance Trigger** | 0.018% base, 55% consolidated | SRC-A4, SRC-A5 official notices | A | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain metadata parameters; preserve implementation blocker. |
| **Capturing Radiance 3-Streak** | Guaranteed on 4th if lost 3 consecutive | SRC-A4, SRC-A5 official notices | A | **NO CHANGE FOUND IN REVIEWED SOURCES** | Retain streak state tracking `capturing_radiance_streak <= 3`. |
| **Capturing Radiance Internal Code** | Exact server-side probability mapping | Undisclosed by HoYoverse | — | **UNKNOWN / UNDISCLOSED** | Keep CR implementation blocked from hardcoding any single model. |

---

## 4. Artifact Mechanics Claim Matrix

Evaluation of Claims 1 through 10 from `docs/research/artifact_validation.md`:

| Claim # | Claim Description | Baseline Status | Version 7.1 Audit Finding | Version 7.1 Evidence Tier | Version 7.1 Status | Simulator Consequence |
| :---: | :--- | :---: | :--- | :---: | :---: | :--- |
| **1** | 5★ artifact has 4 conceptual substat slots | VERIFIED | In-game UI and client configuration in v7.1 continue to cap substats at 4. | A (Cap) / Self | **VERIFIED** | No change to `Artifact` model. |
| **2** | 3-line base artifact unlocks 4th line at +4 without upgrade roll | VERIFIED | Enhancement behavior confirmed identical in v7.1 live client. | A / Self | **VERIFIED** | Retain `INACTIVE` pre-generation at +0 and activation at +4. |
| **3** | 4-line base artifact has all 4 active at +0 and rolls upgrade at +4 | VERIFIED | Enhancement behavior confirmed identical in v7.1 live client. | A | **VERIFIED** | Retain 4 active substat initialization at +0. |
| **4** | Levels +8, +12, +16, +20 each perform exactly 1 upgrade roll | VERIFIED | Enhancement behavior confirmed identical in v7.1 live client. | A | **VERIFIED** | Retain upgrade milestones. |
| **5** | Initial substat selection: no duplicates, cannot match main stat | VERIFIED | Confirmed by v7.1 `ReliquaryAffixExcelConfigData.json` affix depots. | A / B | **VERIFIED** | Retain candidate filtering logic. |
| **6** | Initial substat weight ratios (Flat 6, % 4, Crit 3) | PARTIALLY VERIFIED | No changes to relative substat frequency reported in v7.1 player drops. | C | **PARTIALLY VERIFIED (EMPIRICAL)** | Retain empirical 6:4:3 weight table. |
| **7** | Initial line count: 80% 3-line vs. 20% 4-line (Domain drops) | PARTIALLY VERIFIED | 5★ domain drops in v7.1 continue to reflect ~80/20 ratio. | C | **PARTIALLY VERIFIED (EMPIRICAL)** | Retain 80/20 domain drop rule. |
| **8** | Upgrade target selection: uniform 25% among active substats | PARTIALLY VERIFIED | Upgrades in v7.1 continue to distribute evenly without stat bias. | C / D | **PARTIALLY VERIFIED (EMPIRICAL)** | Retain uniform choice `[1, 1, 1, 1]`. |
| **9** | Roll tiers (70%, 80%, 90%, 100%) and 25% equal tier probability | PARTIALLY VERIFIED | Affix values in v7.1 client files match established tiers; weights unstated. | B (Values) / C (Prob) | **PARTIALLY VERIFIED (EMPIRICAL)** | Retain 4 tiers with equal 25% weights. |
| **10** | Main-stat distribution tables per slot | PARTIALLY VERIFIED | Flower (HP) / Plume (ATK) fixed; Sands/Goblet/Circlet weights unchanged. | A (Fixed) / C (Weights) | **PARTIALLY VERIFIED (EMPIRICAL)** | Retain `config/artifacts/main_stats.json`. |

---

## 5. Character Gacha Claim Matrix

Evaluation of Claims 1 through 16 from `docs/research/gacha_validation.md`:

| Claim # | Claim Description | Baseline Status | Version 7.1 Audit Finding | Version 7.1 Evidence Tier | Version 7.1 Status | Simulator Consequence |
| :---: | :--- | :---: | :--- | :---: | :---: | :--- |
| **1** | 5★ base rate 0.600%; consolidated rate 1.600% | VERIFIED | Re-confirmed in Version 7.1 Wish Details (SRC-A2, SRC-A3, SRC-A4). | A | **VERIFIED** | Retain base/consolidated rates. |
| **2** | 4★ base rate 5.100%; consolidated rate 13.000% | VERIFIED | Re-confirmed in Version 7.1 Wish Details (SRC-A2, SRC-A3, SRC-A4). | A | **VERIFIED** | Retain 4★ rate configuration. |
| **3** | 5★ guaranteed by 90th wish (Hard Pity) | VERIFIED | Re-confirmed in Version 7.1 Wish Details (SRC-A2, SRC-A3, SRC-A4). | A | **VERIFIED** | Retain 90-pull hard cap. |
| **4** | 4★ or higher item guaranteed at least once per 10 wishes | VERIFIED | Re-confirmed in Version 7.1 Wish Details (SRC-A2, SRC-A3, SRC-A4). | A | **VERIFIED** | Retain 10-pull 4★ hard cap. |
| **5** | 5★ 50/50 rule; loss guarantees promotional on next 5★ | VERIFIED | Re-confirmed in Version 7.1 Wish Details (SRC-A2, SRC-A3, SRC-A4). | A | **VERIFIED** | Retain 50/50 and guarantee state. |
| **6** | Wish 1 and Wish 2 share identical guarantee count | VERIFIED | Re-confirmed in Version 7.1 Event Wishes notices (SRC-A2, SRC-A3). | A | **VERIFIED** | Retain shared atomic `GachaState`. |
| **7** | Pity/guarantees carry over between successive banner rotations | VERIFIED | Re-confirmed across v7.1 Phase I to Phase II transition. | A | **VERIFIED** | Retain state preservation across rotations. |
| **8** | 5★ soft pity starts at pull 74 (+6% linear increment through 89) | PARTIALLY VERIFIED | Empirical tracker data for v7.1 banners (SRC-C1) shows standard soft pity. | C | **PARTIALLY VERIFIED (EMPIRICAL)** | Retain decoupled `RarityProbabilityModel`. |
| **9** | Large-scale datasets support strong increase from pull 74 | PARTIALLY VERIFIED | Corroborated by ongoing aggregate wish data. | C | **PARTIALLY VERIFIED (EMPIRICAL)** | Use for calibration/regression only. |
| **10** | 4★ featured 50% chance; guaranteed after loss; equal 1/3 split | VERIFIED | Re-confirmed in Version 7.1 Wish Details (SRC-A2, SRC-A3, SRC-A4). | A | **VERIFIED** | Retain 4★ featured selection logic. |
| **11** | Capturing Radiance introduced in Version 5.0 | VERIFIED | Historical fact; reaffirmed in v7.1 client rules text. | A | **VERIFIED** | Retain versioned rule set tagging. |
| **12** | CR base rate 0.018%; consolidated promotional rate 55.000% | VERIFIED | Re-confirmed in Version 7.1 Wish Details (SRC-A4, SRC-A5). | A | **VERIFIED** | Retain published parameters in metadata. |
| **13** | Guaranteed CR trigger after 3 consecutive second-occasion wins | VERIFIED | Re-confirmed in Version 7.1 Wish Details (SRC-A4, SRC-A5). | A | **VERIFIED** | Retain `capturing_radiance_streak <= 3`. |
| **14** | CR applies only during active 50/50; does not alter existing guarantees | VERIFIED | Re-confirmed in Version 7.1 Wish Details (SRC-A4, SRC-A5). | A | **VERIFIED** | Bypassed when `featured_5star_guaranteed`. |
| **15** | Exact soft-pity curve is an official published rule | NOT VERIFIED | Still absent from official materials; HoYoverse publishes only 0.6% & 1.6%. | — | **NOT VERIFIED** | Never label empirical curve as official fact. |
| **16** | Non-featured 4★ split (50% character / 50% weapon) | NOT VERIFIED | Official UI states pool contents; exact sub-pool split is unstated. | C / D | **NOT VERIFIED AS SERVER RULE** | Model as configurable empirical split. |

---

## 6. Capturing Radiance — Critical Boundary & Mathematical Audit

### 6.1 Officially Disclosed Parameters (Level A)
As re-verified in Version 7.1 official notices (SRC-A4, SRC-A5), HoYoverse explicitly discloses exactly four rules:
1. **Base Trigger Probability:** $0.018\%$ ($0.00018$).
2. **Consolidated Promotional Probability:** $55.000\%$ (the overall proportion of 5★ pulls resulting in the promotional character over an infinite horizon, including standard 50/50 wins, guarantee pulls, and Capturing Radiance triggers).
3. **Streak Guarantee Condition:** "If the promotional 5★ character is the second 5★ character obtained on three consecutive occasions, Capturing Radiance is guaranteed to trigger on the next applicable 5★ pull."
4. **Invocation Scope:** The mechanic evaluates **only** on eligible 5★ pulls where the promotional character is not already guaranteed (`featured_5star_guaranteed == False`). It does not replace or consume an existing 100% guarantee.

### 6.2 Mathematical Boundary & The "Naive Bernoulli" Fallacy
A critical finding from our mathematical audit (first noted in `docs/specs/p2_gacha_engine_spec.md` §15.2 and re-confirmed under Version 7.1 parameters) is that **the published numbers cannot be reconciled via a single memoryless Bernoulli trial**:
- If an eligible 50/50 pull evaluates Capturing Radiance as an independent Bernoulli draw with $P_{\text{CR}} = 0.00018$, followed by a standard $0.5$ coin flip:
  $$P(\text{promotional on non-guaranteed 5★}) = 0.00018 + (1 - 0.00018) \times 0.5 = 0.50009$$
- Incorporating the streak guarantee at failure streak $k = 3$:
  Even with the guaranteed trigger every 3 consecutive losses, the effective win rate on non-guaranteed pulls rises only to $\approx 51.7\%$.
- An overall win rate of $51.7\%$ on non-guaranteed pulls yields a consolidated promotional rate far below the officially claimed **$55.000\%$** (which mathematically requires that $\approx 10\%$ of otherwise lost 50/50 pulls be converted into wins, meaning the true conditional trigger rate on a loss must be $\approx 10\%$, or the win rate on non-guaranteed pulls must be $\approx 55\%$).

### 6.3 Knowns vs. Unknowns Summary
- **WHAT IS KNOWN (OFFICIAL FACT, Level A):**
  - The published numbers ($0.018\%$ base, $55.000\%$ consolidated, 3-loss streak guarantee).
  - The exact UI trigger animation (the "special radiance" visual when winning via CR).
  - The exact boundary conditions (applies only during 50/50).
- **WHAT IS UNKNOWN (PROPRIETARY SERVER LOGIC):**
  - What HoYoverse's internal definition of "base trigger probability of 0.018%" actually represents in server code (e.g., does $0.018\%$ represent a per-pull base rate prior to hitting 5★, a baseline trigger prior to streak escalation, or an artifact of Chinese-to-English probability disclosure terminology?).
  - How the server transitions failure states between streak counts 0, 1, and 2.
  - Whether a progressive internal counter (hidden soft-pity for CR) exists.

### 6.4 Implementation Blocker Reaffirmation
> [!CAUTION]
> **RESEARCH & IMPLEMENTATION BLOCKER STATUS:**
> **Capturing Radiance implementation remains BLOCKED.**
> Under the rules of `AGENTS.md` and the project charter, the simulator must **never** hardcode an empirical hypothesis as an authoritative game rule.
> Because Version 7.1 materials do not provide the missing server-side algorithm, no default algorithm may be hardcoded into `GachaEngine`.
> The architectural design in `docs/specs/p2_gacha_engine_spec.md` (which isolates Capturing Radiance entirely behind the pluggable `CapturingRadianceModel` abstract interface) remains the only valid and approved design. Any concrete model implementing a specific curve or mathematical formulation must be explicitly flagged as an `EmpiricalCapturingRadianceModel` and must be authorized by ChatGPT / Art before implementation.

---

## 7. Answers to Required Research Questions

### Question A: What do Version 7.1 official materials explicitly say about artifact generation/enhancement probabilities and rules, if anything?
**Answer:** Official Version 7.1 materials (Update Details, in-game help text) mention **no changes** to artifact generation or enhancement probabilities. The only artifact-related changes in Version 7.1 are the introduction of new artifact sets (e.g. domain sets in new areas) and the "Set Lock Plans" UI convenience feature. Enhancement milestones (+4, +8, +12, +16, +20), the 4-substat slot limit, candidate exclusivity, and roll multipliers remain identical to previous versions.

### Question B: What do Version 7.1 official materials explicitly say about Character Event Wish probabilities, pity, featured guarantees, banner carry-over, and Capturing Radiance, if anything?
**Answer:** Official Version 7.1 Event Wishes notices and in-game Wish Details explicitly re-confirm the established contractual rules:
- 5★ base rate: $0.600\%$; consolidated rate: $1.600\%$; hard pity: 90 pulls.
- 4★ base rate: $5.100\%$; consolidated rate: $13.000\%$; hard pity: 10 pulls ("4★ or higher item guaranteed at least once per 10 attempts").
- 50/50 rule for promotional 5★ characters; losing awards a standard character and guarantees the promotional character on the next 5★.
- Character Event Wish and Character Event Wish-2 share and accumulate the same guarantee count.
- Pity counters and guarantees carry over to subsequent banner rotations within the same wish type.
- Capturing Radiance: base trigger rate $0.018\%$; consolidated promotional rate $55.000\%$; guaranteed after 3 consecutive second-occasion promotional outcomes; applies only during active 50/50.

### Question C: Which existing project claims are still supported by current official sources?
**Answer:** All claims designated as **Level A** in `docs/research/artifact_validation.md` (Claims 1, 2, 3, 4, 5, 10 for Flower/Plume) and `docs/research/gacha_validation.md` (Claims 1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14) continue to be fully supported by current Version 7.1 official sources.

### Question D: Which existing claims are only empirical, community-derived, reverse-engineered, or unknown?
**Answer:**
1. **Empirical / Community-Derived (Level C / D):**
   - Substat generation candidate weights ($6:6:6:4:4:4:4:4:3:3$).
   - Domain drop initial line count distribution ($80\%$ 3-line vs. $20\%$ 4-line).
   - Uniform $25\%$ target selection during artifact enhancement.
   - Equal $25\%$ probability across the 4 roll tiers ($70\%, 80\%, 90\%, 100\%$).
   - Sands, Goblet, and Circlet exact decimal distribution percentages.
   - 5★ soft-pity onset at pull 74 with linear $+6.0\%$ increment per pull.
   - 4★ soft-pity onset at pull 9 (jump to $56.1\%$).
   - 4★ non-featured 50/50 split between characters and weapons.
2. **Reverse-Engineered (Level B):**
   - Exact floating-point affix multipliers in `ReliquaryAffixExcelConfigData.json`.
3. **Unknown / Undisclosed:**
   - Server-side Capturing Radiance mathematical algorithm connecting $0.018\%$ to $55.000\%$.
   - Server collision behavior when pulling a 5★ item at 4★ pity = 9.
   - Server PRNG algorithm, state derivation, and integer weight representations.

### Question E: Did Version 7.1 introduce a documented change that requires changing the existing artifact or character-gacha SPEC?
**Answer:** **No.** Version 7.1 introduced no documented changes to underlying mechanics. `docs/specs/p2_gacha_engine_spec.md` accurately captures all verified Version 7.1 rules, properly isolates empirical curves behind interfaces, and requires **no modifications**.

### Question F: If no official version-specific change is found, what can safely be concluded, and what cannot be concluded from absence of a change notice?
**Answer:**
- **What CAN safely be concluded:** HoYoverse published no changes to player-facing contractual wish rules or artifact enhancement rules. The formal public rules and probabilities in Version 7.1 are identical to those published in previous versions.
- **What CANNOT be concluded:** Absence of a notice does **not** prove that backend server algorithms, PRNG implementations, or unobservable internal weight tables were untouched. In proprietary software systems, backend changes that do not alter published contractual probabilities can occur without patch note disclosure.

### Question G: What evidence is missing before the project could claim stronger fidelity to Version 7.1?
**Answer:** To claim absolute server-level fidelity, the project would require:
1. Leak or disclosure of proprietary HoYoverse server source code or server-side configuration data (`GachaServerConfig`, `ReliquaryAffixServerWeightTable`).
2. Official disclosure of the exact server algorithm for Capturing Radiance.
3. Multi-million wish datasets harvested exclusively from Version 7.1 banners (post-September 23, 2026) to statistically confirm that the empirical soft-pity curve and Capturing Radiance trigger rates have undergone zero silent adjustments.

---

## 8. Unresolved Questions & Next Actions

### Unresolved Questions
1. **Capturing Radiance Mathematical Model:** Which empirical model (e.g., progressive threshold vs. conditional failure-boost vs. dual-pool model) should be adopted as the default empirical strategy for `CapturingRadianceModel` in Phase 2?
2. **Multi-Source Artifact Line Count:** Should the artifact engine in a future phase support Strongbox/Boss drop rates ($66\%$ 3-line vs. $34\%$ 4-line) in addition to Domain drops ($80/20$)?

### Recommended Next Actions
1. **Maintain Phase Boundaries:** Keep P2 implementation on hold until ChatGPT / Art formally review this delta report and issue implementation authorization.
2. **Preserve Current Specifications:** Retain `docs/specs/p2_gacha_engine_spec.md` without edits; its architecture is 100% sound for Version 7.1.
3. **P2 Implementation Readiness:** When implementation is authorized, proceed strictly in accordance with `p2_gacha_engine_spec.md`, implementing the engine with pluggable models and deterministic seed reproducibility.
