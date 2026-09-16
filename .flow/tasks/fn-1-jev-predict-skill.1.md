---
satisfies: [R1, R2, R3, R4, R5, R6, R7, R8, R9, R10]
---
# fn-1-jev-predict-skill.1 Implement Jev-predict skill

## Description
TBD

## Acceptance
Every R-ID in the parent spec's ## Acceptance Criteria is satisfied; judge this task against the spec's criteria directly.

## Done summary
Shipped `/jev-predict-skill` as a host SKILL.md. It resolves any argument skill, asks Jev whether a closed breakdown exists, extracts the next decision labels from that skill, and reports a Choice. Eligibility is match plus breakdown. There is no skip gate and no automatic execute. Host impl-review SHIP on 5856c4a.
## Evidence
- Commits: 2ba615ff0b580ad0a6afe3eee3be2f54c2f88552, 5856c4a4099d6e950db614074e0521a0bb4645b3
- Tests: host impl-review SHIP (round 3, 5856c4a)
- PRs:
