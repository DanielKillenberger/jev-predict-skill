---
name: jev-predict-skill
description: >
  Predict a skill's next closed decision outcome with TypeSafe Jev without
  running that skill. Use when asked to jev-predict a skill, forecast what
  /flow or /flow-next-flow would do next, or select among a skill's
  predetermined outcomes from current context.
disable-model-invocation: true
---

# /jev-predict-skill

Takes **any skill as an argument**. First asks TypeSafe Jev how confident it
is that a closed breakdown can be made. Only then extracts a closed outcome
set and Jev-selects over those outcomes plus context plus the skill body.
`/flow` and `/flow-next-flow` are examples, not the only targets.

**Never execute, dispatch, or implement the argument skill.** The result is a
prediction. Do not run `/flow-next:flow` or any other conductor hop to obtain
it.

Keep `TYPESAFE_API_KEY` in the environment. Do not write it into this file,
the report, or commit it.

## Arguments

The argument is the skill to predict. Resolve it in this order (the Python
module implements the same rule):

1. Missing or blank → report that no skill was given; produce no prediction.
2. Filesystem path to a skill file or a directory containing `SKILL.md`.
3. Slash name or skill name (`/flow-next-flow`, `flow-next:flow`, `/flow`).
4. Pasted skill body that has YAML frontmatter with `name:`.
5. Anything else → report that the argument cannot be read as a skill; produce
   no prediction.

## Procedure

From this repository root:

```bash
PYTHONPATH=src python3 -m jev_predict_skill --context "<current context>" --json -- "<skill argument>"
```

1. Gather **read-only** context for Jev `state` (session request, `flowctl
   show --json` / `list --json` / `ready --json` when the argument is a
   flow-next skill). That is observation, not running the conductor.
2. Run the command above. Do not invoke the argument skill as a Cursor
   `/skill` or subprocess.
3. Report the module output as-is.

## Result contract

- `status: predicted` — print the discrete `outcome` and the closed
  `outcomes` list. For `/flow-next-flow` the outcome is the conductor phase
  (route-matrix stage), not a hop loop.
- `status: not_predictable` — Jev was not confident a breakdown can be made,
  or host extraction found no closed set. Report that. Do not invent a
  structured prediction or a conductor phase.
- `status: error` — missing argument, unreadable skill, assessment failure,
  or Jev selection failure. Report the `message`. Produce no prediction.

The Python module is the source of truth for thresholds, Jev questions, and
error kinds. Do not re-implement the judgments in prose.
