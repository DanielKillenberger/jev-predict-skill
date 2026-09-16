---
satisfies: [R1, R2, R3, R4]
---
# fn-2-public-readme-for-jev-predict-skill.1 Write public README.md

## Description
TBD

## Acceptance
- [ ] TBD

## Done summary
Added a public `README.md` at the repo root for jev-predict-skill. It states
the one-liner (predict another skill's next closed decision via TypeSafe Jev
without running that skill), explains why (Jev = typed System One Choice/Score/
Noul with probabilities, not text generation), when to use it (closed-decision
skills, not open-ended generation), install (`TYPESAFE_API_KEY`, `SKILL.md`
location, no build), a quick example with a prediction report and a fail-closed
stop, the numbered flow (resolve → gather → noul breakdown ≥0.65 → extract labels
+ none_of_the_above → choice), limits, and links. Accurate to the current
SKILL.md; no secrets or example tokens, no invented API fields, SKILL.md not
pasted in. Documentation only — the skill is unchanged.
## Evidence
- Commits: 3d342f592a3f3cce25637c7b6a780b93ab890f38
- Tests:
- PRs: