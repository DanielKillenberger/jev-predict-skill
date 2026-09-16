# Public README for jev-predict-skill

## Goal & Context

The repo ships `jev-predict-skill` (a host `SKILL.md`) but has no public entry
point for someone landing on GitHub. Add a root `README.md` that explains what
the skill does, when to reach for it, how to install it, and how it works —
accurate to the current `SKILL.md` behavior, in a terse developer voice.

## Acceptance Criteria

- **R1:** `README.md` exists at the repo root and describes the skill accurately
  against the current `SKILL.md`: predicts another skill's next closed decision
  via TypeSafe Jev (`jev-latest`, `POST https://api.typesafe.ai/v1/systemone`),
  without running the target skill.
- **R2:** Covers what it does, why (Jev = typed System One decisions, not text
  generation), when to use it (closed-decision skills; not open-ended
  generation), install (`TYPESAFE_API_KEY`, where `SKILL.md` lives), a quick
  example, the numbered flow, and its fail-closed limits.
- **R3:** No secrets, no example bearer tokens, no invented API fields, and the
  full `SKILL.md` is not pasted in. Links to TypeSafe and its docs where useful.
- **R4:** No changes to the skill itself or unrelated files.

## Boundaries

- Documentation only. Does not reimplement or modify the skill.
