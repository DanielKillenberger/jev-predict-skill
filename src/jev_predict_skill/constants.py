"""Thresholds and Jev questions — keep reviewable in one place."""

from __future__ import annotations

BREAKDOWN_NOUL_MIN = 0.65

BREAKDOWN_INSTRUCTIONS = (
    "Can this skill be broken down into a predetermined, closed set of "
    "decision outcomes that Jev can select among, rather than open-ended "
    "generation or undecomposable slow reasoning?"
)

BREAKDOWN_CRITERIA = {
    "true": (
        "The skill has or implies a finite named outcome set that a Choice "
        "question can cover without inventing new labels."
    ),
    "false": (
        "Outcomes are open-ended, generated as free text, or not a closed set."
    ),
}

SELECT_INSTRUCTIONS = (
    "Given the skill body and the current context, which closed decision "
    "outcome would running that skill produce right now? Pick only from the "
    "provided options. Do not invent a new outcome."
)

NONE_OF_THE_ABOVE = "none_of_the_above"

FLOW_NEXT_FLOW_ALIASES = frozenset(
    {
        "flow",
        "/flow",
        "flow-next-flow",
        "/flow-next-flow",
        "flow-next:flow",
        "/flow-next:flow",
    }
)

FLOW_NEXT_FLOW_OUTCOMES = (
    "strategy",
    "prospect",
    "chart",
    "capture",
    "refine",
    "plan",
    "plan-review",
    "work",
    "qa",
    "make-pr",
    "resolve-pr",
    "land",
    "features",
    "visual",
    "prose",
    NONE_OF_THE_ABOVE,
)

OUTCOME_SECTION_TITLES = frozenset(
    {
        "outcomes",
        "decision outcomes",
        "routes",
        "phases",
        "possible outcomes",
        "closed outcomes",
    }
)

TABLE_OUTCOME_HEADERS = frozenset(
    {"route", "outcome", "phase", "decision", "outcomes"}
)
