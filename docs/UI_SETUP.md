# EduOps Clarify web workspace — installation and deployment

**This is an additive UI patch, not a replacement project.** It has no `.env`, no API keys, and no learner data. Do not overwrite existing `eduops_agent` files or your updated root README.

## Install on Windows

1. Back up or commit your working branch first. Extract `EduOps_Clarify_Teacher_Workspace_UI.zip` **into the existing project root** (`C:\Users\gomom\Documents\eduops-clarify`) with `Expand-Archive -Path ... -DestinationPath . -Force`.
2. In the already-active VS Code project PowerShell terminal, install the UI's dependencies:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Choose a *separate* demo access password for live Gemini calls. Never use or share your Gemini API key as this password:

   ```powershell
   $env:EDUOPS_LIVE_PASSWORD = 'choose-your-own-demo-password'
   $env:EDUOPS_GEMINI_MODEL = 'gemini-3.5-flash-lite'
   ```

4. Start the app from the repository root:

   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run web_app.py
   ```

5. Open `http://localhost:8501` in your browser (Streamlit prints its local address in the terminal). The home page requires no API key. To test the existing offline sample, open **Assess a learner → Offline walkthrough → Run offline walkthrough**. To test live, switch to **Live Gemini**, enter the demo password, then run one fictional assessment.
6. Test all project tests (including the six new UI logic tests):

   ```powershell
   .\.venv\Scripts\python.exe -m unittest discover -s tests -v
   ```

   At the time the patch was created, 22 pre-existing tests had been reported passing by the project owner. This new patch's own tests have been checked separately; the complete local app must be tested on the owner's current code before a deployment claim.

## Deployment to Streamlit Community Cloud

- Commit and push this **reviewed UI patch** to `hackathon-build`; do not commit `.env`, API keys, `.streamlit/secrets.toml`, SQLite files or test result data.
- In `https://share.streamlit.io`, link GitHub (you may need private-repo permission and organisation approval). The deployment account needs admin permission to the repository.
- Create the app with repository `the-it-crowd-ai/eduops-clarify`, branch `hackathon-build`, entrypoint `web_app.py`.
- Configure app secrets through **Advanced settings / Secrets**, not in Git:

  ```toml
  GOOGLE_API_KEY = "YOUR_API_KEY_HERE"
  EDUOPS_GEMINI_MODEL = "gemini-3.5-flash-lite"
  EDUOPS_LIVE_PASSWORD = "YOUR_SEPARATE_DEMO_PASSWORD_HERE"
  ```

  Enter *real values privately in the Streamlit dashboard*, not in any chat or repo file. This is a **template only**.
- Deploy; open the resulting `*.streamlit.app` URL and test the **offline walkthrough first**, then one limited live request. The code cannot guarantee Google's availability.
- Cloud SQLite storage is temporary; reports may be lost when the app sleeps or redeploys. Do **not** use real learner data or assume persistence.
- **Security:** A single shared password is a demo convenience, not production-grade access control or rate limiting. Do not publish the password with the link. If you make the app public, monitor your Gemini quota or disable live mode. Cloud secrets must remain private.

## What not to assume

- This UI has *not* been deployed by ChatGPT or verified running against your latest private GitHub files.
- It currently supports fictional sample IDs from `data/test_data.json`; changing the answer on-screen is intentionally not supported until the ADK pipeline supports arbitrary inputs safely.
- No extra agent is created by this UI. The verified build has **two** independent AI agents.
- No fully autonomous teacher grading or permanent database is claimed.
