# Judges' demonstration guide — 14 November 2026

Ready for an offline demonstration. Successful live Gemini assessment and
verification remain unverified because the final readiness attempt returned 503.
No application features or frameworks were changed during this readiness check.

## Preparation

Open PowerShell in `C:\Users\gomom\Documents\eduops-clarify`. Use the existing
virtual environment and secure API configuration. Do not display `.env` or
provider debug logs on the shared screen. Use fictional `student_001` only.

Suggested introduction: “EduOps Clarify proposes rubric-based marks, asks an
independent agent to assess the same answer, checks the outputs, drafts feedback,
and records an audit trail. Teachers approve every final decision.”

## 1. Show automated checks (about one minute)

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The 13 November readiness check passed exactly **22 tests**, with zero failures
or errors. Tests cover structural validation, evidence, mark arithmetic,
disagreement, independent verifier input, feedback, SQLite round trips,
Windows connection cleanup, runner cleanup, timeouts, and simulated 503 failures.
These unit tests do not make Gemini requests.

## 2. Demonstrate the deterministic workflow (about two minutes)

```powershell
.\.venv\Scripts\python.exe -m eduops_agent.offline_demo
```

Say explicitly: “This is an offline fixture simulation, not live agent output.”
Point to:

- `OFFLINE_SIMULATION_NO_AI` and the fixture-labelled trace.
- Rejection of the deliberately invented evidence quote.
- `corrected_invalid_first_result`: a valid independent fixture replaces the
  invalid initial proposal, with the reason retained for audit.
- Proposed mark **2/2**, draft feedback, and `teacher_approval_required: true`.
- The returned `run_id`, which identifies the saved SQLite audit record.

The readiness demonstration saved **run 5** in `results/eduops.sqlite3` and read
it back successfully: 2/2 proposal, feedback present, zero contract validation
errors. New demonstrations create new run IDs.

## 3. Prove persistence (about one minute)

```powershell
.\.venv\Scripts\python.exe -c "import json; from eduops_agent.storage import recent_reports; r = next(r for r in recent_reports(limit=100) if r['execution_mode']=='OFFLINE_SIMULATION_NO_AI'); print(json.dumps({k:r[k] for k in ('run_id','created_at','execution_mode','decision','final_result','feedback','teacher_approval_required')}, indent=2))"
```

Match this run ID to the offline demonstration. Explain that stored initial and
independent outputs, validation errors, and trace support later teacher review.
The database and generated files stay local and are excluded from Git.

## 4. Optional live demonstration (allow up to two minutes)

```powershell
.\.venv\Scripts\python.exe -m eduops_agent.pipeline --student student_001
```

Make one attempt. Each agent invocation has a 60-second timeout. HTTP retries
are disabled; tool use may still require multiple model turns.

On success, show the initial and independent assessments, validation errors,
decision, feedback, trace, and run ID. The verifier receives the original answer
and rubric, not the first agent's grade. Disagreement requires teacher review.

On failure, show the safe error report and stored run ID, then return to the
offline demonstration. Do not repeatedly retry or claim the fixture proves live
model behavior. CLI exit code 1 is expected for a failed live assessment.

The single final readiness attempt on 13 November saved **run 6**, failing at
assessment with `ServerError`, HTTP **503**, status **UNAVAILABLE**. Exact
provider message, checked for secrets:

> This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.

It produced no grade, did not proceed to verification, and stored teacher-review
feedback. No subsequent live retry was made.

## Closing explanation and limitations

The offline validation, correction, feedback, and audit path is demonstrated.
A mocked successful pipeline also verifies independent verifier input. A
successful complete live Gemini run is still unverified. Structural checks do
not establish conceptual marking accuracy or neutral clarification quality;
teachers must approve the rubric and proposed marks.

The shared contract is unchanged. Its example C2 quote starts with `Same` while
the sample answer uses `same`; the exact-evidence validator would reject that
example quotation. Actual offline final output passes the validator.

## Git readiness

Verified `.env` at root and in `eduops_agent/`, SQLite databases and sidecars,
Python bytecode/caches, the virtual environment, and the generated PowerShell
module cache are ignored. `git ls-files` found no tracked `.env`, local SQLite
or `.db` files, bytecode, results files, or that generated module cache.
Source code and documentation still require normal review and committing; no
commit or GitHub push was performed by this check.
