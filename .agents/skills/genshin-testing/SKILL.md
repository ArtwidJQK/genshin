\---

name: genshin-testing

description: Validate Genshin simulator mechanics through deterministic tests, invariant checks, statistical validation, RNG reproducibility, boundary testing, and regression testing. Use when validating artifact rolls, gacha probability, pity systems, state transitions, or RNG behavior.

\---



\# Genshin Testing



\## Mission



Prove that the simulator implementation behaves according to its documented specification.



Testing must distinguish:



\- implementation correctness

\- statistical correctness

\- reproducibility

\- mechanic correctness



A passing unit test alone does not prove the simulator is correct.



\---



\## 1. Deterministic Testing



Whenever the simulator supports explicit seeds:



\- identical seed + identical inputs must produce identical outputs

\- different seeds should be allowed to produce different outputs

\- RNG state must not leak between independent simulations

\- test cases must record the seed when reproducibility matters



Required invariant:



```text

same seed

\+

same initial state

\+

same inputs

=

same result
