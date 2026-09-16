"""CLI for /jev-predict-skill. Prints a report; never runs the argument skill."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from jev_predict_skill.predict import PredictResult, predict_skill


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jev-predict-skill",
        description=(
            "Predict a skill's closed decision outcome with TypeSafe Jev "
            "without executing that skill."
        ),
    )
    parser.add_argument(
        "skill",
        nargs="?",
        help="Skill slash name, path to SKILL.md, or pasted skill body.",
    )
    parser.add_argument(
        "--context",
        default="",
        help="Current session or repo context to include in the Jev state.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the machine-readable result object.",
    )
    return parser


def format_report(result: PredictResult) -> str:
    lines = [
        f"status: {result.status}",
        f"kind: {result.kind}",
        f"message: {result.message}",
    ]
    if result.breakdown_noul is not None:
        lines.append(f"breakdown_noul: {result.breakdown_noul:.3f}")
    if result.prediction is None:
        lines.append("prediction: none")
        return "\n".join(lines)
    pred = result.prediction
    lines.extend(
        [
            f"outcome: {pred.outcome}",
            f"outcomes: {', '.join(pred.outcomes)}",
            f"confidence: {pred.confidence:.3f}",
            f"argument_skill: {pred.argument_skill}",
            f"executed_argument_skill: {str(pred.executed_argument_skill).lower()}",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = predict_skill(args.skill, context=args.context)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_report(result))
    if result.status == "predicted":
        return 0
    if result.status == "not_predictable":
        return 2
    return 1


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
