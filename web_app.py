"""EduOps Clarify — teacher-first Streamlit workspace.

This is an additive frontend. It uses the existing Google ADK pipeline,
existing offline_demo module, existing test fixtures, and existing SQLite log.
No secret is stored in source code. Use only fictional demo records.

Run from the repository root: python -m streamlit run web_app.py
"""
from __future__ import annotations

import asyncio
import hmac
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import streamlit as st

from eduops_ui.logic import list_fictional_students, summarize_report
from eduops_agent.assessment_tools import load_assessment
from eduops_agent.storage import recent_reports

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "test_data.json"
STYLE = ROOT / "eduops_ui" / "assets" / "style.css"

st.set_page_config(
    page_title="EduOps Clarify · Teacher workspace",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"About": "EduOps Clarify by The IT Crowd. Demo uses fictional learner data only."},
)


def h(text: Any) -> str:
    return html.escape(str(text), quote=True)


def load_secrets() -> None:
    """Read Streamlit-hosted secrets without printing them or editing .env."""
    for name in ("GOOGLE_API_KEY", "EDUOPS_GEMINI_MODEL", "EDUOPS_LIVE_PASSWORD"):
        if os.environ.get(name):
            continue
        try:
            if name in st.secrets:
                os.environ[name] = str(st.secrets[name])
        except Exception:
            # Streamlit may raise StreamlitSecretNotFoundError on local machines
            # with no secrets.toml; the app should still load offline.
            pass
    # This is the model that previously completed a live two-agent sample.
    os.environ.setdefault("EDUOPS_GEMINI_MODEL", "gemini-3.5-flash-lite")


def offline_report() -> dict:
    """Run the EXISTING clearly labelled offline simulation, then read its audit row."""
    env = dict(os.environ)
    # Prevent accidental API access from this offline subprocess.
    env.pop("GOOGLE_API_KEY", None)
    env.pop("GEMINI_API_KEY", None)
    proc = subprocess.run(
        [sys.executable, "-m", "eduops_agent.offline_demo"],
        cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("Offline demonstration could not finish. Check the terminal logs.")
    matches = re.findall(r'"run_id"\s*:\s*(\d+)', proc.stdout)
    if not matches:
        raise RuntimeError("Offline demonstration completed without a readable audit ID.")
    run_id = int(matches[-1])
    for report in recent_reports(limit=100):
        if report.get("run_id") == run_id:
            if report.get("execution_mode") != "OFFLINE_SIMULATION_NO_AI":
                raise RuntimeError("Expected a labelled offline simulation audit report.")
            return report
    raise RuntimeError("Could not read the offline report back from SQLite.")


def live_report(student_id: str) -> dict:
    """Invoke the project's tested ADK pipeline, not a UI-created fake agent."""
    from eduops_agent.pipeline import run_student

    return asyncio.run(run_student(student_id))


def go(page: str) -> None:
    st.session_state["next_page"] = page
    st.rerun()


def top(label: str, heading: str, description: str | None = None) -> None:
    st.markdown(f'<div class="edu-kicker">{h(label)}</div>', unsafe_allow_html=True)
    st.title(heading)
    if description:
        st.write(description)


def details_panel(assessment: dict) -> None:
    if assessment.get("error"):
        st.error(assessment["error"])
        return
    criteria = []
    for criterion in assessment.get("rubric", []):
        points = criterion.get("points", 0)
        criteria.append(
            '<div class="edu-rubric-row"><strong>' + h(criterion.get("id", "")) +
            '<span class="edu-rubric-points">' + h(points) + ' mark' +
            ('s' if points != 1 else '') + '</span></strong><span>' +
            h(criterion.get("description", "")) + '</span></div>'
        )
    st.markdown(
        '<section class="edu-input-section edu-question-section" aria-label="Question">'
        '<h3 class="edu-input-label">Question</h3><div class="edu-question-text">' +
        h(assessment.get("question", "Question unavailable")) + '</div></section>'
        '<section class="edu-input-section edu-answer-section" aria-label="Learner answer">'
        '<h3 class="edu-input-label">Learner answer</h3><blockquote class="edu-answer-text">' +
        h(assessment.get("student_answer", "")) + '</blockquote></section>'
        '<section class="edu-input-section edu-rubric-section" aria-label="Marking criteria">'
        '<h3 class="edu-input-label">Marking criteria</h3>' + ''.join(criteria) + '</section>',
        unsafe_allow_html=True,
    )


def report_panel(report: dict) -> None:
    summary = summarize_report(report)
    st.caption(summary["mode_label"])
    if summary["status"] == "error":
        st.error("Assessment could not complete. No proposed mark is available.")
        if report.get("error_code") == "503":
            st.info("Gemini is temporarily unavailable (503). Retry later or choose the offline walkthrough.")
        elif report.get("error_type") in ("TimeoutError", "AsyncTimeoutError"):
            st.info("Gemini timed out. Retry later or choose the offline walkthrough.")
    elif summary["mark"] is not None:
        st.markdown(
            '<div class="edu-score"><div class="edu-score-label">Proposed mark - not final</div>'
            '<div class="edu-score-num">' + h(summary["mark"]) + '<span class="edu-score-max"> / ' +
            h(summary["maximum"]) + '</span></div></div>', unsafe_allow_html=True,
        )
        st.success("Verification: " + summary["decision_label"])
    else:
        st.warning("Verification: " + summary["decision_label"])
        st.caption("No proposed mark is available. Review or clarification is needed.")

    if summary["feedback"]:
        st.markdown('#### Feedback for the learner')
        st.write(summary["feedback"])
    if summary["criteria"]:
        st.markdown('#### Criterion evidence')
        rows = ''.join(
            '<tr><th scope="row">' + h(row.get("criterion_id", "Criterion")) + '</th><td>' +
            h(row.get("awarded_points", 0)) + '</td><td>' +
            h(row.get("evidence") or "No evidence quoted for this criterion.") + '</td></tr>'
            for row in summary["criteria"] if isinstance(row, dict)
        )
        st.markdown('<table class="edu-evidence" aria-label="Criterion evidence">'
                    '<thead><tr><th scope="col">Criterion</th><th scope="col">Points</th>'
                    '<th scope="col">Quoted evidence</th></tr></thead><tbody>' + rows +
                    '</tbody></table>', unsafe_allow_html=True)
    if summary["explanation"]:
        with st.expander("Why this mark was proposed", expanded=False):
            st.write(summary["explanation"])
    st.markdown("#### Awaiting teacher review")
    st.write("Review the evidence before recording a final grade.")
    with st.expander("Technical validation and audit trail", expanded=False):
        if summary["run_id"] is not None:
            st.caption("Audit record #" + str(summary["run_id"]))
        st.write("Initial validation issues:", summary["initial_validation_errors"] or "None")
        st.write("Verification validation issues:", summary["verifier_validation_errors"] or "None")
        st.write("Workflow steps:", summary["trace"] or "Not available")
        st.download_button(
            "Download audit JSON", data=json.dumps(report, ensure_ascii=False, indent=2),
            file_name=f"eduops-run-{summary['run_id'] or 'report'}.json",
            mime="application/json", use_container_width=True,
        )


def overview_page() -> None:
    top("Teacher workspace", "Ready to assess?")
    st.write("Choose a learner. Run the assessment. Review the evidence.")
    if st.button("Start an assessment", type="primary", use_container_width=True):
        go("Assess a learner")
    st.caption("Fictional demo learners only. Every proposed grade needs teacher review.")
    with st.expander("What happens when I run an assessment?", expanded=False):
        st.write("An Assessment Agent proposes a mark. An independent Verification Agent checks the same answer. You review the evidence and make the final decision.")
        st.write("Offline walkthrough uses prepared examples without AI calls.")


def assess_page() -> None:
    st.title("Assess a learner")
    with st.container(border=True):
        mode_col, learner_col, action_col = st.columns([1.25, 1, 1.15], gap="medium")
        with mode_col:
            mode = st.radio("Assessment mode", ["Live Gemini", "Offline walkthrough"],
                            key="assessment_mode", on_change=clear_assessment,
                            help="Offline uses prepared fixtures, never an AI response.")
        options = ["student_001"] if mode == "Offline walkthrough" else list_fictional_students(DATA)
        if not options:
            st.error("No fictional test cases were found. Confirm data/test_data.json is in the repository.")
            return
        with learner_col:
            selected = st.selectbox("Fictional learner", options=options, key="selected_learner",
                                    on_change=clear_assessment)
        assessment = load_assessment(selected)
        context = (mode, selected)
        if st.session_state.get("report_context") != context:
            clear_assessment()
        with action_col:
            allowed = True
            count = st.session_state.get("live_count", 0)
            if mode == "Live Gemini":
                password = os.getenv("EDUOPS_LIVE_PASSWORD", "")
                entered = st.text_input("Access code", type="password",
                                        help="Separate demo password; never enter an API key.")
                allowed = bool(password and entered) and hmac.compare_digest(entered, password)
                if not password:
                    st.warning("Live mode is locked. Configure EDUOPS_LIVE_PASSWORD to enable it.")
                elif entered and not allowed:
                    st.error("Access code not recognised.")
                if count >= 2:
                    st.warning("Session limit reached (two live attempts).")
            run_clicked = st.button("Run assessment" if mode == "Live Gemini" else "Run offline walkthrough",
                                    type="primary", use_container_width=True,
                                    disabled=not allowed or (mode == "Live Gemini" and count >= 2)
                                    or "error" in assessment)
        if mode == "Offline walkthrough":
            st.caption("Offline simulation: prepared example, no AI.")
        else:
            st.caption(f"Live Gemini: {max(0, 2 - count)} of 2 attempts remaining.")

    left, right = st.columns([1, 1.15], gap="medium")
    with left:
        with st.container(border=True):
            details_panel(assessment)
    with right:
        with st.container(border=True):
            st.markdown('<div class="edu-panel-header">Assessment result</div>', unsafe_allow_html=True)
            if run_clicked:
                clear_assessment()
                try:
                    if mode == "Live Gemini":
                        st.session_state["live_count"] = count + 1
                    with st.status("Assessing and checking the answer...", expanded=True) as status:
                        st.write("This may take up to two minutes." if mode == "Live Gemini"
                                 else "Loading the labelled offline simulation and audit record.")
                        report = live_report(selected) if mode == "Live Gemini" else offline_report()
                        st.session_state["latest_report"] = report
                        st.session_state["report_context"] = context
                        status.update(label="Assessment unavailable" if report.get("status") == "error"
                                      else "Assessment ready for teacher review",
                                      state="error" if report.get("status") == "error" else "complete", expanded=False)
                except Exception as exc:
                    st.error("The run could not finish safely. Retry later or check your local configuration.")
                    with st.expander("Technical failure details", expanded=False):
                        st.caption("Error type: " + type(exc).__name__)
            report = st.session_state.get("latest_report")
            expected_mode = "live_google_adk" if mode == "Live Gemini" else "OFFLINE_SIMULATION_NO_AI"
            if (report and st.session_state.get("report_context") == context
                    and report.get("execution_mode") == expected_mode and report.get("student_id") == selected):
                report_panel(report)
            elif not run_clicked:
                st.markdown('<div class="edu-empty"><strong>Ready to assess ' + h(selected) + '.</strong>'
                            '<p>Select Run assessment to begin.</p>'
                            '</div>', unsafe_allow_html=True)


def clear_assessment() -> None:
    """Discard previous output before a changed selection or a new attempt."""
    st.session_state.pop("latest_report", None)
    st.session_state.pop("report_context", None)


def history_page() -> None:
    st.title("Review history")
    try:
        reports = recent_reports(limit=40)
    except Exception:
        st.error("Could not read the local audit database.")
        return
    if not reports:
        st.info("No reports yet. Open 'Assess a learner' to generate an audit record.")
        return
    choices = {}
    for report in reports:
        info = summarize_report(report)
        runid = info["run_id"]
        label = (f"#{runid} · {info['student_id']} · "
                 f"{'Simulation' if info['mode'] == 'OFFLINE_SIMULATION_NO_AI' else 'Live / other'} · "
                 f"{info['decision_label']}")
        choices[label] = report
    selected = st.selectbox("Choose a saved run", options=list(choices))
    current = choices[selected]
    l, r = st.columns([1, 1.1], gap="large")
    with l:
        with st.container(border=True):
            st.markdown('#### Original learner response')
            original = current.get("assessment", {})
            if isinstance(original, dict) and original.get("student_answer"):
                details_panel(original)
            else:
                st.caption("Input details not present in this saved record.")
    with r:
        with st.container(border=True):
            report_panel(current)
    st.caption("SQLite on free cloud hosting is not permanent storage. For this demo, do not upload real learner data.")


def about_page() -> None:
    top("How it works", "Designed for teachers to stay in control",
        "A clear explanation of what the system does today—and what it does not claim.")
    l, r = st.columns([1, 1], gap="large")
    with l:
        with st.container(border=True):
            st.subheader("The assessment workflow")
            for n, title, desc in [
                ("01", "Assessment Agent", "Reads the sample rubric and answer. Proposes marks with exact quoted evidence."),
                ("02", "Independent Verification Agent", "Reviews the same question and answer without seeing the first proposed mark."),
                ("03", "Deterministic safeguards", "Checks mark totals, required criteria, and whether claimed quotes appear verbatim."),
                ("04", "Teacher checkpoint", "Disagreements require review. Feedback and final marks remain teacher-controlled."),
            ]:
                st.markdown('<div class="edu-step"><div class="edu-step-n">' + n + '</div><div>'
                            '<div class="edu-step-title">' + h(title) + '</div>'
                            '<div class="edu-step-detail">' + h(desc) + '</div></div></div>',
                            unsafe_allow_html=True)
    with r:
        with st.container(border=True):
            st.subheader("What you can trust")
            st.write("**Live Gemini:** Uses actual Google ADK Assessment and Verification Agent calls. Success depends on Google's availability.")
            st.write("**Offline walkthrough:** Uses prepared fixtures to demonstrate correction and persistence. It is not an AI assessment.")
            st.write("**Evidence checks:** Detect invented exact quotes and scoring inconsistencies; they do not prove conceptual accuracy.")
            st.write("**Privacy:** Uses fictional learner samples. No uploads or real learner records are supported in this demo.")
            st.divider()
            st.caption("Built by The IT Crowd for Colleague Zero 2026. Human review is required for every grade.")
    st.markdown('<div class="edu-footnote">Design references: Linear’s published, human-authored interface redesign and Khan Academy’s design-system colour guidance. All EduOps styling is original.</div>', unsafe_allow_html=True)


def main() -> None:
    load_secrets()
    st.markdown("<style>" + STYLE.read_text(encoding="utf-8") + "</style>", unsafe_allow_html=True)
    if "navigation" not in st.session_state:
        st.session_state["navigation"] = "Assess a learner"
    if st.session_state.get("next_page"):
        st.session_state["navigation"] = st.session_state.pop("next_page")
    with st.sidebar:
        st.markdown('''
          <div class="edu-brand">
          <div class="edu-logo"><span class="edu-logo-mark">✦</span>EduOps Clarify</div>
          <div class="edu-brand-small">Understand beyond the memo</div>
          </div>''', unsafe_allow_html=True)
        st.divider()
        st.radio("Workspace navigation", ["Overview", "Assess a learner", "Review history", "How it works"],
                 key="navigation", label_visibility="collapsed")
        st.divider()
        st.caption("THE IT CROWD · 2026")
        st.caption("Fictional demo records only. Final decisions belong to teachers.")
    nav = st.session_state.get("navigation", "Overview")
    if nav == "Assess a learner":
        assess_page()
    elif nav == "Review history":
        history_page()
    elif nav == "How it works":
        about_page()
    else:
        overview_page()


if __name__ == "__main__":
    main()
