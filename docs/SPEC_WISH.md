# SPEC_WISH — Character Event Wish Specification

**Document Version:** 1.0.0  
**Target Game Version:** Genshin Impact 7.1 (Reaffirmed)  
**Status:** ACTIVE (SPEC complete; implementation blocked on Capturing Radiance model approval)  
**Primary Detailed Reference:** `docs/specs/p2_gacha_engine_spec.md`  
**Roadmap Alignment:** `docs/PROJECT_PLAN.md` Section 5 & `docs/research/gacha_validation.md`

---

## 1. Scope & Banner Types

This specification formalizes the rules, pity mechanics, guarantees, probability distributions, and state tracking for the Character Event Wish gacha engine:

* **Primary Limited Character Banner:** Character Event Wish (Banner 1).
* **Secondary Limited Character Banner:** Character Event Wish-2 (Banner 2).
* **Shared State:** Pity counters (`pity_5star`, `pity_4star`) and guarantee flags are shared atomically across Banner 1 and Banner 2, and carried over across banner rotations (`VERIFIED`, Official in-game rule).
* **Isolation:** Standard Wish (Wanderlust Invocation) and Weapon Event Wish operate on separate, independent state trackers.

---

## 2. 5★ Character Pull Rules

### 2.1 Probabilities & Hard Pity
* **Base Probability:** $0.600\%$ ($P = 0.006$) per single pull (`VERIFIED`, Level A official rule).
* **Consolidated Probability:** $1.600\%$ ($P = 0.016$) including pity (`VERIFIED`, Level A official notice).
* **Hard Pity:** Guaranteed 5★ outcome on or before pull 90 (`VERIFIED`, Level A official rule). Counter resets to $0$ upon receiving any 5★ character.

### 2.2 Soft Pity Curve
* **Evidence Level:** `INFERRED` (Level C, Crowdsourced empirical data).
* **Model:** Soft pity onset occurs at **pull 74**, increasing linearly by approximately $+6.0\%$ per pull ($P(n) = 0.006 + 0.06 \times (n - 73)$) until reaching $100\%$ at pull 90.
* **Architecture:** Decoupled behind `RarityProbabilityModel` interface (`StandardEmpiricalPityModel` vs `ConstantRateHardPityModel`).

### 2.3 50/50 Guarantee System
* **First 5★ Drop:** $50\%$ chance to be the on-banner promotional character; $50\%$ chance to be a standard 5★ character (`VERIFIED`, Level A official rule).
* **Post-Loss Guarantee:** If the 5★ character is not the promotional character, the **next 5★ character is guaranteed 100%** to be the promotional character (`VERIFIED`, Level A official rule).
* **Reset:** Obtaining the promotional character resets the guarantee flag to non-guaranteed (`VERIFIED`).

### 2.4 Capturing Radiance (Version 5.0+)
* **Evidence Classification:**
  - Official Parameters: Base trigger rate $0.018\%$; Consolidated promotional rate $55.000\%$; 3-loss guarantee (`VERIFIED`, Level A).
  - Internal Algorithm: Proprietary server logic undisclosed (`UNKNOWN`, Level E / Empirical Hypothesis).
* **Status:** **BLOCKED FROM PRODUCTION DEFAULT MODE**.
* **Engine Policy:** Pluggable `CapturingRadianceModel` interface. Empirical models are placed behind `EXPERIMENTAL` strategy flags and disabled by default in `strict` fidelity mode (`AGENTS.md` Section 6.3).

---

## 3. 4★ Pull Rules

### 3.1 Probabilities & Hard Pity
* **Base Probability:** $5.100\%$ ($P = 0.051$) (`VERIFIED`, Level A official rule).
* **Consolidated Probability:** $13.000\%$ ($P = 0.130$) including pity (`VERIFIED`, Level A official notice).
* **Hard Pity:** Guaranteed 4★ outcome on or before pull 10 (`VERIFIED`, Level A official rule).

### 3.2 4★ State Independence & Guarantees
* **Independent 4★ Counter:** Pulling a 5★ character **does not** reset `pity_4star` (`VERIFIED`, Official in-game rule).
* **Featured Split:** 50% chance of a featured 4★ promotional character; 50% chance of a standard 4★ character or weapon (`VERIFIED`, Level A).
* **Post-Loss 4★ Guarantee:** If a 4★ pull yields a non-featured outcome, the next 4★ pull is guaranteed to be a featured 4★ character (`VERIFIED`, Level A).
* **Uniform Featured Distribution:** When a featured 4★ is awarded, it is drawn uniformly ($\frac{1}{3} \approx 33.33\%$) among the 3 rate-up 4★ characters (`VERIFIED`, Level A).

---

## 4. State Representation & Pure Function Contract

The gacha engine operates as a deterministic, pure state machine:
$$\text{pull}(S, C, R) \to (S', \text{result}, \text{events})$$
* **$S$ (`GachaState`):** `pity_5star`, `pity_4star`, `guaranteed_featured_5`, `guaranteed_featured_4`, `radiance_streak_counter`.
* **$C$ (`BannerConfig`):** Rates, pools, pity caps, and model strategies.
* **$R$ (`RNGInterface`):** Seed-isolated pseudo-random number generator (`PythonRNG`).
* **Audit Trail:** Every pull emits a structured `PullEvent` containing state before, state after, roll outcome, and flags.
