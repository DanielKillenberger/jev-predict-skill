"""Jev-first prediction pipeline. Never executes the argument skill."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from jev_predict_skill.constants import BREAKDOWN_NOUL_MIN
from jev_predict_skill.jev import HttpJevClient, JevClient, JevError
from jev_predict_skill.outcomes import extract_outcomes
from jev_predict_skill.resolve import ResolveError, ResolvedSkill, resolve_skill

Status = Literal["predicted", "not_predictable", "error"]


@dataclass(frozen=True)
class Prediction:
    outcome: str
    outcomes: tuple[str, ...]
    probabilities: dict[str, float]
    confidence: float
    breakdown_noul: float
    argument_skill: str
    executed_argument_skill: bool = False


@dataclass(frozen=True)
class PredictResult:
    status: Status
    kind: str
    message: str
    prediction: Prediction | None = None
    breakdown_noul: float | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status,
            "kind": self.kind,
            "message": self.message,
            "prediction": None,
            "breakdown_noul": self.breakdown_noul,
        }
        if self.prediction is not None:
            payload["prediction"] = {
                "outcome": self.prediction.outcome,
                "outcomes": list(self.prediction.outcomes),
                "probabilities": self.prediction.probabilities,
                "confidence": self.prediction.confidence,
                "breakdown_noul": self.prediction.breakdown_noul,
                "argument_skill": self.prediction.argument_skill,
                "executed_argument_skill": self.prediction.executed_argument_skill,
            }
        return payload


def _error(kind: str, message: str, *, noul: float | None = None) -> PredictResult:
    return PredictResult(
        status="error",
        kind=kind,
        message=message,
        breakdown_noul=noul,
    )


def _not_predictable(message: str, *, noul: float | None = None) -> PredictResult:
    return PredictResult(
        status="not_predictable",
        kind="not_predictable",
        message=message,
        breakdown_noul=noul,
    )


def predict_skill(
    argument: str | None,
    *,
    context: str = "",
    jev: JevClient | None = None,
    search_roots: tuple[Path, ...] | None = None,
    cwd: Path | None = None,
    home: Path | None = None,
    flow_state: dict[str, Any] | None = None,
) -> PredictResult:
    """Assess, extract, and Jev-select. Never executes the argument skill."""

    resolved = resolve_skill(argument, search_roots=search_roots, cwd=cwd, home=home)
    if isinstance(resolved, ResolveError):
        return _error(resolved.kind, resolved.message)

    client = jev if jev is not None else HttpJevClient()
    state = _judgment_state(resolved, context=context, flow_state=flow_state)

    try:
        noul = client.assess_breakdown(state)
    except JevError as exc:
        return _error("assessment_failed", f"Assessment could not complete: {exc}")
    except Exception as exc:  # noqa: BLE001 — any client crash is an assessment failure
        return _error("assessment_failed", f"Assessment could not complete: {exc}")

    if noul < BREAKDOWN_NOUL_MIN:
        return _not_predictable(
            "Skill is not predictable by Jev: low confidence that a breakdown can be made.",
            noul=noul,
        )

    outcomes = extract_outcomes(resolved.body, name=resolved.name, argument=resolved.argument)
    if not outcomes:
        return _not_predictable(
            "Skill is not predictable by Jev: breakdown yielded no closed outcome set.",
            noul=noul,
        )

    try:
        selected = client.select_outcome(state, outcomes)
    except JevError as exc:
        return _error("selection_failed", f"Jev selection failed: {exc}", noul=noul)
    except Exception as exc:  # noqa: BLE001 — any client crash is a selection failure
        return _error("selection_failed", f"Jev selection failed: {exc}", noul=noul)

    return PredictResult(
        status="predicted",
        kind="predicted",
        message=f"Predicted outcome: {selected.choice}",
        breakdown_noul=noul,
        prediction=Prediction(
            outcome=selected.choice,
            outcomes=outcomes,
            probabilities=selected.probabilities,
            confidence=selected.confidence,
            breakdown_noul=noul,
            argument_skill=resolved.name,
            executed_argument_skill=False,
        ),
    )


def _judgment_state(
    resolved: ResolvedSkill,
    *,
    context: str,
    flow_state: dict[str, Any] | None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "skill_name": resolved.name,
        "skill_argument": resolved.argument,
        "skill_body": resolved.body,
        "context": context,
    }
    if flow_state:
        state["flow_state"] = flow_state
    return state
