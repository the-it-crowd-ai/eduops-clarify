# EduOps Clarify â€” Hackathon implementation patch

**Made for The IT Crowd.** Built as new hackathon-day code for review and integration into the existing private repository; not uploaded or tested on your private GitHub. It is not a claim that the full live workflow has passed.

## What this adds

- `eduops_agent/agent.py`: Google ADK Assessment Agent, uses `load_assessment` **tool** (local rubric/answer file read).
- `eduops_agent/verifier_agent.py`: separate Google ADK Verification Agent, makes a *fresh independent assessment* with no access to the first agent's mark.
- `eduops_agent/validator.py`: deterministic checks for malformed outputs, duplicated rubric criteria, mark arithmetic and invented evidence quotes.
- `eduops_agent/pipeline.py`: orchestrates **assess -> independently verify -> compare/repair or escalate -> feedback -> SQLite audit log**.
- `eduops_agent/feedback.py`: targeted draft feedback for teacher review.
- `eduops_agent/storage.py`: SQLite persistence in `results/eduops.sqlite3` (do NOT commit real student records).
- `tests/`: 15 local tests of structural validation, correction, disagreements, feedback and persistence.

## Important limits

- **The final mark is never automatic.** Teachers must approve scores and any clarifications.
- **Substantive disagreement is flagged for review**, not silently overwritten.
- When the first agent produces demonstrably invalid output and the verifier's output is structurally valid, the pipeline replaces the first proposal with a corrected, *still provisional* one and logs why.
- The validator checks whether a quoted substring really exists in the answer; it does **not** prove the student understands the concept. That's why we use the independent Verification Agent and teacher oversight.
- A model 503 will be logged as `status: error`, not misrepresented as completed grading.
- The two-agent live workflow **has not been tested against your Gemini key** by the author; models and usage limits depend on your Google AI Studio account. The default model is `gemini-3.8-flash`, the one that previously worked in your connection test, but it later returned `503`. A different available Gemini model can be selected with `EDUOPS_GEMINI_MODEL` environment variable after checking its availability.

## Merge into your existing Windows VS Code repository

**Before copying, save any changes in your open VS Code files.** This package intentionally includes an updated `eduops_agent/agent.py`, `assessment_tools.py`, and `__init__.py`. Copying replaces those files. It never contains or overwrites your `.env`, `data/` files, Git history, or Python `.venv`.

1. Download `eduops_hackathon_patch.zip` from ChatGPT.
2. Place it inside `C:\Users\gomom\Documents\eduops-clarify` (your repository root).
3. In the VS Code PowerShell terminal **in that folder**, run:

```powershell
Expand-Archive .\eduops_hackathon_patch.zip -DestinationPath . -Force
```

4. Make sure the root `.gitignore` also includes these lines (add only if missing):

```gitignore
.env
.venv/
__pycache__/
results/
```

5. Confirm the data files from your earlier work are still in the root `data/` folder. Don't share `eduops_agent/.env` with anyone.
6. You already installed `google-adk==2.14.0`, so there is no need to reinstall if it is working. If needed, use:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-hackathon.txt
```

7. Run **offline tests** first (no Gemini API cost):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

8. Run the **real two-agent workflow** on your fictional test student:

```powershell
.\.venv\Scripts\python.exe -m eduops_agent.pipeline --student student_001
```

It calls Gemini twice: assessment and independent verification. This consumes API quota. If the model returns `503`, the program prints an error report and saves a trace in `results/eduops.sqlite3`. Don't retry rapidly.

9. If Google's model is overloaded, you can still test the validation, correction and SQLite audit trail WITHOUT Gemini:

```powershell
.\.venv\Scripts\python.exe -m eduops_agent.offline_demo
```

This is explicitly marked **OFFLINE SIMULATION ONLY**. It uses hardcoded fixture outputs and must never be presented as a live autonomous multi-agent result.

10. For exploratory interactive testing, use:

```powershell
.\.venv\Scripts\adk.exe run eduops_agent
```

At `[user]:` type `Assess student_001 using the rubric. Return JSON.`

11. After testing, review `git status`, check no secrets or database files are tracked (`results/.gitignore` in this package ignores SQLite files), then commit the hackathon-day work with a truthful message, e.g. `git add eduops_agent tests HACKATHON_README.md requirements-hackathon.txt` followed by `git commit -m "Build hackathon assessment verification workflow"`. Do not push until the team agrees on the branch and code review.

## Demo success conditions

- Offline unit tests pass.
- One real `student_001` assessment returns valid JSON and rubric quote evidence.
- Independent verifier makes a separately logged proposal.
- The final report records agreement, deterministic repair, or disagreement requiring teacher review.
- SQLite stores traceability; teacher feedback is draft only.
- Expand to the other fictional answers after one live success.

## Compliance

The organisers clarified that the existing repo/environment can stay while rebuilding the actual agent during hackathon hours. This patch is newly authored build content; preserve truthful commit history. No `GOOGLE_API_KEY`, real learner details or `.env` files are included.
