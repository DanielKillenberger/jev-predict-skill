"""Focused tests for each AC error case and the structured prediction paths."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jev_predict_skill.cli import format_report, run
from jev_predict_skill.constants import BREAKDOWN_NOUL_MIN, FLOW_NEXT_FLOW_OUTCOMES
from jev_predict_skill.jev import ChoiceAnswer, JevError
from jev_predict_skill.outcomes import extract_outcomes
from jev_predict_skill.predict import predict_skill

FLOW_SKILL = """---
name: flow-next-flow
description: Conductor that routes the next flow-next phase.
---

# /flow-next-flow
"""

GENERIC_SKILL = """---
name: ship-or-wait
description: Choose whether to ship or wait.
---

# Ship or wait

## Outcomes

- ship
- wait
"""

OPEN_SKILL = """---
name: brainstorm
description: Open-ended brainstorming with no closed outcomes.
---

# Brainstorm

Write whatever ideas come to mind.
"""


class FakeJev:
    def __init__(
        self,
        *,
        noul: float = 0.9,
        choice: str = "work",
        assess_error: Exception | None = None,
        select_error: Exception | None = None,
    ) -> None:
        self.noul = noul
        self.choice = choice
        self.assess_error = assess_error
        self.select_error = select_error
        self.assess_calls = 0
        self.select_calls = 0
        self.last_outcomes: tuple[str, ...] | None = None

    def assess_breakdown(self, state):
        self.assess_calls += 1
        if self.assess_error:
            raise self.assess_error
        return self.noul

    def select_outcome(self, state, outcomes):
        self.select_calls += 1
        self.last_outcomes = outcomes
        if self.select_error:
            raise self.select_error
        return ChoiceAnswer(
            choice=self.choice,
            probabilities={self.choice: 0.8},
            confidence=0.8,
        )


def _write_skill(directory: Path, name: str, body: str) -> Path:
    skill_dir = directory / name
    skill_dir.mkdir()
    path = skill_dir / "SKILL.md"
    path.write_text(body, encoding="utf-8")
    return path


class PredictSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.skills = self.root / "skills"
        self.skills.mkdir()
        self.addCleanup(self.tmp.cleanup)

    def _predict(self, argument, jev=None, **kwargs):
        return predict_skill(
            argument,
            jev=jev or FakeJev(),
            search_roots=(self.skills,),
            cwd=self.root,
            home=self.root,
            **kwargs,
        )

    def test_missing_argument_reports_and_has_no_prediction(self):
        for argument in (None, "", "   "):
            with self.subTest(argument=argument):
                result = self._predict(argument)
                self.assertEqual(result.status, "error")
                self.assertEqual(result.kind, "missing_argument")
                self.assertIn("No skill was given", result.message)
                self.assertIsNone(result.prediction)

    def test_unreadable_skill_reports_and_has_no_prediction(self):
        result = self._predict("not-a-real-skill-xyz")
        self.assertEqual(result.status, "error")
        self.assertEqual(result.kind, "unreadable_skill")
        self.assertIn("cannot be read as a skill", result.message)
        self.assertIsNone(result.prediction)

    def test_assessment_cannot_complete_reports_and_has_no_prediction(self):
        jev = FakeJev(assess_error=JevError("HTTP 529"))
        _write_skill(self.skills, "ship-or-wait", GENERIC_SKILL)
        result = self._predict("ship-or-wait", jev=jev)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.kind, "assessment_failed")
        self.assertIn("Assessment could not complete", result.message)
        self.assertIsNone(result.prediction)
        self.assertEqual(jev.select_calls, 0)

    def test_low_confidence_is_not_predictable_and_stops(self):
        jev = FakeJev(noul=0.41, choice="ship")
        _write_skill(self.skills, "ship-or-wait", GENERIC_SKILL)
        result = self._predict("ship-or-wait", jev=jev)
        self.assertEqual(result.status, "not_predictable")
        self.assertIsNone(result.prediction)
        self.assertLess(result.breakdown_noul, BREAKDOWN_NOUL_MIN)
        self.assertEqual(jev.select_calls, 0)
        self.assertIn("not predictable", result.message.lower())

    def test_no_closed_outcome_set_is_not_predictable(self):
        jev = FakeJev(noul=0.91, choice="invented")
        _write_skill(self.skills, "brainstorm", OPEN_SKILL)
        result = self._predict("brainstorm", jev=jev)
        self.assertEqual(result.status, "not_predictable")
        self.assertIsNone(result.prediction)
        self.assertIn("no closed outcome set", result.message)
        self.assertEqual(jev.select_calls, 0)

    def test_selection_failure_reports_and_has_no_prediction(self):
        jev = FakeJev(noul=0.92, select_error=JevError("HTTP 422"))
        _write_skill(self.skills, "ship-or-wait", GENERIC_SKILL)
        result = self._predict("ship-or-wait", jev=jev)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.kind, "selection_failed")
        self.assertIn("Jev selection failed", result.message)
        self.assertIsNone(result.prediction)

    def test_flow_next_flow_predicts_a_conductor_phase(self):
        jev = FakeJev(noul=0.93, choice="work")
        _write_skill(self.skills, "flow-next-flow", FLOW_SKILL)
        result = self._predict("/flow-next-flow", jev=jev)
        self.assertEqual(result.status, "predicted")
        self.assertIsNotNone(result.prediction)
        self.assertEqual(result.prediction.outcome, "work")
        self.assertIn("work", result.prediction.outcomes)
        self.assertEqual(result.prediction.outcomes, FLOW_NEXT_FLOW_OUTCOMES)
        self.assertFalse(result.prediction.executed_argument_skill)
        self.assertEqual(jev.last_outcomes, FLOW_NEXT_FLOW_OUTCOMES)

    def test_generic_predetermined_skill_returns_discrete_outcomes(self):
        jev = FakeJev(noul=0.88, choice="wait")
        _write_skill(self.skills, "ship-or-wait", GENERIC_SKILL)
        result = self._predict("/ship-or-wait", jev=jev)
        self.assertEqual(result.status, "predicted")
        self.assertEqual(result.prediction.outcome, "wait")
        self.assertEqual(result.prediction.outcomes, ("ship", "wait"))
        self.assertNotEqual(result.prediction.outcomes, FLOW_NEXT_FLOW_OUTCOMES)

    def test_flow_alias_uses_the_same_closed_phase_set(self):
        _write_skill(self.skills, "flow-next-flow", FLOW_SKILL)
        outcomes = extract_outcomes(FLOW_SKILL, name="flow-next-flow", argument="/flow")
        self.assertEqual(outcomes, FLOW_NEXT_FLOW_OUTCOMES)

    def test_report_omits_prediction_on_errors(self):
        result = self._predict(None)
        report = format_report(result)
        self.assertIn("prediction: none", report)
        self.assertNotIn("outcome:", report)


class CliTests(unittest.TestCase):
    def test_cli_missing_argument_exits_error(self):
        code = run([])
        self.assertEqual(code, 1)


class OutcomeExtractionTests(unittest.TestCase):
    def test_frontmatter_outcomes_list(self):
        body = "---\nname: demo\noutcomes:\n  - alpha\n  - beta\n---\n# Demo\n"
        self.assertEqual(extract_outcomes(body, name="demo"), ("alpha", "beta"))


if __name__ == "__main__":
    unittest.main()
