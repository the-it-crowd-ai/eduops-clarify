# EduOps Clarify — teacher-first interface decisions

## Credible, human-designed references

**Linear:** https://linear.app/now/how-we-redesigned-the-linear-ui

The March 2024 redesign is explicitly credited to the named human team Karri Saarinen, Yann-Edern Gillet, Romain Cascino and Andreas Eldh. Its authors document why they simplified sidebar navigation, treated the header and content hierarchy carefully, kept consistent space between elements, and used distinct surface elevation and contrast. We adopted **design principles**, not the site's source code, artwork, typography assets or exact visual identity.

**Khan Academy:** https://blog.khanacademy.org/how-we-rebuilt-khan-academys-color-system-from-the-ground-up/

Staff product designer Caitlyn Mayers documents a new colour architecture for Khan Academy, focusing on semantic tokens and consistent meaning. EduOps uses a distinctly original warm-neutral palette and reserves green for actionable successes, amber for review states, and neutral ink for most content.

**GOV.UK Design System:** https://design-system.service.gov.uk/

Maintained by the human design team at the Government Digital Service. Useful accessibility guardrails: explicit labels, plain language, form guidance, readable content and avoiding icon-only navigation.

## Product decisions

- Audience: teachers assessing a fictional formative learner answer; not developers monitoring agents.
- Primary flow: **Select sample → Run assessment → Review evidence → Teacher decision**.
- Navigation: four clear sections, consistent sidebar; no purposeless AI-chat interface, complex charts or multiple competing calls to action.
- Content: the question and rubric remain visible next to the result. Every proposed mark displays criterion evidence.
- Feedback: clear distinction between proposed mark and teacher-approved decision. UI does not claim a final grade was submitted.
- Modes: **Live Gemini** is genuine ADK inference; **Offline walkthrough** is clearly labelled hardcoded fixture validation (no AI).
- Error state: no invented grade on 503 or provider timeout. Prefer a useful, transparent next step.
- Trust: no real learner data, no secret in code, SQLite audit export for fictional cases.

## Original visual identity

- Primary background: warm linen `#F8F7F2`, not dashboard-black or neon-gradient.
- Reading surfaces: paper `#FFFFFF` with thin sage borders `#DEE4DC`.
- Navigation: deep forest `#183C34` for a confident but restrained anchor.
- Actions: forest-teal `#167460`; success: soft sage `#E4F2EB`; caution: honey `#F8E9C8`.
- Headings: Georgia editorial serif for large introductions; system sans-serif for controls and factual content.
- Responsive: two-column reading/review panel on desktop; Streamlit columns stack on narrow screens.
- Interaction: one primary button per decision point; all actions labelled in ordinary teacher language.

## Scope and limitations

This UI is additive and calls **existing** `eduops_agent.pipeline.run_student`, `eduops_agent.offline_demo`, `assessment_tools.load_assessment` and `storage.recent_reports`. It does not manufacture new agent logic, accept real pupil data or implement a teacher approval database. Streamlit Community Cloud's local SQLite storage is temporary. Live mode requires a separate demo access password to discourage unapproved public API usage; this is *not* full authentication or per-user billing protection.

Any future addition of arbitrary teacher-entered answers requires changing and re-testing the current fixture-ID-based agent pipeline; merely placing a text box in the UI would misrepresent functionality.
