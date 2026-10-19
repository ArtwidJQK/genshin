# ADR-001: Artifact Display Rounding Boundary

- **Status:** Accepted for presentation only
- **Date:** 2026-10-20
- **Context:** Artifact substat values previously rounded the internal sum to four decimal places in the domain model. SPEC_ARTIFACT.md section 3.4 requires internal values to retain precision and rounding to occur only at the display boundary.
- **Decision:** Keep the unrounded sum in Substat.value. Add a pure formatter that displays flat HP/ATK/DEF and Elemental Mastery as whole numbers, and all other recognized artifact properties to one decimal place with a percent sign. Use Decimal conversion from the input's string representation and ROUND_HALF_UP for display ties.
- **Alternatives considered:** Continue rounding in the domain model (rejected because it loses precision); use binary-float formatting (rejected because tie behavior is less explicit); preserve unrounded values without a shared formatter (rejected because consumers could diverge).
- **Consequences:** Internal enhancement data is not mutated by formatting. ROUND_HALF_UP is a display-layer engineering convention; it does not change RNG, rolls, probability, or stored state. If authoritative UI evidence establishes a different tie rule, update the formatter and its test vectors.
- **Evidence boundary:** Display precision is specified in docs/SPEC_ARTIFACT.md section 3.4. The tie-breaking rule is an engineering convention, not a claim about proprietary game internals.
