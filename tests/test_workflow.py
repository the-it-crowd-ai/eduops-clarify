"""Workflow regressions using fixtures, with no provider calls."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from eduops_agent.offline_demo import run_demo
from eduops_agent.pipeline import invoke_agent, run_student
from eduops_agent.storage import recent_reports
from eduops_agent.validator import validate_result
from test_validator import ASSESSMENT, VALID


class OfflineWorkflowTests(unittest.TestCase):
    def test_offline_report_round_trip_and_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'audit.sqlite3'
            report = run_demo(db)
            stored = recent_reports(db)[0]
            self.assertEqual(stored['run_id'], report['run_id'])
            self.assertEqual(stored['final_result'], report['final_result'])
            self.assertEqual(stored['feedback'], report['feedback'])
            self.assertEqual(stored['execution_mode'], 'OFFLINE_SIMULATION_NO_AI')
            self.assertEqual(stored['decision'], 'corrected_invalid_first_result')
            self.assertEqual(validate_result(stored['assessment'], stored['final_result']), [])
            self.assertTrue(stored['initial_validation_errors'])
            self.assertEqual(stored['verifier_validation_errors'], [])
            self.assertTrue(stored['teacher_approval_required'])


class LiveWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_persisted_and_verifier_is_independent(self):
        from eduops_agent.agent import root_agent
        from eduops_agent.verifier_agent import verifier_agent
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'audit.sqlite3'
            with patch('eduops_agent.pipeline.load_assessment', return_value=copy.deepcopy(ASSESSMENT)), patch(
                'eduops_agent.pipeline.invoke_agent', new_callable=AsyncMock,
                side_effect=[json.dumps(VALID), json.dumps(VALID)]
            ) as invoke:
                report = await run_student('student_001', db_path=db)
            self.assertEqual(invoke.await_count, 2)
            self.assertIs(invoke.call_args_list[0].args[0], root_agent)
            self.assertIs(invoke.call_args_list[1].args[0], verifier_agent)
            independent_input = invoke.call_args_list[1].args[1].split('\n', 1)[1]
            self.assertEqual(json.loads(independent_input), ASSESSMENT)
            self.assertEqual(report['decision'], 'agreement')
            self.assertEqual(validate_result(ASSESSMENT, report['final_result']), [])
            self.assertEqual(recent_reports(db)[0]['feedback'], report['feedback'])
            for agent in (root_agent, verifier_agent):
                self.assertEqual(agent.model.retry_options.attempts, 1)

    async def test_503_stored_safely_without_retry_or_grade(self):
        class Unavailable(Exception):
            code = 503
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'audit.sqlite3'
            with patch('eduops_agent.pipeline.invoke_agent', new_callable=AsyncMock,
                       side_effect=Unavailable('sensitive-provider-detail')) as invoke:
                report = await run_student('student_001', db_path=db)
            invoke.assert_awaited_once()
            stored = recent_reports(db)[0]
            self.assertEqual(report['status'], 'error')
            self.assertEqual(stored['error_code'], '503')
            self.assertIsNone(stored['final_result'])
            self.assertIn('temporarily unavailable', stored['error'])
            self.assertIn('teacher review', stored['feedback'])
            self.assertNotIn('sensitive-provider-detail', json.dumps(stored))
            self.assertNotIn('verification_agent_called', stored['trace'])

    async def test_runner_closed_when_session_creation_fails(self):
        runner = SimpleNamespace(
            session_service=SimpleNamespace(create_session=AsyncMock(side_effect=RuntimeError('failed'))),
            close=AsyncMock(),
        )
        with patch('google.adk.runners.InMemoryRunner', return_value=runner):
            with self.assertRaises(RuntimeError):
                await invoke_agent(SimpleNamespace(name='fixture'), 'fixture')
        runner.close.assert_awaited_once()

    async def test_runner_closed_after_final_response(self):
        event = SimpleNamespace(is_final_response=lambda: True,
                                content=SimpleNamespace(parts=[SimpleNamespace(text='{}')]))
        async def events(**kwargs):
            yield event
        runner = SimpleNamespace(
            session_service=SimpleNamespace(create_session=AsyncMock()),
            run_async=events, close=AsyncMock(),
        )
        with patch('google.adk.runners.InMemoryRunner', return_value=runner):
            self.assertEqual(await invoke_agent(SimpleNamespace(name='fixture'), 'fixture'), '{}')
        runner.close.assert_awaited_once()

    async def test_timeout_is_stored_without_grade(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'audit.sqlite3'
            with patch('eduops_agent.pipeline.invoke_agent', new_callable=AsyncMock,
                       side_effect=TimeoutError) as invoke:
                report = await run_student('student_001', db_path=db)
            invoke.assert_awaited_once()
            self.assertEqual(report['error_type'], 'TimeoutError')
            self.assertEqual(recent_reports(db)[0]['status'], 'error')
            self.assertIsNone(report['final_result'])

    async def test_verifier_503_does_not_publish_initial_grade(self):
        class Unavailable(Exception):
            code = 503
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'audit.sqlite3'
            with patch('eduops_agent.pipeline.load_assessment', return_value=copy.deepcopy(ASSESSMENT)), patch(
                'eduops_agent.pipeline.invoke_agent', new_callable=AsyncMock,
                side_effect=[json.dumps(VALID), Unavailable('provider unavailable')]
            ) as invoke:
                report = await run_student('student_001', db_path=db)
            self.assertEqual(invoke.await_count, 2)
            self.assertIn('verification_agent_called', report['trace'])
            self.assertEqual(recent_reports(db)[0]['error_code'], '503')
            self.assertIsNone(report['final_result'])
