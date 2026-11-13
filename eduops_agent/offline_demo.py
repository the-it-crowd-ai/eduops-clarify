"""OFFLINE FIXTURE SIMULATION: not a Gemini call or a true AI demonstration.

Run: python -m eduops_agent.offline_demo
This proves the deterministic correction/audit path works when Gemini is down.
"""

import json
from .assessment_tools import load_assessment
from .pipeline import reconcile
from .storage import DEFAULT_DB, save_report


def run_demo(db_path=DEFAULT_DB) -> dict:
    assessment = load_assessment("student_001")
    if "error" in assessment:
        raise SystemExit(assessment["error"])
    draft = {
        "student_id": "student_001", "question_id": "Q001",
        "maximum_mark": 2, "proposed_mark": 2,
        "criterion_results": [
            {"criterion_id": "C1", "awarded_points": 1,
             "evidence": "THIS QUOTE WAS INVENTED"},
            {"criterion_id": "C2", "awarded_points": 1,
             "evidence": "same money can't buy like before"},
        ],
        "explanation": "Deliberately faulty fixture for validation testing.",
        "status": "assessed", "clarification_question": None,
    }
    independent = {
        **draft, "explanation": "The two concepts are evidenced in the learner answer.",
        "criterion_results": [
            {"criterion_id": "C1", "awarded_points": 1,
             "evidence": "Things getting expensive"},
            {"criterion_id": "C2", "awarded_points": 1,
             "evidence": "same money can't buy like before"},
        ],
    }
    # The inputs above are FIXTURES, not the output of any AI agent.
    report = reconcile(assessment, draft, independent)
    report["execution_mode"] = "OFFLINE_SIMULATION_NO_AI"
    report["trace"] = [
        "OFFLINE_FIXTURE_assessment_not_an_agent_call",
        "OFFLINE_FIXTURE_verification_not_an_agent_call",
        "deterministic_validation_completed",
        "invalid_initial_fixture_replaced_with_valid_independent_fixture",
    ]
    report["run_id"] = save_report(report, db_path)
    return report


def main():
    report = run_demo()
    print("OFFLINE SIMULATION ONLY — no Gemini/API call made")
    print(json.dumps({
        "run_id": report["run_id"],
        "mode": report["execution_mode"],
        "decision": report["decision"],
        "status": report["status"],
        "proposed_mark": report["final_result"]["proposed_mark"],
        "feedback": report["feedback"],
        "teacher_approval_required": report["teacher_approval_required"],
        "initial_validation_errors": report["initial_validation_errors"],
        "trace": report["trace"],
    }, indent=2))


if __name__ == "__main__":
    main()
