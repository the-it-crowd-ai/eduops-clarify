"""Safe data-loading tools: expected test answers must NEVER go to the model."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_assessment(student_id: str) -> dict:
    """Get a fictional learner's question, rubric and answer, excluding labels.

    Args:
        student_id: Learner identifier, e.g. student_001.

    Returns:
        The assessment input, or an error if the student is not found.
    """
    try:
        rubric = json.loads((DATA_DIR / "marking_rubric.json").read_text(encoding="utf-8"))
        cases = json.loads((DATA_DIR / "test_data.json").read_text(encoding="utf-8"))
        for case in cases["test_cases"]:
            if case.get("student_id") == student_id:
                return {
                    "student_id": student_id,
                    "question_id": rubric["question_id"],
                    "question": rubric["question"],
                    "maximum_mark": rubric["maximum_mark"],
                    "rubric": rubric["rubric"],
                    "student_answer": case["student_answer"],
                }
        return {"error": f"Student ID not found: {student_id}"}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"error": f"Assessment data could not be loaded: {type(exc).__name__}"}
