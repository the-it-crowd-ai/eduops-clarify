"""Teacher-review learning suggestions; not another LLM request."""


def suggest_feedback(assessment: dict, final_result: dict) -> str:
    status = final_result.get("status")
    if status == "needs_clarification":
        return "Ask the neutral clarification question and review the response before deciding a mark."
    if status != "assessed":
        return "Manual teacher review is needed before providing individualised feedback."
    result_by_id = {x["criterion_id"]: x for x in final_result["criterion_results"]}
    unmet = [c["description"] for c in assessment["rubric"]
             if result_by_id[c["id"]]["awarded_points"] < c["points"]]
    if not unmet:
        return "The learner demonstrated all required concepts. Extend the discussion with a real-life example."
    return "Suggested revision focus: " + "; ".join(unmet) + ". Teacher to confirm before sharing."
