# Open Questions & Unresolved Mechanics

This document tracks all unresolved mechanics, conflicting community evidence, and open design decisions for the Genshin Simulator, adhering strictly to **AGENTS.md Section 2.3 & 6.2** and **docs/PROJECT_PLAN.md Section 2 & 5.1.1**.

---

## 1. Governance Rules for Unresolved Mechanics

1. **Separation of Defaults:**
   - **Technical Defaults** (e.g., internal data representations, interface boundaries, file layouts) may be chosen by the engineering team, recorded in an Architecture Decision Record (ADR), and implemented.
   - **Mechanics-Affecting Defaults** (e.g., probabilities, state machines, pity reset rules, rounding formulas) **must never** silently become default product behavior.
2. **Strategy Isolation:**
   - Any unresolved mechanic must either be isolated behind an explicitly named strategy interface at evidence level `ASSUMED` or `EXPERIMENTAL` (disabled by default in the main `strict` fidelity mode), OR execution of the dependent module must stop until Product Owner (Art) and ChatGPT approve a resolution.
3. **No Fabricated Numbers:**
   - No constant may be assigned without an auditable provenance record and evidence classification.

---

## 2. Catalog of Open Questions

### OQ-01: Capturing Radiance Exact Server Algorithm
* **Status:** **BLOCKED FROM DEFAULT ENGINE** (Strategy Isolation Required).
* **Game Version:** Genshin Impact 5.0+ (reaffirmed 7.1).
* **Published Official Evidence (Level A):**
  - Base trigger rate: $0.018\%$ per pull.
  - Consolidated promotional character rate: $55.000\%$.
  - 3-consecutive-loss guarantee (if a player fails 50/50 three times in a row without a promotional character on the standard pool occasion, the next is guaranteed).
* **The Conflict / Gap:**
  - HoYoverse disclosed the aggregate macro outcomes and guarantee threshold, but **not** the internal Markov transition kernel or state machine.
  - A static Bernoulli trial on 50/50 loss yielding $0.018$ or a flat conditional probability does not yield $55.0\%$ consolidated rate when combined with 90-pull pity and guarantee states; it yields $\approx 51.7\%$.
  - Multiple community Markov chains reproduce an aggregate $55\%$, but each posits different conditional probabilities (e.g., 10% rescue upon 50/50 loss vs. progressive accumulation).
* **Simulator Action:**
  - Core Gacha Engine defines the abstract interface `CapturingRadianceModel` (`docs/specs/p2_gacha_engine_spec.md`).
  - Community models are implemented under `app/core/gacha/strategies/` labeled `EXPERIMENTAL`, disabled by default in `strict` fidelity mode.
  - Test suites assert that the engine refuses to run unverified models in `strict` mode.

---

### OQ-02: Soft Pity Curve for Character Event Wish
* **Status:** **EMPIRICALLY INFERRED (Level C)**.
* **Game Version:** All versions (1.0 through 7.1).
* **Published Official Evidence (Level A):**
  - Base rate: $0.600\%$.
  - Consolidated rate: $1.600\%$.
  - Hard pity: 90 pulls.
* **The Conflict / Gap:**
  - HoYoverse does not publicly document the onset pull or exact step function of soft pity.
  - Aggregate crowdsourced datasets (Paimon.moe, millions of pulls) indicate soft pity begins at **pull 74**, increasing linearly by approximately $+6.0\%$ per pull ($P(n) = 0.006 + 0.06 \times (n - 73)$ for $74 \le n \le 89$), reaching $100\%$ at pull 90.
* **Simulator Action:**
  - Pluggable `RarityProbabilityModel` interface.
  - `StandardEmpiricalPityModel` provides the community $+6\%$/pull curve, labeled `INFERRED` (allowed in `best_effort` mode).
  - `ConstantRateHardPityModel` provides the strict baseline (0.6% flat until 90), labeled `VERIFIED`.

---

### OQ-03: Hallowed Exegesis Threshold Milestones (Reshaping)
* **Status:** **BLOCKED** (Do not implement Reshaping until resolved).
* **Game Version:** Genshin Impact 5.7+ (reaffirmed 7.1).
* **The Conflict / Gap:**
  - Artifact Reshaping uses *Dust of Enlightenment* to redistribute substat upgrade rolls on a +20 5★ artifact with 2 chosen prioritized substats.
  - Consecutive non-optimal reshapes accumulate *Hallowed Exegesis* points to guarantee 3 or 4 rolls into prioritized substats.
  - **Source Conflict:**
    - Some community theorycrafting guides state the guarantee milestones occur at **6, 12, and 18** accumulated points.
    - Other sources cite milestones at **12 and 16** accumulated points.
    - In addition, empirical reports conflict on whether the guaranteed rolls can both land on the *same* prioritized substat or must distribute across both.
* **Simulator Action:**
  - Per `docs/PROJECT_PLAN.md` Section 4.5 & 6.1 (Step 3): **Do not implement Reshaping or Hallowed Exegesis while sources conflict.**
  - Requires extraction and verification of official in-game tutorial text before Phase P4.

---

### OQ-04: Multi-Source Artifact Line Count Distribution
* **Status:** **ISOLATED TO DOMAIN DROPS**.
* **Game Version:** All versions (1.0 through 7.1).
* **The Conflict / Gap:**
  - Current configuration (`config/artifacts/rules.json`) models Domain of Blessing drops: $80\%$ 3-line vs $20\%$ 4-line.
  - Crowdsourced data shows that Artifact Strongbox, World Bosses, and Abyss Reliquaries exhibit an initial distribution of approximately $66\%$ 3-line vs $34\%$ 4-line.
* **Simulator Action:**
  - Retain $80/20$ for domain drops in P1 and P2.
  - Add source-specific configuration in Phase P3 (Loot Sources: Domain vs Strongbox).

---

### OQ-05: Artifact Transmuter Elixir Cost Formula
* **Status:** **PENDING PHASE P4**.
* **Game Version:** Genshin Impact 5.0+ (reaffirmed 7.1).
* **The Conflict / Gap:**
  - Creating a custom artifact via Artifact Transmuter requires *Sanctifying Elixir*.
  - Cost varies by artifact slot (Flower/Plume: 1 Elixir; Sands: 2 Elixirs; Goblet: 4 Elixirs; Circlet: 3 Elixirs).
  - The exact guarantee mechanism (guaranteeing 2 initial chosen substats and minimum 2 upgrade rolls) needs exact verification against in-game help text.
* **Simulator Action:**
  - Scheduled for Phase P4; research in-game tutorial text prior to implementation.

---

### OQ-06: 4★ Soft Pity Curve & Weapon/Character Pool Split
* **Status:** **INFERRED (Level C)**.
* **Game Version:** All versions (1.0 through 7.1).
* **Published Official Evidence (Level A):**
  - Base rate: $5.100\%$.
  - Consolidated rate: $13.000\%$.
  - 10-pull guarantee.
* **The Conflict / Gap:**
  - Crowdsourced data shows 4★ soft pity begins at pull 9 (increasing to ~56% at pull 9 and 100% at pull 10).
  - The non-guaranteed split between 4★ weapons and 4★ standard characters in Character Event Wish requires exact pool weights.
* **Simulator Action:**
  - Modeled in `docs/specs/p2_gacha_engine_spec.md` with explicit `FourStarOutcomeModel`.
