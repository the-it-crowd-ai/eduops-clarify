"""ADK two-agent assessment -> verification -> feedback -> SQLite.

Run from repository root:
  .\\.venv\\Scripts\\python.exe -m eduops_agent.pipeline --student student_001

No expected marks are ever given to either agent.
"""

import argparse
import asyncio
import json
import re
import uuid

from dotenv import load_dotenv

from .assessment_tools import load_assessment
from .feedback import suggest_feedback
from .storage import DEFAULT_DB, save_report
from .validator import criterion_signature, validate_result


def parse_json(text: str) -> dict:
    """Accept raw JSON and one fenced JSON block; reject extra commentary."""
    cleaned = text.strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.S | re.I)
    if fence:
        cleaned = fence.group(1).strip()
    value = json.loads(cleaned)
    if not isinstance(value, dict):
        raise ValueError("Agent response is not a JSON object")
    return value


async def invoke_agent(agent, message: str) -> str:
    """Run an ADK agent in a fresh, isolated session."""
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    app_name = f"eduops_{agent.name}"
    runner = InMemoryRunner(agent=agent, app_name=app_name)
    session_id = uuid.uuid4().hex
    try:
        await runner.session_service.create_session(
            app_name=app_name, user_id="fictional_demo", session_id=session_id
        )
        final_text = None
        request = types.Content(role="user", parts=[types.Part(text=message)])
        async for event in runner.run_async(
            user_id="fictional_demo", session_id=session_id, new_message=request
        ):
            if event.is_final_response() and event.content:
                parts = [p.text for p in (event.content.parts or []) if getattr(p, "text", None)]
                if parts:
                    final_text = "\n".join(parts)
        if not final_text:
            raise RuntimeError(f"Agent {agent.name} produced no final text")
        return final_text
    finally:
        await runner.close()


def reconcile(assessment: dict, draft: dict, independent: dict) -> dict:
    """Only auto-adopt verifiably valid repair of an *invalid* initial output.

    A substantive disagreement is flagged for human review, never silently
    changed to a different learner mark.
    """
    a_errors = validate_result(assessment, draft)
    b_errors = validate_result(assessment, independent)
    trace = ["assessment_agent_called", "verification_agent_called",
             "deterministic_validation_completed"]
    decision = "needs_review"
    final_result = None

    if not a_errors and not b_errors:
        if criterion_signature(draft) == criterion_signature(independent):
            final_result = draft
            decision = "agreement"
            trace.append("independent_assessments_agree")
        else:
            decision = "disagreement_requires_teacher"
            trace.append("independent_assessments_disagree")
    elif a_errors and not b_errors:
        # Deterministic repair: the first answer is structurally invalid or
        # cites non-existent evidence. The independently valid result replaces
        # that invalid draft; this is a PROPOSAL, not an official changed mark.
        final_result = independent
        decision = "corrected_invalid_first_result"
        trace.append("invalid_initial_result_replaced_with_valid_independent_result")
    elif not a_errors and b_errors:
        decision = "verifier_failed_validation"
        trace.append("independent_verifier_output_invalid")
    else:
        decision = "both_agents_failed_validation"
        trace.append("both_outputs_invalid")

    return {
        "student_id": assessment["student_id"],
        "question_id": assessment["question_id"],
        "status": final_result["status"] if final_result else "needs_review",
        "decision": decision,
        "assessment": assessment,
        "initial_result": draft,
        "independent_result": independent,
        "initial_validation_errors": a_errors,
        "verifier_validation_errors": b_errors,
        "final_result": final_result,
        "feedback": suggest_feedback(assessment, final_result or {"status": "needs_review"}),
        "trace": trace,
        "teacher_approval_required": True,
        "execution_mode": "live_google_adk",
    }


async def run_student(student_id: str, *, db_path=DEFAULT_DB) -> dict:
    load_dotenv("eduops_agent/.env")
    assessment = load_assessment(student_id)
    if "error" in assessment:
        return {"student_id": student_id, "status": "error",
                "error": assessment["error"], "execution_mode": "local_error"}

    trace = ["workflow_started"]
    try:
        from .agent import root_agent
        from .verifier_agent import verifier_agent

        trace.append("assessment_agent_called")
        draft_text = await asyncio.wait_for(invoke_agent(
            root_agent,
            f"Use load_assessment to assess student ID {student_id}. "
            "Return only the complete JSON assessment proposal."
        ), timeout=60)
        draft = parse_json(draft_text)

        # The verifier receives only the underlying question + rubric + learner
        # answer. It does not see the first grade, preventing anchoring.
        trace.append("verification_agent_called")
        verifier_text = await asyncio.wait_for(invoke_agent(
            verifier_agent,
            "Independently assess this fictional learner. Return only JSON.\n"
            + json.dumps(assessment, ensure_ascii=False)
        ), timeout=60)
        verified = parse_json(verifier_text)
        report = reconcile(assessment, draft, verified)
    except Exception as exc:
        # Provider exception text can contain credentials or request details.
        # Store only a controlled message and a numeric HTTP status.
        code = getattr(exc, "code", None)
        code = int(code) if isinstance(code, (str, int)) and str(code).isdigit() else None
        unavailable = code == 503
        report = {
            "student_id": student_id,
            "question_id": assessment["question_id"],
            "status": "error", "decision": "model_or_runtime_failed",
            "error_type": type(exc).__name__,
            "error": ("Gemini is temporarily unavailable. Try again later."
                      if unavailable else "Assessment could not complete. Teacher review is required."),
            "trace": trace + ["workflow_interrupted"],
            "execution_mode": "live_google_adk",
            "final_result": None,
            "feedback": suggest_feedback(assessment, {"status": "needs_review"}),
            "teacher_approval_required": True,
        }
        if code is not None:
            report["error_code"] = str(code)

    report["run_id"] = save_report(report, db_path)
    return report


def main():
    parser = argparse.ArgumentParser(description="EduOps Clarify two-agent formative assessment")
    parser.add_argument("--student", default="student_001", help="Fictional student ID")
    args = parser.parse_args()
    report = asyncio.run(run_student(args.student))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
