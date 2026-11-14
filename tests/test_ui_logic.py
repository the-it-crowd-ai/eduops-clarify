"""No network or UI dependency: safe view-model tests."""
import json
import tempfile
import unittest
from pathlib import Path

from eduops_ui.logic import can_show_mark, list_fictional_students, summarize_report


class UIHelpersTests(unittest.TestCase):
    def test_error_never_displays_mark(self):
        report = {"status": "error", "error": "503", "final_result": {
            "status": "assessed", "proposed_mark": 2, "maximum_mark": 2}}
        self.assertFalse(can_show_mark(report))
        self.assertIsNone(summarize_report(report)["mark"])

    def test_no_final_result_never_displays_mark(self):
        self.assertFalse(can_show_mark({"status": "needs_review", "proposed_mark": 2}))

    def test_real_result_has_mode_and_mark(self):
        data = {"status": "assessed", "decision": "agreement", "execution_mode": "live_google_adk",
                "final_result": {"status": "assessed", "proposed_mark": 2, "maximum_mark": 2,
                                 "criterion_results": [{"criterion_id": "C1", "awarded_points": 1,
                                                        "evidence": "Things getting expensive"}]}}
        s = summarize_report(data)
        self.assertEqual(s["mark"], 2)
        self.assertIn("Live Gemini", s["mode_label"])

    def test_offline_is_explicitly_labeled(self):
        s = summarize_report({"execution_mode": "OFFLINE_SIMULATION_NO_AI"})
        self.assertIn("no AI", s["mode_label"])

    def test_boolean_cannot_be_displayed_as_mark(self):
        self.assertFalse(can_show_mark({"status": "assessed", "final_result": {
            "status": "assessed", "proposed_mark": True, "maximum_mark": 2}}))

    def test_only_fixture_ids_are_listed(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "test_data.json"
            target.write_text(json.dumps({"test_cases": [
                {"student_id": "student_001"}, {"student_id": "student_002"},
                {"student_id": None}]}), encoding="utf-8")
            self.assertEqual(list_fictional_students(target), ["student_001", "student_002"])


if __name__ == "__main__":
    unittest.main()
