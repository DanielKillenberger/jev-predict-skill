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

## Goal & Context

<!-- Source-tag breakdown: 80% [user] / 20% [paraphrase] -->

A `/jev-predict-skill` that takes any skill as an "argument" — not only flow-next. It uses TypeSafe Jev (typesafe.ai). The first step is to use Jev to determine how confident it is that a breakdown can be made. If the skill has a predetermined set of outcomes (like `/flow`), it then breaks the skill into a set of decision outcomes and runs Jev against those outcomes, the context, and the actual skill to get the outcome much faster, without running the argument skill.

## API Contracts

<!-- scope: technical -->

Invocation takes any skill as an "argument". [user]

Step 1: use Jev to determine how confident it is that a breakdown can be made. [user]

Step 2 (only if that confidence is high enough): break the skill down into a set of decision outcomes. [paraphrase]

Step 3: run Jev against that outcome set, the context, and the actual skill to select the outcome. [paraphrase]

`/flow` is one example of a skill with a predetermined outcome set, not the only supported skill. [paraphrase]

## Acceptance Criteria

<!-- scope: both -->

- **R1:** The skill takes any skill as an "argument". Errors: missing argument → report that no skill was given and produce no prediction; argument that cannot be read as a skill → report that and produce no prediction. [paraphrase]
- **R2:** It first assesses if the skill is predictable by jev — whether it can be broken down into structured outcomes. Errors: assessment cannot complete → report the failure and produce no prediction. [paraphrase]
- **R3:** For `/flow-next-flow` it predicts the flow-next phase that the conductor would choose without actually running the conductor. Errors: no error surface beyond R1 and R2 when the argument is `/flow-next-flow` and R2 finds it predictable. [paraphrase]
- **R4:** When the assessment finds the skill is not predictable by jev, the skill reports that result and does not invent a structured-outcomes prediction or a conductor phase. Errors: no error surface beyond the explicit not-predictable report. [inferred]
- **R5:** When the assessment finds the skill is predictable by jev and the argument is not `/flow-next-flow`, the skill produces a structured prediction composed of discrete outcomes rather than only unstructured prose. Errors: no error surface beyond R1 and R2. [paraphrase]
- **R6:** The skill is not limited to flow-next; it works for any argument skill that has a predetermined set of outcomes, `/flow` being one example. Errors: no error surface beyond R1. [paraphrase]
- **R7:** The first step uses Jev to determine how confident it is that a breakdown can be made. Errors: Jev call fails → report that and produce no prediction; low confidence that a breakdown can be made → report not-predictable and stop (no breakdown, no outcome prediction). [user]
- **R8:** Only after R7 is confident enough, break the skill into a set of decision outcomes, then run Jev against that set, the context, and the actual skill to get the outcome. Errors: breakdown yields no closed outcome set → report not-predictable and produce no invented outcome; Jev selection fails → report that and produce no prediction. [paraphrase]
- **R9:** The selected outcome is produced without executing or running the argument skill, so the result is faster than a live run of that skill. Errors: no error surface beyond R7 and R8. [paraphrase]

## Boundaries

<!-- scope: business -->

- Does not actually run the conductor. [paraphrase]
- Does not execute or implement the argument skill. [inferred]
- Does not replace `/flow-next-flow`. [inferred]
- Does not only support flow-next skills. [paraphrase]

## Decision Context

<!-- scope: both — FLAT -->

Use Jev first to judge confidence that a breakdown can be made; only then extract a closed outcome set and run Jev on those outcomes plus context plus the skill. That is faster than running the argument skill (for example `/flow`) and stays a prediction, not a live hop. [paraphrase]

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
- **Phase prediction** — `/flow-next-flow` maps to one Choice over a known phase-name set (plus optional Nouls); Jev must not invent a phase string. Source: https://docs.typesafe.ai/primitives/choice.md
- **Nearest cookbooks** — skill suggestion (need-a-skill Noul, then closed names), function calling (closed args only), confidence-gated classification / intent routing. Source: https://docs.typesafe.ai/cookbooks/skill_suggestion.md
- **Errors** — `401` auth, `422` validation, `429` rate limit, `529` overload; SDKs retry with backoff. Source: https://docs.typesafe.ai/api.md

### practice-scout
- **Gotcha:** do not ask Jev to analyze, reason, or generate a prediction document — keep snap judgments and compose in host code. Source: https://docs.typesafe.ai/primitives.md
- **Gotcha:** do not invent a free-form output schema; answers cannot leave the options or levels you supplied. Source: https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md
- **Gotcha:** include `other` / `none of the above` when the option set may not cover the skill, or Jev is forced to pick a false winner. Source: https://docs.typesafe.ai/primitives/choice.md
- **Gotcha:** treat “predictable?” as a Noul or Choice gate, then refuse to predict when the gate fails; low Choice/Score confidence or Noul near 0.5 means do not act. Source: https://docs.typesafe.ai/patterns/confidence-routing.md
- **Gotcha:** for `/flow-next-flow`, put route-matrix rows plus observed `flowctl show --json` state in `state`, then Choice over named routes — do not route on input kind or simulate the hop loop in one call. Source: https://flow-next.dev/choosing-your-route/
- **Gotcha:** host `SKILL.md` gathers state and calls TypeSafe; Jev is not itself a host skill; keep `TYPESAFE_API_KEY` out of the skill file. Source: https://docs.typesafe.ai/agent-skill.md
- **Gotcha:** batch every question over the same state in one request; a second call only when the first answer is required to fetch evidence or change options. Source: https://docs.typesafe.ai/cookbooks/parallel_questions.md
