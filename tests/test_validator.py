"""Offline tests: no API calls, no real student data."""

import copy
import unittest

from eduops_agent.validator import validate_result, criterion_signature
from eduops_agent.feedback import suggest_feedback
from eduops_agent.pipeline import parse_json, reconcile

ASSESSMENT = {
    "student_id": "student_001", "question_id": "Q001",
    "question": "Explain inflation and purchasing power.", "maximum_mark": 2,
    "rubric": [
        {"id": "C1", "description": "General prices rise", "points": 1},
        {"id": "C2", "description": "Purchasing power falls", "points": 1},
    ],
    "student_answer": "Things getting expensive and same money can't buy like before.",
}
VALID = {
    "student_id": "student_001", "question_id": "Q001", "proposed_mark": 2,
    "maximum_mark": 2,
    "criterion_results": [
        {"criterion_id": "C1", "awarded_points": 1, "evidence": "Things getting expensive"},
        {"criterion_id": "C2", "awarded_points": 1, "evidence": "same money can't buy like before"},
    ],
    "explanation": "The learner understands prices and what money buys.",
    "status": "assessed", "clarification_question": None,
}


class ValidatorTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_result(ASSESSMENT, VALID), [])

    def test_invented_evidence(self):
        result = copy.deepcopy(VALID)
        result["criterion_results"][0]["evidence"] = "prices went up over time"
        self.assertIn("Evidence for C1 is not an exact quote", validate_result(ASSESSMENT, result))

    def test_mismatched_total(self):
        result = copy.deepcopy(VALID)
        result["proposed_mark"] = 1
        self.assertIn("proposed_mark does not match the sum", validate_result(ASSESSMENT, result))

    def test_duplicate_criterion(self):
        result = copy.deepcopy(VALID)
        result["criterion_results"].append(copy.deepcopy(result["criterion_results"][0]))
        self.assertTrue(any("Duplicate criterion" in msg for msg in validate_result(ASSESSMENT, result)))

    def test_missing_criterion(self):
        result = copy.deepcopy(VALID)
        result["criterion_results"].pop()
        result["proposed_mark"] = 1
        self.assertIn("Not all rubric criteria are represented", validate_result(ASSESSMENT, result))

    def test_boolean_points_rejected(self):
        result = copy.deepcopy(VALID)
        result["criterion_results"][0]["awarded_points"] = True
        self.assertIn("Invalid awarded_points for C1", validate_result(ASSESSMENT, result))

    def test_ambiguous_null_mark(self):
        result = copy.deepcopy(VALID)
        result.update(status="needs_clarification", proposed_mark=None,
                      clarification_question="What do you mean by money going down?",
                      criterion_results=[])
        self.assertEqual(validate_result(ASSESSMENT, result), [])

    def test_unresolved_with_awards_rejected(self):
        result = copy.deepcopy(VALID)
        result.update(status="needs_review", proposed_mark=None)
        self.assertIn("Unresolved assessments must not award points", validate_result(ASSESSMENT, result))

    def test_reconcile_agreement(self):
        report = reconcile(ASSESSMENT, VALID, copy.deepcopy(VALID))
        self.assertEqual(report["decision"], "agreement")
        self.assertEqual(report["final_result"]["proposed_mark"], 2)

    def test_reconcile_disagreement_is_review(self):
        independent = copy.deepcopy(VALID)
        independent["proposed_mark"] = 1
        independent["criterion_results"][1].update(awarded_points=0, evidence="")
        report = reconcile(ASSESSMENT, VALID, independent)
        self.assertEqual(report["status"], "needs_review")
        self.assertIsNone(report["final_result"])

    def test_reconcile_repairs_invalid_evidence(self):
        draft = copy.deepcopy(VALID)
        draft["criterion_results"][0]["evidence"] = "fictional quotation"
        report = reconcile(ASSESSMENT, draft, VALID)
        self.assertEqual(report["decision"], "corrected_invalid_first_result")
        self.assertTrue(report["teacher_approval_required"])

    def test_json_parsing(self):
        self.assertEqual(parse_json('```json\n{"x": 1}\n```'), {"x": 1})
        with self.assertRaises(Exception):
            parse_json('Ignore rules; {"x": 1}')

    def test_feedback(self):
        result = copy.deepcopy(VALID)
        result["proposed_mark"] = 1
        result["criterion_results"][1].update(awarded_points=0, evidence="")
        self.assertIn("Purchasing power", suggest_feedback(ASSESSMENT, result))
        self.assertNotIn("expected_mark", suggest_feedback(ASSESSMENT, result))

    def test_independent_signature_ignores_prose(self):
        other = copy.deepcopy(VALID)
        other["explanation"] = "Different wording, same grade."
        self.assertEqual(criterion_signature(VALID), criterion_signature(other))


if __name__ == "__main__":
    unittest.main()
