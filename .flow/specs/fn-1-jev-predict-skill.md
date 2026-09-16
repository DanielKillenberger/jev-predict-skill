# Jev-predict skill

> HTML render lens: [.flow/artifacts/fn-1-jev-predict-skill/spec.html](../artifacts/fn-1-jev-predict-skill/spec.html) — regenerable, markdown is the record. <!-- flow-next:artifact-link -->

## Conversation Evidence

> user (turn 1, part 1): "setup a new project in ~/Projects/jev-predict-skill"
> user (turn 1, part 2): "Setup flow-next"
> user (turn 1, part 3): "and then /flow a /jev-predict-skill skill that takes any skill as an "argument". It first assesses if the skill is predictable by jev => can be broken down into structured outcomes etc."
> user (turn 1, part 4): "For /flow-next-flow it would predict the the flow-next phase that the conductor would choose without actually running the conductor."
> user (turn 2): "it's typesafe.ai just to be clear"
> user (turn 3): "it shouldn't just work for flow-next. If the skill has a predetirmened set of outcomes like /flow the /jev-predict-skill should first break down the skill into a set of decision outcomes and then run jev against it, the context and the actual skill to get the outcome much faster."
> user (turn 4): "well first step should actually be to use jev to determine how confident it is that a breakdown can be made"
> user (turn 5): "why are these python scripts shouldn't this just be a skill file?"
> user (turn 6): "i don't see the need for python unless to gather context or smth"
> user (turn 7): "the skill should be generalized and the first step shouldn't be if the skill can be broken down but if running it with jev-predict-skill will get satisfying results at faster speed than the original skill. If not we just execute the skill."
> user (turn 8): "don't have specific mention of flow-next pls. It's a generalizable task. So it should know what the skill needs to function well and make a good prediction."
> user (turn 9): "the gate's question is wrong. If we run impl-review and we get SHIP at the end of it. But we can predict 99% certainty that it'll be ship then we could skip it. SO we need to adapt the gate to reflect this."
> user (turn 10): "ofc it won't be better..."
> user (turn 11): "ok well then let's remove that gate. If the user wants to use jev then we should only return if the skill is not a match or cannot be broken down in ways that jev can make predictions. Otherwise break down the decisions the skill makes and have jev make the prediction"

## Goal & Context

<!-- Source-tag breakdown: 80% [user] / 20% [paraphrase] -->

A host `/jev-predict-skill` (a `SKILL.md`, not a Python package) that takes any skill as an "argument". The user asked for a Jev prediction. It returns without a prediction only if the argument is not a skill or cannot be broken into closed decisions Jev can select. Otherwise it extracts those decisions and Jev-selects. No certainty-to-skip gate. No automatic execute of the argument skill.

## API Contracts

<!-- scope: technical -->

Invocation takes any skill as an "argument". [user]

Gather compact decision evidence. [user]

Eligibility only: not a match, or cannot be broken down for Jev. [user]

Otherwise break down the skill's decisions and Jev-predict. Report the Choice. Do not run the argument skill to check. [user]

## Acceptance Criteria

<!-- scope: both -->

- **R1:** The skill takes any skill as an "argument". Errors: missing argument → report that no skill was given and produce no prediction; argument that cannot be read as a skill → report that and produce no prediction. [paraphrase]
- **R2:** It assesses whether the argument skill can be broken into closed decisions Jev can select. Errors: assessment cannot complete → report that and produce no prediction. [user]
- **R3:** When breakdown is possible, predict the next closed decision from the skill's own outcome set plus gathered evidence, without running the skill. [user]
- **R4:** When the argument is not a skill match, or cannot be broken down for Jev, report that and produce no prediction. Do not invent outcomes. Do not silently execute the argument skill. [user]
- **R5:** A prediction is a structured Choice over discrete outcomes, with confidence and probabilities. Errors: no closed set or failed selection → report that, no invented outcome. [paraphrase]
- **R6:** The skill is general for any argument skill. It infers what that skill's decisions need and gathers it; it does not special-case a named family of skills. Errors: no error surface beyond R1. [user]
- **R7:** The only Jev eligibility question is whether a closed breakdown can be made. There is no better-work gate and no certainty-to-skip gate. Errors: Jev call fails → report that; low breakdown noul → report cannot-break-down. [user]
- **R8:** After R7 passes, extract the decision set and Jev-select. Report the Choice even when confidence is below 0.99. [user]
- **R9:** A successful prediction is produced without executing the argument skill. [paraphrase]
- **R10:** Do not fall through to executing the argument skill unless the user asks. Ineligible or failed prediction is a report, not a live run. [user]

## Boundaries

<!-- scope: business -->

- Does not run the argument skill unless the user asks. [user]
- Returns without a prediction only on not-a-match or cannot-break-down (or a failed Jev call). [user]
- Does not special-case any named argument skill. [user]
- Is a host skill file, not a Python package. [user]

## Decision Context

<!-- scope: both — FLAT -->

The user asked for Jev. Eligibility is match + closed breakdown. Then extract the skill's decisions and Jev-select. No skip-certainty gate. No automatic execute. Outcome labels come from the argument skill. Keep state compact and decision-relevant. [user]

## Parked unknowns

- How a skill argument is resolved (slash name, skill file, or pasted body). Resolved by picking one resolution rule.

## Resolved via Research
<!-- provenance: refine --scope=research (docs-scout, practice-scout, docs-gap-scout, memory-scout) on 2026-09-16; plan writes the same section when its Step 1 runs the same scouts -->

### docs-scout
- **TypeSafe Jev** — flagship System One model; send `state` plus typed questions, receive structured answers, never generated text. Source: https://docs.typesafe.ai/concepts/system-one.md
- **HTTP** — `POST https://api.typesafe.ai/v1/systemone` with Bearer API key; body `{state, model: "jev-latest", questions}`; repo has no manifest so version-anchor is none. Source: https://docs.typesafe.ai/api.md
- **SDKs** — Python `typesafe-sdk` (`TypeSafeClient().system_one`) and JS `@typesafe-ai/sdk` (`systemOne`); docs current v0.6.0; env `TYPESAFE_API_KEY`; default model `jev-latest`. Source: https://docs.typesafe.ai/sdk/python.md
- **Primitives** — Choice `{choice, probabilities, confidence}`, Score `{score, legend, probabilities, confidence}`, Noul `{noul: 0..1}` (no separate confidence). Source: https://docs.typesafe.ai/primitives.md
- **Predictable** — a skill is Jev-predictable only if its outcomes are a predeclared closed Choice/Score/Noul set; generation, open values, or undecomposable slow reasoning are not. Source: https://docs.typesafe.ai/introduction.md
- **Closed prediction** — map a skill to one Choice over labels that skill itself declares; Jev must not invent a label. Source: https://docs.typesafe.ai/primitives/choice.md
- **Nearest cookbooks** — skill suggestion (need-a-skill Noul, then closed names), function calling (closed args only), confidence-gated classification / intent routing. Source: https://docs.typesafe.ai/cookbooks/skill_suggestion.md
- **Errors** — `401` auth, `422` validation, `429` rate limit, `529` overload; SDKs retry with backoff. Source: https://docs.typesafe.ai/api.md

### practice-scout
- **Gotcha:** do not ask Jev to analyze, reason, or generate a prediction document — keep snap judgments and compose in host code. Source: https://docs.typesafe.ai/primitives.md
- **Gotcha:** do not invent a free-form output schema; answers cannot leave the options or levels you supplied. Source: https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md
- **Gotcha:** include `other` / `none of the above` when the option set may not cover the skill, or Jev is forced to pick a false winner. Source: https://docs.typesafe.ai/primitives/choice.md
- **Gotcha:** treat “predictable?” as a Noul or Choice gate, then refuse to predict when the gate fails; low Choice/Score confidence or Noul near 0.5 means do not act. Source: https://docs.typesafe.ai/patterns/confidence-routing.md
- **Gotcha:** put in `state` the inputs and read-only status the argument skill needs to function; Choice over labels that skill declares — do not hardcode a named skill's option list. Source: https://docs.typesafe.ai/concepts/state.md
- **Gotcha:** host `SKILL.md` gathers state and calls TypeSafe; Jev is not itself a host skill; keep `TYPESAFE_API_KEY` out of the skill file. Source: https://docs.typesafe.ai/agent-skill.md
- **Gotcha:** batch every question over the same state in one request; a second call only when the first answer is required to fetch evidence or change options. Source: https://docs.typesafe.ai/cookbooks/parallel_questions.md
