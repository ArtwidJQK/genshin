\---

name: genshin-research

description: Research and validate Genshin game mechanics with explicit evidence provenance. Use when investigating artifact mechanics, character gacha mechanics, RNG behavior, player-discovered mechanics, or conflicting sources. Never turn assumptions into verified facts.

\---



\# Genshin Research



\## Mission



Maintain a defensible evidence base for the Genshin simulator.



The goal is NOT to prove that every mechanic is exactly identical to the original game's hidden implementation.



The goal is to distinguish:



\- verified mechanics

\- strong inferences

\- simulation assumptions

\- unknown mechanics



\---



\## Evidence Classification



\### VERIFIED



Use only when directly supported by authoritative evidence or sufficiently strong primary evidence.



\### INFERRED



Use when multiple independent observations strongly support the mechanic but the internal implementation is not directly known.



\### ASSUMED



Use when the simulator requires a concrete implementation but evidence is insufficient.



\### UNKNOWN



Use when available evidence is insufficient to determine the mechanic.



\---



\## Research Rules



1\. Never fabricate undocumented mechanics.

2\. Never present player speculation as official behavior.

3\. Preserve source provenance.

4\. Record conflicting evidence.

5\. Record research date.

6\. Separate observed behavior from implementation hypothesis.

7\. If exact internal RNG implementation is unknown, explicitly say so.

8\. Prefer reproducible evidence over anecdotal claims.



\---



\## Claim Format



Every important mechanic should be representable as:



```text

CLAIM:

<mechanic>



STATUS:

VERIFIED | INFERRED | ASSUMED | UNKNOWN



EVIDENCE:

<source / experiment / observation>



CONFIDENCE:

HIGH | MEDIUM | LOW



CONFLICTS:

<conflicting evidence, if any>



IMPLEMENTATION IMPACT:

<what the simulator should do>



NOTES:

<uncertainty or limitations>
