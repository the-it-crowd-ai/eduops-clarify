# EduOps Clarify — Understand Beyond the Memo

**The IT Crowd | Colleague Zero 2026 hackathon submission**

EduOps Clarify is a prototype assessment colleague for teachers. It combines
rubric-based assessment, an independent second assessment, evidence checks,
draft learner feedback, and a local audit trail. **Teachers retain responsibility
for reviewing and approving final marks.**

**Submission status:** the offline workflow is demonstrated and all **22 automated
tests passed** in the 13 November 2026 readiness check. A successful complete
live Gemini workflow remains **unverified**: the latest live attempt returned
HTTP **503 UNAVAILABLE** during assessment.

## The educational problem

A learner can understand a concept without reproducing the exact wording of a
marking memorandum. Nonstandard grammar or an ambiguous explanation can make
that understanding harder to recognise. Teachers must interpret the response,
apply the rubric consistently, explain the proposed mark, and decide when to
ask for clarification.

EduOps Clarify explores how an AI colleague can support that work while keeping
evidence, uncertainty, and teacher judgement visible.

## Our solution

The system is designed to assess demonstrated understanding against a rubric,
cite the learner's own words, and flag uncertainty for clarification or review.
A second agent assesses the original answer independently before the system
compares the proposals.

For teachers, the intended benefits are an organised second opinion, explicit
criterion-level evidence, draft feedback, and a traceable record of decisions.
For learners, the aim is to recognise meaning beyond memorised wording and
provide feedback connected to the concepts they still need to demonstrate.
These are design goals; learning outcomes, time savings, and marking accuracy
have not been measured.

## How the workflow works

```text
Question + rubric + fictional learner answer
                    |
             Assessment Agent
                    |
       Independent Verification Agent
       (receives original input, not the first grade)
                    |
       Validate and compare both proposals
                    |
       Draft feedback -> SQLite audit record
                    |
          Teacher review and approval
```

1. **Assessment Agent:** uses Google ADK and Gemini. Its `load_assessment` tool
   reads the question, rubric, and learner answer from local JSON data. Expected
   test marks are excluded from the tool's returned input. The agent is
   instructed to recognise meaning, avoid grammar penalties unless required by
   the rubric, and cite exact answer excerpts for positive awards.
2. **Independent Verification Agent:** uses a separate ADK agent and session to
   assess the same original input without seeing the first proposal. Both agents
   use Gemini; this independence of input does not guarantee independent errors.
3. **Validation and comparison:** Python checks required fields, criterion
   coverage, score bounds, arithmetic, and whether quoted evidence exists in the
   answer. Valid proposals with matching criterion awards can proceed. If the
   first output is invalid and the second is valid, the second becomes the
   provisional result with the correction recorded. Substantive disagreement
   or verifier failure requires teacher review.
4. **Feedback:** deterministic Python rules draft revision guidance from unmet
   rubric criteria, or direct the teacher to clarification or manual review.
   This step makes no additional model call.
5. **Persistence:** SQLite stores reports, validation errors, feedback, and traces
   in `results/eduops.sqlite3`. A `run_id` identifies each stored report. Runtime
   model failures are recorded as errors without a final grade.

Agent assessment statuses are `assessed`, `needs_clarification`, and
`needs_review`. Unresolved assessments use a null proposed mark. See the
[assessment contract](docs/assessment-contract.md) for the shared format.

## Technology stack

| Technology | Role |
| --- | --- |
| Python | Orchestration, validation, feedback, and command-line entry points |
| Google ADK (`google-adk==2.14.0`) | Agents, tool calling, and isolated sessions |
| Gemini | Assessment and independent verification proposals |
| SQLite via Python's `sqlite3` | Local audit persistence |
| `python-dotenv` | Private local API configuration |
| Python `unittest` | Automated tests without live Gemini requests |

## Install and configure

Run these PowerShell commands from the repository root. If the existing virtual
 environment is already configured, reuse it and skip installation.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-hackathon.txt
```

Keep the supplied fictional assessment data in `data/marking_rubric.json` and
`data/test_data.json`.

For live operation, configure `GOOGLE_API_KEY` privately in the process
environment or in the ignored `eduops_agent/.env` file. Do not commit or display
credentials. Offline demonstrations and unit tests do not require an API key or
make Gemini requests, although package imports can load local dotenv settings.

The agents read `EDUOPS_GEMINI_MODEL` if set; the code's fallback is
`gemini-3.8-flash`. Use a model available to your Google API project. The configured
live setup has not completed a successful full workflow, and API access and
quota are required for live calls.

## Run the offline demonstration

Start here for the reproducible judges' demonstration:

```powershell
.\.venv\Scripts\python.exe -m eduops_agent.offline_demo
```

**This is a fixture simulation, not live AI output.** It deliberately supplies
an invented evidence quotation, rejects that initial output, adopts a valid
independent fixture, drafts feedback, and saves the report to SQLite.

Expected highlights are:

- `mode: OFFLINE_SIMULATION_NO_AI`
- `decision: corrected_invalid_first_result`
- A proposed mark of **2/2**, feedback, and `teacher_approval_required: true`
- A new `run_id` and a trace explicitly identifying the fixture inputs

The readiness check saved and read back offline run **5**, confirming the mark,
feedback, and zero final-result structural validation errors. Subsequent runs
receive different IDs. This demonstrates the deterministic workflow and storage,
not Gemini's marking quality.

## Run automated tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The latest readiness run passed **22 tests with zero failures or errors**.
Coverage includes validation, evidence quotations, mark arithmetic, disagreements,
feedback, SQLite persistence and Windows connection cleanup, independent verifier
input, ADK runner cleanup, timeouts, and simulated provider failures.

## Run the live workflow

With private API configuration in place:

```powershell
.\.venv\Scripts\python.exe -m eduops_agent.pipeline --student student_001
```

This invokes assessment and, if that stage succeeds, independent verification.
Live calls consume API quota; assessment tool use may involve multiple model
turns. Each agent invocation has a 60-second timeout, and automatic SDK HTTP
retries are disabled.

The pipeline prints a JSON report and saves it locally. On a model failure, it
prints a safe error report and exits with code 1. Avoid rapid retries; use the
offline demonstration if the service is unavailable.

## Verified results and current limitations

| Check, as of 13 November 2026 | Result |
| --- | --- |
| Automated tests | 22 passed |
| Offline validation, correction, feedback, and storage | Demonstrated; persisted report read back successfully |
| One final live `student_001` attempt | HTTP 503 at assessment; error saved as run 6, no final grade |
| Successful complete live Assessment → Verification → Feedback → SQLite run | Unverified |

The latest provider error was `ServerError: 503 UNAVAILABLE`, with the message:

> This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.

No live verifier output was obtained in that attempt. A mocked successful
pipeline test checks orchestration and independent verifier input, but does not
establish real model performance.

Structural validation cannot determine conceptual correctness, confirm that a
clarification question is neutral, or prove that two agreeing proposals are
correct. No accuracy or learner-impact statistics are claimed. The prototype
uses fictional data; real learner deployment requires privacy review and
teacher-approved rubrics. The CLI records that teacher approval is required;
it does not implement an approval interface or update official marks.

## Teacher oversight

Teachers review the rubric, learner evidence, both proposals, and draft feedback.
They resolve disagreements and ambiguity, decide whether clarification is
appropriate, and approve any final mark. An automatically selected proposal is
still provisional. Clarification must not automatically change an original
examination mark.

## Project guide

- [`eduops_agent/`](eduops_agent/): agent definitions, orchestration, validation,
  feedback, and storage.
- [`tests/`](tests/): automated regression tests.
- [`docs/judges-demo-guide.md`](docs/judges-demo-guide.md): presentation steps,
  persistence check, and live-service fallback for judges.
- [`docs/workflow-verification.md`](docs/workflow-verification.md): verification
  evidence and remaining uncertainties.
- [`HACKATHON_README.md`](HACKATHON_README.md): original implementation and
  integration notes; the status above reflects the later readiness checks.

Credentials, local databases, virtual environments, and generated caches are
excluded from Git. Keep secrets and real learner records out of submissions.
