"""Streamlit interaction regressions without credentials, API calls or DB writes."""
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest


class AssessmentInterfaceTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict('os.environ', {
            'GOOGLE_API_KEY': 'unused-test-placeholder',
            'EDUOPS_LIVE_PASSWORD': 'test-access',
            'EDUOPS_GEMINI_MODEL': 'gemini-3.5-flash-lite',
        })
        env.start()
        self.addCleanup(env.stop)

    def workspace(self):
        # Avoid reading hosted secrets during interface checks.
        with patch.dict('os.environ', {
            'GOOGLE_API_KEY': 'unused-test-placeholder',
            'EDUOPS_LIVE_PASSWORD': 'test-access',
            'EDUOPS_GEMINI_MODEL': 'gemini-3.5-flash-lite',
        }):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'web_app.py')).run()
            app.sidebar.radio[0].set_value('Assess a learner').run()
        self.assertFalse(app.exception)
        return app

    def test_selection_changes_clear_previous_output(self):
        app = self.workspace()
        app.session_state['latest_report'] = {'student_id': 'student_001'}
        app.session_state['report_context'] = ('Live Gemini', 'student_001')
        app.selectbox[0].set_value('student_002').run()
        self.assertNotIn('latest_report', app.session_state)
        app.session_state['latest_report'] = {'student_id': 'student_002'}
        app.main.radio[0].set_value('Offline walkthrough').run()
        self.assertNotIn('latest_report', app.session_state)
        self.assertFalse(app.exception)

    def test_failed_rerun_clears_previous_output(self):
        app = self.workspace()
        app.main.radio[0].set_value('Offline walkthrough').run()
        app.session_state['latest_report'] = {'student_id': 'student_001'}
        app.session_state['report_context'] = ('Offline walkthrough', 'student_001')
        with patch('subprocess.run', side_effect=TimeoutError):
            app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertNotIn('latest_report', app.session_state)
        self.assertTrue(app.error)

    def test_live_requires_access_code(self):
        app = self.workspace()
        self.assertTrue(app.button[0].disabled)


if __name__ == '__main__':
    unittest.main()
