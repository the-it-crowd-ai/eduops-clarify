"""Display-only helpers for EduOps Clarify's teacher-facing workspace.

No Gemini calls or database writes here; source reports are not altered.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DECISION_LABELS = {
    "agreement": "Independent assessments agree",
    "corrected_invalid_first_result": "Invalid evidence corrected",
    "disagreement_requires_teacher": "Agents disagree — review needed",
    "needs_review": "Teacher review needed",
    "verifier_failed_validation": "Verification needs review",
    "both_agents_failed_validation": "Results need review",
    "model_or_runtime_failed": "Model service unavailable",
}


def list_fictional_students(data_path: Path) -> list[str]:
    """Return only learner IDs from the configured fictional fixture file."""
    try:
        payload = json.loads(Path(data_path).read_text(encoding="utf-8"))
        cases = payload.get("test_cases", [])
        return [c["student_id"] for c in cases if isinstance(c, dict)
                and isinstance(c.get("student_id"), str)]
    except (OSError, ValueError, TypeError, AttributeError):
        return []


def summarize_report(report: dict[str, Any]) -> dict[str, Any]:
    """Safely shape an existing report for display; never invent a grade."""
    report = report if isinstance(report, dict) else {}
    result = report.get("final_result")
    if not isinstance(result, dict):
        result = None
    valid_mark = (
        report.get("status") == "assessed" and result is not None
        and result.get("status") == "assessed"
        and type(result.get("proposed_mark")) is int
        and type(result.get("maximum_mark")) is int
        and 0 <= result["proposed_mark"] <= result["maximum_mark"]
    )
    mode = str(report.get("execution_mode", "unknown"))
    if mode == "OFFLINE_SIMULATION_NO_AI":
        mode_label = "Offline simulation · prepared fixtures, no AI"
    elif mode == "live_google_adk":
        mode_label = "Live Gemini · Google ADK"
    else:
        mode_label = "Execution mode not verified"
    return {
        "run_id": report.get("run_id"),
        "student_id": str(report.get("student_id", "unknown")),
        "status": str(report.get("status", "unknown")),
        "decision": str(report.get("decision", "unknown")),
        "decision_label": DECISION_LABELS.get(
            str(report.get("decision", "unknown")), "Teacher review required"
        ),
        "mark": result["proposed_mark"] if valid_mark else None,
        "maximum": result["maximum_mark"] if valid_mark else None,
        "criteria": result.get("criterion_results", []) if valid_mark else [],
        "explanation": result.get("explanation", "") if valid_mark else "",
        "feedback": report.get("feedback", ""),
        "mode": mode,
        "mode_label": mode_label,
        "teacher_approval_required": report.get("teacher_approval_required", True),
        "error": report.get("error", ""),
        "initial_validation_errors": report.get("initial_validation_errors", []),
        "verifier_validation_errors": report.get("verifier_validation_errors", []),
        "trace": report.get("trace", []),
    }


def can_show_mark(report: dict[str, Any]) -> bool:
    return summarize_report(report)["mark"] is not None
