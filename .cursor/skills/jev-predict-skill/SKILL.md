---
name: jev-predict-skill
description: >
  Predict another skill's next closed decision with TypeSafe Jev. Use when
  asked to jev-predict a skill or invoked as /jev-predict-skill. Returns
  without a prediction if the argument is not a skill, cannot be broken
  into decisions Jev can select, assessment or selection fails, or Jev
  picks none_of_the_above.
---

# /jev-predict-skill

Takes **any skill as an argument**. The user asked for a Jev prediction.
Do not ask whether predict is better than running the skill, and do not
require high confidence before answering. Run the skill only if they ask.

Stop without a prediction when:

1. The argument is not a skill (missing, unreadable, not a match).
2. The skill cannot be broken into closed decisions Jev can select.
3. Assessment fails (missing key, HTTP after retries, parse, missing noul).
4. Selection fails (HTTP after retries, parse, missing or incomplete Choice).
5. Jev picks `none_of_the_above` (no matching outcome; do not invent a label).

Otherwise extract the next closed decision and have Jev pick.

Keep `TYPESAFE_API_KEY` in the environment. Do not write it into this file,
the report, or a commit.

## Constants

Review these in this file. Do not invent different questions or thresholds
mid-run.

- **Breakdown question** (`type: noul`, id `can_break_down`):
  - instructions: `Can this skill be broken into a predetermined, closed set of decision outcomes that Jev can select among?`
  - criteria.true: `The skill makes one or more finite named decisions a Choice can cover without inventing labels.`
  - criteria.false: `Outcomes are open-ended generation, undecomposable work with no closed labels, or not a match for Jev.`
- **Breakdown noul:** ≥ `0.65` means extract and predict. Below that, report that it cannot be broken down. Produce no prediction.
- **Selection question** (`type: choice`, id `outcome`):
  - instructions: `Which closed decision outcome would running this skill produce right now? Pick only from the provided options. Do not invent a new outcome.`
  - Always include option `none_of_the_above`.
- **Jev:** `POST https://api.typesafe.ai/v1/systemone` with `model: "jev-latest"`.
- **HTTP:** Capture `%{http_code}`. Retry `429` and `529` up to twice with 1s then 2s backoff. Report `401` as auth failure, `422` as validation failure, other remaining errors as transient or hard failure. `curl -sS` alone is not a failure signal.

## 1. Resolve the argument

First match wins:

1. Missing or blank → report that no skill was given; stop.
2. Filesystem path to a skill file, or a directory containing `SKILL.md` → read it.
3. Slash name or skill name → find `SKILL.md` under these roots, in order. Try the name as given and the same name with `/`, `:`, and `-` swapped (example: `/flow-next:impl-review`, `flow-next-impl-review`, `flow-next/impl-review`).
   - `$JEV_PREDICT_SKILL_PATH` if set (file or directory)
   - `<repo>/.cursor/skills/<name>/SKILL.md`
   - `~/.cursor/skills/<name>/SKILL.md`
   - `~/.codex/skills/<name>/SKILL.md`
   - `~/.claude/skills/<name>/SKILL.md`
   - `~/.cursor/plugins/local/**/skills/<name>/SKILL.md`
   - `~/.cursor/plugins/cache/**/skills/<name>/SKILL.md`
   - `~/.claude/plugins/**/skills/<name>/SKILL.md`
4. Pasted body that starts with YAML frontmatter containing `name:` → use it as the skill.
5. Anything else → report that the argument is not a match for a skill; stop.

Read the skill and any files it points at that define its decisions.

## 2. Gather what those decisions need

Infer from the skill text what facts determine its **next** closed decision.
Gather that **read-only** and keep it small: the decision-relevant evidence
(the change, the contract, status that would change the pick). Do not dump
unrelated skill manuals. Do not run the argument skill.

Jev `state` (all of these, JSON-encoded; never pasted into a shell quote):

- `skill`: argument skill frontmatter plus the decision-relevant body. If
  truncated to stay compact, say so in the field.
- `skill_files`: short excerpts from files the skill points at that define
  its decisions (same truncation rule).
- `skill_name`, `skill_argument`
- `needs`, `gathered`, `context`
- the evidence the decision is made from (compact)

If a required fact cannot be gathered, say so in `gathered`. Still try
breakdown; do not invent the fact.

## 3. Can Jev predict this skill?

Write the JSON body with `jq` (or equivalent) to a temp file. Do not
interpolate state into a single-quoted `-d '...'`. Apostrophes in skill
prose must survive encoding.

```bash
jq -n \
  --argjson state "$STATE_JSON" \
  --arg instructions "$BREAKDOWN_INSTRUCTIONS" \
  --arg true_c "$BREAKDOWN_TRUE" \
  --arg false_c "$BREAKDOWN_FALSE" \
  '{
    state: $state,
    model: "jev-latest",
    questions: {
      can_break_down: {
        type: "noul",
        instructions: $instructions,
        criteria: {true: $true_c, false: $false_c}
      }
    }
  }' > /tmp/jev-predict-breakdown.json

# Retry 429/529 up to twice (1s, 2s). Inspect http_code, not curl exit only.
curl -sS -o /tmp/jev-predict-breakdown.out -w "%{http_code}" \
  https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/jev-predict-breakdown.json
```

Do not log the bearer token.

- Missing key, HTTP after retries, parse failure, or missing noul → report
  that assessment failed (name 401 / 422 / transient when known); stop. No
  prediction.
- Noul `< 0.65` → report that the skill cannot be broken down for Jev; stop.
  No prediction.
- Otherwise continue.

## 4. Break down the next decision (you, not Jev)

Do not ask Jev to invent labels. Take the first non-empty unique list the
**argument skill** itself gives you for the **next** closed decision only:

1. YAML `outcomes:` or an equivalent declared option list.
2. A heading that is clearly the decision set, plus its bullets.
3. A table column that is clearly that set.
4. Named alternatives the skill text says it will pick among.

If that extracted list has fewer than two labels from the skill itself →
report that it cannot be broken down; stop. No prediction.

Then append `none_of_the_above` if it is missing.

Do not Jev-select later sequential decisions in this run. One next Choice
is the answer.

## 5. Jev-select

Build the body the same way as section 3 (`jq` to a file, `-d @file`,
retry `429`/`529`, inspect `http_code`). Selection `criteria` is one
entry per extracted label (including `none_of_the_above`).

Call failure after retries, or a response that lacks any of
`answers.outcome.choice`, `answers.outcome.confidence`, or
`answers.outcome.probabilities` → report that selection failed; stop. No
prediction.

`choice` must be a member of the extracted option set. The probability
map must include every option. If either check fails → report that
selection failed; stop. No prediction.

`none_of_the_above` → report that Jev found no matching outcome; stop. No
invented label.

Otherwise report **predicted**: `outcome`, `outcomes`, `confidence`,
`probabilities`, and the breakdown noul. That is the answer. Do not run
the argument skill to check it.
