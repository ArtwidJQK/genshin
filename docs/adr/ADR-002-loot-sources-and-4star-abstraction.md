# ADR-002: Artifact Loot Sources Design, 4★ Fodder Abstraction, and Fidelity Policy

- **Status:** Under Final Review (Revised per Cross-Review Resolution)
- **Date:** 2026-10-20
- **Context:**
  Phase P3 of the project plan introduces artifact acquisition sources: **Domain of Blessing** (consuming 20 Original Resin or 1 Condensed Resin) and **Artifact Strongbox** (Mystic Offering 3-to-1 sacrifice). In the real game:
  1. Domains of Blessing drop 4★ artifacts in addition to 5★ artifacts. Official in-game text confirms 4★ items are in the pool, but does not state an exact guaranteed minimum number. Empirical player datasets indicate a baseline of 2 (with an unverified ~48% chance of a 3rd).
  2. Level 90 domains guarantee at least one 5★ artifact, but empirical community data indicates an unverified secondary drop chance of approximately $6.54\%$ (mean $\approx 1.065$ 5★ per 20 resin).
  3. Artifact Strongbox accepts 5★ artifacts and converts them at a 3:1 ratio into a selected set, with an empirical initial substat line count distribution of approximately $66\%$ 3-line vs $34\%$ 4-line (~2:1 ratio) rather than the domain $80/20$ ratio. This is an explicitly rounded approximate empirical model, not an official rule (F4).
  4. The existing configuration schema (`app/core/artifact/schema.py`) enforces strict provenance checking (`validate_config_provenance_fidelity`), raising errors if any constant in `provenance.json` has evidence below the active fidelity mode.
  5. `PROJECT_PLAN.md:180` specifies a $4\sigma$ frequency bound after $10^6$ runs, while `AGENTS.md:10.3` mandates pre-registered Chi-square goodness-of-fit testing ($\alpha = 0.001$).
  
  Architectural decisions were required to resolve: how to handle 4★ artifact drops without over-engineering; how to enforce strict mode consistently across catalog validation and runtime without silent bypasses (F1); how to validate inputs to the Strongbox; how to decouple the testing architecture (F5); how to execute Condensed Resin with sequential PRNG determinism (F6); and how to reconcile the statistical criteria with family-wise error rate control without requiring test independence (F5).

- **Decisions:**
  1. **4★ Fodder Abstraction (Option 1A) & Evidence Separation (F3):**
     - The domain result returns concrete 5★ `Artifact` instances and an integer counter `count_4star_fodder: int`.
     - Full 4★ artifact entities (with separate roll tables, main stat progression, 16-level caps, and substats) will **not** be constructed in Phase P3.
     - Rationale: In Genshin Impact, endgame artifact farming treats 4★ drops almost universally as enhancement fodder or mora conversions. Modeling full 4★ entity structures would roughly double domain complexity and memory overhead with zero value to 5★ RNG simulation.
     - Evidence Separation (F3):
       - Inclusion of 4★ artifacts in pool: `VERIFIED` (Level A).
       - Drop quantity distribution (2 to 3, mean ~2.48): `INFERRED` (Level C).
       - Fodder integer count representation: `ASSUMED` (Simulator Design Choice).
  2. **Two-Layer Strict Fidelity Policy & Refusal Invariant (F1):**
     - **Layer 1 (Configuration Catalog Checking):** `validate_config_provenance_fidelity(prov_path, mode=FidelityMode.STRICT)` will check `loot_sources.json`. Constants with evidence level `INFERRED` (such as `secondary_5star_probability = 0.0654`, `set_distribution_weights = 50/50`, `initial_line_count_weights = 80/20`, and `fodder_4star_baseline = 2`) will correctly be reported as fidelity violations in `STRICT` mode, exactly as `substats.CRIT_RATE` is reported today.
     - **Layer 2 (Runtime Execution Refusal Invariant):**
       - In `LootFidelityMode.STRICT`: Because complete artifact generation requires drawing a set (50/50), initial lines (80/20 or 66/34), and candidate substats (6/4/3) that are `INFERRED`, the engine **MUST NOT silently substitute or default unverified numbers**. If invoked in `STRICT` mode against production configurations, `run_domain_of_blessing` and `craft_strongbox` **refuse execution and raise `FidelityViolationError`**.
       - Availability: Strict execution is unavailable in the standard engine until a verified-only configuration baseline is formally supplied.
       - Entity Internals (F1): Even if a verified drop quantity rule is supplied, **artifact entity internals remain INFERRED**. The overall result payload must **NEVER be described as fully VERIFIED**; its `weakest_evidence_level` must honestly reflect the weakest constituent parameter (`INFERRED`). This labeling rule eliminates any contradiction between a verified drop quantity and unverified entity internals, ensuring strict fidelity mode integrity.
       - In `LootFidelityMode.BEST_EFFORT` (Default Operational Mode): The engine executes empirical community models ($p = 0.0654$ for 2nd 5★, 80/20 and 66/34 initial lines, 4★ fodder 2-3) and reports `weakest_evidence_level = "INFERRED"`.
       - In `LootFidelityMode.EXPERIMENTAL`: Allows research overrides; reports `weakest_evidence_level = "EXPERIMENTAL"` or `"ASSUMED"`.
       - Rationale: Eliminates any silent bypass and satisfies `AGENTS.md Section 5.2`: *"A rule whose evidence is below the active mode must be refused with a clear error, not silently defaulted."*
  3. **Strongbox Input Validation (Option 3A):**
     - The `craft_strongbox` function accepts `sacrifice_artifacts: List[Artifact]`.
     - The domain engine strictly validates in order:
       1. `isinstance(sacrifice_artifacts, list)`
       2. `len(sacrifice_artifacts) >= 3`
       3. `len(sacrifice_artifacts) % 3 == 0`
       4. `all(artifact.rarity == 5 for artifact in sacrifice_artifacts)`
       5. `target_set` is valid and non-empty.
       6. `fidelity_mode != STRICT` (raises `FidelityViolationError`).
     - Invalid inputs raise domain `ValueError` or `TypeError` exceptions immediately, ensuring no partial consumption or invalid entity states occur.
  4. **Condensed Resin Equivalence & Single-PRNG Stream Policy (F6):**
     - 1 Condensed Resin (40 Original Resin equivalent) executes two consecutive, independent 20-resin domain drop passes (`cycle_index = 0` and `cycle_index = 1`) using **one continuous injected PRNG stream** (never re-seeded or cloned between cycles).
     - Result aggregation: `artifacts = cycle_0.artifacts + cycle_1.artifacts`, `count_4star_fodder = cycle_0.fodder + cycle_1.fodder`, `resin_spent = 40`, `runs_executed = 2`, `audit_events = cycle_0.audit_events + cycle_1.audit_events`.
     - Epistemological Boundary: Single-stream advancement is a simulator design decision (`ASSUMED`) guaranteeing determinism; it does not claim to prove server-internal RNG dispatch.
  5. **Dual-Gate Pre-Registered Statistical Acceptance Criteria (F5):**
     - Statistical verification requires satisfying **two independent, co-equal, mandatory acceptance gates** ($\text{PASS} = \text{Gate}_1 \land \text{Gate}_2$):
       - **Gate 1 (Chi-Square Goodness-of-Fit with Bonferroni Correction):** Evaluates multi-bin categorical distributions across $M = 3$ hypothesis tests (5 slots $df = 4$, set split $df = 1$, initial lines $df = 1$) with $\alpha_{\text{adj}} = \frac{0.001}{3} \approx 0.000333$. Controls FWER by Boole's inequality without requiring independence between tests.
       - **Gate 2 ($4\sigma$ Local Binomial Boundary Gate):** Enforces strict univariate frequency bounds $|\hat{p} - p| \le 4\sqrt{p(1-p)/N}$ across 4 scalar metrics (Set 50/50, Domain 4-line, Strongbox 4-line, Secondary 5★).
       - Pre-registered Fast Suite ($N = 100,000$, `seed = 20261020`) and Heavy Suite ($N = 1,000,000$, `seed = 20261021`). Both gates must pass simultaneously.
  6. **Three-Layer Decoupled Testing Architecture (F5):**
     - Layer 1 (`test_loot_determinism.py`): Bit-for-bit replay from seed, PRNG stream isolation, state save/restore replay, multi-seed divergence.
     - Layer 2 (`test_loot_invariants.py`): Strongbox 3:1 validation, Condensed Resin 2x rewards, strict mode refusal, 4★ fodder integer invariants.
     - Layer 3 (`test_loot_statistical.py`): Dual-gate Chi-square and $4\sigma$ distribution tests across $N = 100,000$ and $N = 1,000,000$.
     - Rationale: Decouples statistical convergence from deterministic correctness; a single seed test cannot serve as sole proof of RNG correctness.
  7. **Phase Scope Boundaries (F2):**
     - Configuration files (`loot_sources.json`) and provenance modifications are specified in P3.1 as requirements, but are **P3.2 deliverables**. Zero configuration files are modified in P3.1.

- **Alternatives Considered:**
  - *Full 4★ Artifact Domain Model:* Rejected because it introduces excessive code bloat without adding any value to 5★ endgame simulation.
  - *Silently applying 6.5% secondary drop in strict mode:* Rejected because `AGENTS.md` Section 5 explicitly prohibits using `INFERRED` rules in `strict` mode.
  - *Executing strict drop quantity (1 5★) while silently using inferred substat weights:* Rejected per Project Lead review. Bypasses catalog validation and creates an epistemological contradiction. Strict mode must refuse execution when required configuration constants are unverified.
  - *Accepting raw integer count for Strongbox sacrifices:* Rejected because passing actual `Artifact` instances allows validation of rarity, ensures future integration with inventory state management, and enforces atomic consumption semantics.
  - *Re-seeding RNG for Condensed Resin second cycle:* Rejected because re-seeding with the same seed causes duplicate identical drops; single sequential PRNG stream advancement accurately models consecutive independent trials.

- **Consequences:**
  - The domain model remains pure, deterministic, and lightweight.
  - Strict mode provides unassailable integrity by refusing unverified server internals.
  - Best-effort mode provides realistic farming economics for theorycrafters, honestly labeled as `INFERRED`.
  - All output entities carry an audit trail of stochastic decisions.

- **Evidence Boundary & Exact Provenance:**
  - 1 guaranteed 5★ per Level 90 domain: `VERIFIED` (Level A, In-Game Client UI / Level 90 Domain Description).
  - 3:1 Strongbox sacrifice ratio, 5★ requirement, and multiple of 3: `VERIFIED` (Level A, In-Game Mystic Offering UI).
  - 2x reward for Condensed Resin: `VERIFIED` (Level A, In-Game Help Menu: *Condensed Resin*).
  - 6.54% secondary 5★ drop rate: `INFERRED` (Level C, Genshin Data Gathering Team Sheet: *Artifact Drop Rates*, Tab: *Artifact Quantity*, $N = 48,932$, observed $6.54\% \pm 0.22\%$).
  - 4★ fodder baseline (2) and bonus rate (48%): `INFERRED` (Level C, Genshin Data Gathering Team Sheet: *Artifact Drop Rates*, Tab: *Artifact Quantity*). Reclassified from VERIFIED.
  - 80/20 initial line count for Domains: `INFERRED` (Level C, Genshin Data Gathering Team Sheet: *Artifact Quality & Affixes*, Tab: *Artifact Quality (Domains)*, $N = 34,228$, observed $79.9\% : 20.1\%$).
  - 66/34 initial line count for Strongbox: `INFERRED` (Level C, NGA TID: 33220261 / Genshin Data Gathering Team Sheet: *Strongbox Quality*, $N = 15,280$, observed $65.8\% : 34.2\%$). Rounded empirical parameter; not an official rule (F4).
  - 50/50 domain set distribution: `INFERRED` (Level C, Genshin Data Gathering Team Sheet: *Artifact Drop Rates*, Tab: *Domain Rewards*, $N > 100,000$, observed $49.98\% : 50.02\%$).
  - Uniform 20% slot distribution: `INFERRED` (Level C, Genshin Data Gathering Team Sheet: *Artifact Drop Rates*, Tab: *Slot Distribution*, $N > 100,000$, observed $20.0\% \pm 0.2\%$).
  - 4★ Fodder counter abstraction: `ASSUMED` (Simulator Design Choice).

- **Open Decisions for Project Lead Final Approval:**
  - Decision Point 1: Confirmation of the Strict Fidelity Refusal Invariant (`FidelityViolationError` when required parameters are `INFERRED`) (F1).
  - Decision Point 2: Confirmation of P3.2 deliverable boundaries for `loot_sources.json` and `provenance.json` (F2).
  - Decision Point 3: Confirmation of 4★ fodder reclassification to `INFERRED` (F3).
  - Decision Point 4: Confirmation of Strongbox initial line integer representation `{"3": 66, "4": 34}` in config labeled `INFERRED` as an approximate model (F4).
  - Decision Point 5: Confirmation of Dual-Gate statistical criteria ($\text{Gate}_1 \land \text{Gate}_2$) with Bonferroni union bound (F5).
  - Decision Point 6: Confirmation of Sequential Single-PRNG Stream Policy for Condensed Resin (F6).
  - Standing Blockers: Capturing Radiance (`OQ-01`) and Reshaping / Hallowed Exegesis (`OQ-03`) remain strictly `BLOCKED`.
