"""Non-AI structural guardrails. These do NOT judge conceptual correctness."""

REQUIRED_FIELDS = {
    "student_id", "question_id", "proposed_mark", "maximum_mark",
    "criterion_results", "explanation", "status", "clarification_question",
}
ALLOWED_STATUSES = {"assessed", "needs_clarification", "needs_review"}


def validate_result(assessment: dict, result: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(result, dict):
        return ["Assessment output must be a JSON object"]
    for field in REQUIRED_FIELDS - set(result):
        errors.append(f"Missing required field: {field}")

    for field in ("student_id", "question_id", "maximum_mark"):
        if result.get(field) != assessment.get(field):
            errors.append(f"Incorrect {field}")

    if not isinstance(result.get("explanation"), str) or not result["explanation"].strip():
        errors.append("Missing explanation")

    status = result.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append("Invalid status")

    max_mark = assessment.get("maximum_mark")
    if type(max_mark) is not int or max_mark < 0:
        return errors + ["Invalid rubric maximum_mark"]
    if not isinstance(assessment.get("student_answer"), str):
        return errors + ["Invalid learner answer"]

    rubric: dict[str, int] = {}
    for criterion in assessment.get("rubric", []):
        if not isinstance(criterion, dict):
            return errors + ["Malformed rubric"]
        cid, cap = criterion.get("id"), criterion.get("points")
        if not isinstance(cid, str) or type(cap) is not int or cap < 0 or cid in rubric:
            return errors + ["Malformed rubric criterion"]
        rubric[cid] = cap
    if not rubric or sum(rubric.values()) != max_mark:
        return errors + ["Rubric points do not sum to the maximum"]

    items = result.get("criterion_results")
    if not isinstance(items, list):
        return errors + ["criterion_results must be a list"]

    seen: set[str] = set()
    total = 0
    for item in items:
        if not isinstance(item, dict):
            errors.append("Malformed criterion result")
            continue
        cid = item.get("criterion_id")
        if not isinstance(cid, str) or cid not in rubric:
            errors.append(f"Unknown criterion: {cid}")
            continue
        if cid in seen:
            errors.append(f"Duplicate criterion: {cid}")
        seen.add(cid)

        points, evidence = item.get("awarded_points"), item.get("evidence")
        if type(points) is not int or not 0 <= points <= rubric[cid]:
            errors.append(f"Invalid awarded_points for {cid}")
            continue
        total += points
        if not isinstance(evidence, str):
            errors.append(f"Evidence must be a string for {cid}")
        elif points > 0 and (not evidence.strip() or evidence not in assessment["student_answer"]):
            errors.append(f"Evidence for {cid} is not an exact quote")
        elif points == 0 and evidence != "":
            errors.append(f"Evidence for {cid} must be empty for zero points")

    if status == "assessed":
        if seen != set(rubric):
            errors.append("Not all rubric criteria are represented")
        if type(result.get("proposed_mark")) is not int:
            errors.append("proposed_mark must be an integer when assessed")
        elif not (0 <= result["proposed_mark"] <= max_mark):
            errors.append("proposed_mark out of range")
        elif result["proposed_mark"] != total:
            errors.append("proposed_mark does not match the sum")
        if result.get("clarification_question") is not None:
            errors.append("Assessed results must not contain a clarification question")
    elif status in {"needs_clarification", "needs_review"}:
        if result.get("proposed_mark") is not None:
            errors.append("Unresolved assessments must use a null proposed_mark")
        if status == "needs_clarification":
            q = result.get("clarification_question")
            if not isinstance(q, str) or not q.strip():
                errors.append("Neutral clarification question is required")
        elif result.get("clarification_question") is not None:
            errors.append("Review results should not include clarification questions")
        # Unresolved statuses may include zero or more criterion results, but
        # must not award points before the meaning has been resolved.
        if total > 0:
            errors.append("Unresolved assessments must not award points")

    return errors


def criterion_signature(result: dict):
    """Compare *independent* assessments without relying on prose wording."""
    if result.get("status") != "assessed":
        return (result.get("status"), None)
    rows = sorted(
        (item["criterion_id"], item["awarded_points"])
        for item in result["criterion_results"]
    )
    return ("assessed", result["proposed_mark"], tuple(rows))
