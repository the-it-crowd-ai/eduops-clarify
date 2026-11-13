import tempfile
import unittest
from pathlib import Path

from eduops_agent.storage import save_report, recent_reports


class StorageTests(unittest.TestCase):
    def test_sqlite_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "results.sqlite3"
            row = save_report({"student_id": "student_001", "status": "needs_review"}, db)
            self.assertEqual(row, 1)
            data = recent_reports(db)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["status"], "needs_review")
