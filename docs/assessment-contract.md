# EduOps Clarify — Assessment Agent Data Contract

## Purpose

This document defines the shared data format for Phase 1 of EduOps Clarify.

All team members must use this format when preparing assessment data, writing prompts, implementing the Assessment Agent and creating tests.

## 1. Assessment Agent Input

The agent receives:
- Student ID
- Question ID and question text
- Maximum mark
- Marking rubric
- Student's written answer

Example JSON:

```json
{
  "student_id": "student_001",
  "question_id": "Q001",
  "question": "Explain what inflation means.",
  "maximum_mark": 2,
  "rubric": [
    {
      "id": "C1",
      "description": "Prices of goods and services generally increase over time.",
      "points": 1
    },
    {
      "id": "C2",
      "description": "Money loses purchasing power.",
      "points": 1
    }
  ],
  "student_answer": "Things keep getting expensive and same money can't buy much like before."
}
```

This rubric is illustrative. The team must approve the actual marking criteria before relying on them.

## 2. Assessment Agent Output

The agent must return a JSON object containing:

- `student_id`: The student's identifier.
- `question_id`: The assessed question.
- `proposed_mark`: Suggested mark, or `null` when the answer cannot yet be assessed reliably.
- `maximum_mark`: Maximum available mark.
- `criterion_results`: Mark awarded and evidence for each rubric criterion.
- `explanation`: Reason for the assessment.
- `status`: Assessment outcome.
- `clarification_question`: Neutral question if clarification is needed.

Example JSON:

```json
{
  "student_id": "student_001",
  "question_id": "Q001",
  "proposed_mark": 2,
  "maximum_mark": 2,
  "criterion_results": [
    {
      "criterion_id": "C1",
      "awarded_points": 1,
      "evidence": "Things keep getting expensive"
    },
    {
      "criterion_id": "C2",
      "awarded_points": 1,
      "evidence": "Same money can't buy much like before"
    }
  ],
  "explanation": "The response demonstrates both required concepts despite nonstandard grammar.",
  "status": "assessed",
  "clarification_question": null
}
```

## 3. Allowed Assessment Statuses

The `status` field must use one of these values:

- `assessed`: The available answer supports a proposed mark.
- `needs_clarification`: The student's meaning is unclear. Use `proposed_mark: null` and provide a neutral clarification question.
- `needs_review`: The response requires a human decision that the agent cannot reliably make.

## 4. Assessment Rules

1. Assess demonstrated understanding, not exact wording.
2. Do not penalize grammar unless the rubric explicitly requires it.
3. Award credit only for concepts supported by the student's response.
4. Never invent missing reasoning.
5. Explain every proposed mark using rubric evidence.
6. Keep awarded marks within the available criterion points.
7. Flag ambiguous responses rather than guessing.
8. Do not automatically treat clarification responses as grounds for changing an original examination mark.

## 5. Responsibilities

**Task A — Assessment Data**
Create assessment inputs following Section 1.

**Task B — Agent Instructions**
Write instructions requiring the output in Section 2 and the rules in Sections 3–4.

**Task C — Agent Implementation**
Build Python code that accepts the input and produces valid JSON output.

**Task D — Testing**
Validate the JSON structure, scoring rules and assessment behaviour against team-approved expected results.

## 6. Phase 1 Completion Criteria

Phase 1 is complete when:

- The Assessment Agent runs successfully.
- It accepts the agreed input format.
- It returns the agreed output format.
- Its responses are tested against known examples.
- Failures and limitations are documented.
- The team agrees the component is ready to integrate with a Verification Agent.

Changes to this contract must be discussed before implementation to avoid integration conflicts.
