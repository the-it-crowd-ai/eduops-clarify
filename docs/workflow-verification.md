# Workflow verification — 13 November 2026

The deterministic workflow and SQLite audit trail work. A complete successful
Gemini assessment plus verification remains unverified because the live service
returned HTTP 503 during assessment.

## Results

- Used the existing `.venv/Scripts/python.exe`; installed no dependencies.
- Ran `eduops_agent.offline_demo` through Python's module runner with dotenv
  loading mocked out. Runs 1 and 2 were stored in `results/eduops.sqlite3`.
- Run 2: `OFFLINE_SIMULATION_NO_AI`, `corrected_invalid_first_result`, proposed
  mark 2/2, feedback present, teacher approval required. The invented initial
  quotation was rejected and the independent fixture passed validation.
- Read reports back through `recent_reports`; both offline final results passed
  `validate_result` with zero errors. Tests also compare persisted feedback and
  final results against the returned report.
- An initial pipeline attempt with dotenv disabled failed without process
  credentials; run 3 records a controlled error, no grade, and teacher review.
- After explicit authorization for private application loading of `.env`, ran
  the existing pipeline for `student_001`. Gemini returned `ServerError`, HTTP
  503. Run 4 stores a safe unavailable message, no final result, teacher-review
  feedback, and a trace stopping at assessment. CLI exit code 1 is expected.
  No subsequent live retry was made.
- All 22 unit tests passed (the original 15 plus 7 workflow regressions).
  Tests ran with `dotenv.load_dotenv` mocked out, without API calls.

## Implementation

- Both agents use ADK's Gemini model with `HttpRetryOptions(attempts=1)`:
  one HTTP attempt, no automatic SDK retries. Each agent invocation has a
  60-second timeout. ADK tool use may require additional model turns; this
  setting bounds retries per HTTP request, not the number of tool turns.
- ADK runners close in `finally`, including failed session creation.
- Runtime failures persist controlled error messages rather than raw provider
  text, with a numeric HTTP status when available. Both assessment and verifier
  failures produce no final grade and include teacher-review feedback.
- The offline demo exposes a callable `run_demo(db_path)` for isolated testing
  and prints its status, proposed mark, feedback, and approval requirement.

## Assessment contract review

`docs/assessment-contract.md` was reviewed and left unchanged. The offline final
assessment contains all eight required fields, matching student/question IDs,
an integer proposed mark equal to the criterion sum, correct maximum, valid
status, criterion bounds, exact learner evidence, explanation, and a null
clarification question. The report envelope adds audit/feedback metadata; its
runtime `error` status is not an Assessment Agent output and is never presented
as a contract-valid grade.

The invalid initial fixture is intentionally retained for audit, with validation
errors. Only the valid independent fixture becomes the proposed final result.
Both agent prompts require teacher review and neutral clarification. The verifier
receives only the original assessment input, not the initial grade; this is
covered by a mocked successful pipeline test.

The contract example capitalizes `Same` in C2 evidence although its input uses
`same`. The existing validator requires exact substrings and would reject that
example quote. This documentation discrepancy is recorded here without changing
the shared contract.

## Remaining unverified

- Successful real Gemini assessment, independent verification, and feedback in
  one live run; the 503 occurred before a successful assessment response.
- Real model conceptual correctness, neutrality of clarification questions,
  rubric approval, and teacher acceptance. Structural validation and fixture
  tests do not prove these qualities.
- Live verifier failure was tested with a simulated 503, not a second provider
  call. Timeout behavior is regression tested using a simulated timeout.

After the service recovers, run one fresh pipeline attempt using the existing
virtual environment:

```powershell
.\.venv\Scripts\python.exe -m eduops_agent.pipeline --student student_001
```

For the fixture demonstration:

```powershell
.\.venv\Scripts\python.exe -m eduops_agent.offline_demo
```

No keys were printed or modified, no framework changes were made, and nothing
was pushed to GitHub. `.env` was loaded privately by the application only after
authorization for the live test.

## Final readiness recheck — 13 November 2026

Ran the exact virtual-environment unittest discovery command: **22 passed**, no
failures or errors. Ran the offline module directly: saved run **5**; read-back
confirmed a 2/2 proposal, feedback, and zero final-result contract errors.

Made one live attempt with the existing private API configuration. Saved run
**6**, `ServerError`, HTTP **503 UNAVAILABLE**, at the assessment stage. The
provider message was: “This model is currently experiencing high demand. Spikes
in demand are usually temporary. Please try again later.” No final grade,
verification call, or subsequent retry. Successful complete live operation
remains unverified.

Checked Git ignore rules and tracked-file names without displaying secrets.
Existing `.env`, results, bytecode, and virtual-environment exclusions work.
Added explicit SQLite/sidecar exclusions and an exclusion for a discovered
PowerShell module cache. No matching secrets/databases/cache files were tracked.
Prepared `docs/judges-demo-guide.md` for 14 November. No runtime feature changes,
framework changes, commits, or pushes were made during this readiness check.
