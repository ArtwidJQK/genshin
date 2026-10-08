\---

name: genshin-adversarial-audit

description: Adversarially audit Genshin simulator implementations by attempting to falsify mechanics, RNG behavior, state transitions, statistical assumptions, research claims, and test validity. Use before declaring substantial mechanics or systems complete.

\---



\# Genshin Adversarial Audit



\## Mission



Try to prove that the simulator is wrong.



Do not optimize for confirming the implementation.



Actively search for:



\- incorrect mechanics

\- hidden assumptions

\- RNG bias

\- state leakage

\- boundary errors

\- invalid statistical conclusions

\- weak tests

\- research contradictions

\- implementation/test coupling



The default mindset is:



> "What evidence would prove this implementation incorrect?"



\---



\# 1. Audit Scope



Determine which layers are affected:



\- Research

\- Specification

\- Architecture

\- RNG

\- Core mechanics

\- State management

\- Statistical behavior

\- Tests

\- Documentation



Do not audit unrelated systems unnecessarily.



\---



\# 2. Research Audit



Check every important mechanic for provenance.



For each claim ask:



1\. Is the source authoritative?

2\. Is the source current?

3\. Is the claim directly observed?

4\. Is it inferred?

5\. Is it merely assumed?

6\. Are conflicting sources documented?

7\. Did implementation treat an assumption as fact?



Flag:



```text

UNSUPPORTED\_CLAIM

CONFLICTING\_EVIDENCE

ASSUMPTION\_PRESENTED\_AS\_FACT

STALE\_EVIDENCE
