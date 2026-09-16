"""TypeSafe Jev client. Questions stay typed; the host composes the result."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

SYSTEM_ONE_URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"


class JevError(Exception):
    """Jev could not complete a judgment."""


@dataclass(frozen=True)
class ChoiceAnswer:
    choice: str
    probabilities: dict[str, float]
    confidence: float


class JevClient(Protocol):
    def assess_breakdown(self, state: dict[str, Any]) -> float:
        """Return a Noul in [0, 1] that a closed breakdown is possible."""

    def select_outcome(self, state: dict[str, Any], outcomes: tuple[str, ...]) -> ChoiceAnswer:
        """Choose one closed outcome."""


class HttpJevClient:
    """POST /v1/systemone. Reads TYPESAFE_API_KEY; never logs it."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        url: str = SYSTEM_ONE_URL,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get("TYPESAFE_API_KEY")
        self._url = url
        self._timeout = timeout

    def assess_breakdown(self, state: dict[str, Any]) -> float:
        from jev_predict_skill.constants import BREAKDOWN_CRITERIA, BREAKDOWN_INSTRUCTIONS

        payload = self._system_one(
            state,
            {
                "breakdown": {
                    "type": "noul",
                    "instructions": BREAKDOWN_INSTRUCTIONS,
                    "criteria": BREAKDOWN_CRITERIA,
                }
            },
        )
        answer = _require_answer(payload, "breakdown")
        noul = answer.get("noul")
        if not isinstance(noul, (int, float)):
            raise JevError("Jev breakdown answer was missing a noul.")
        return float(noul)

    def select_outcome(self, state: dict[str, Any], outcomes: tuple[str, ...]) -> ChoiceAnswer:
        from jev_predict_skill.constants import SELECT_INSTRUCTIONS

        payload = self._system_one(
            state,
            {
                "outcome": {
                    "type": "choice",
                    "instructions": SELECT_INSTRUCTIONS,
                    "criteria": {option: None for option in outcomes},
                }
            },
        )
        answer = _require_answer(payload, "outcome")
        choice = answer.get("choice")
        if not isinstance(choice, str) or not choice:
            raise JevError("Jev selection answer was missing a choice.")
        raw_probs = answer.get("probabilities") or {}
        if not isinstance(raw_probs, dict):
            raise JevError("Jev selection answer had invalid probabilities.")
        probabilities = {
            str(key): float(value)
            for key, value in raw_probs.items()
            if isinstance(value, (int, float))
        }
        confidence = answer.get("confidence", 0.0)
        if not isinstance(confidence, (int, float)):
            confidence = 0.0
        return ChoiceAnswer(
            choice=choice,
            probabilities=probabilities,
            confidence=float(confidence),
        )

    def _system_one(self, state: dict[str, Any], questions: dict[str, Any]) -> dict[str, Any]:
        if not self._api_key:
            raise JevError("Jev call failed: TYPESAFE_API_KEY is not set.")
        body = json.dumps(
            {"state": state, "model": DEFAULT_MODEL, "questions": questions}
        ).encode("utf-8")
        request = urllib.request.Request(
            self._url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            raise JevError(f"Jev call failed: HTTP {exc.code}.") from exc
        except urllib.error.URLError as exc:
            raise JevError(f"Jev call failed: {exc.reason}.") from exc
        except TimeoutError as exc:
            raise JevError("Jev call failed: request timed out.") from exc
        except json.JSONDecodeError as exc:
            raise JevError("Jev call failed: response was not JSON.") from exc
        if not isinstance(payload, dict):
            raise JevError("Jev call failed: response was not an object.")
        return payload


def _require_answer(payload: dict[str, Any], key: str) -> dict[str, Any]:
    answers = payload.get("answers")
    if not isinstance(answers, dict) or key not in answers:
        raise JevError(f"Jev call failed: missing '{key}' answer.")
    answer = answers[key]
    if not isinstance(answer, dict):
        raise JevError(f"Jev call failed: '{key}' answer was not an object.")
    return answer
