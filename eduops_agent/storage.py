"""SQLite audit log. Only fictional test data until privacy review."""

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "results" / "eduops.sqlite3"


def save_report(report: dict, db_path: Path = DEFAULT_DB) -> int:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # The connection context manages transactions; closing releases the file handle.
    with closing(sqlite3.connect(str(db_path))) as conn, conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS assessment_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            student_id TEXT NOT NULL,
            status TEXT NOT NULL,
            report_json TEXT NOT NULL
        )""")
        cur = conn.execute(
            "INSERT INTO assessment_runs(created_at, student_id, status, report_json) VALUES (?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                str(report.get("student_id", "unknown")),
                str(report.get("status", "error")),
                json.dumps(report, ensure_ascii=False),
            ),
        )
        return int(cur.lastrowid)


def recent_reports(db_path: Path = DEFAULT_DB, limit: int = 20) -> list[dict]:
    if not Path(db_path).exists():
        return []
    # The connection context manages transactions; closing releases the file handle.
    with closing(sqlite3.connect(str(db_path))) as conn, conn:
        rows = conn.execute(
            "SELECT id, created_at, report_json FROM assessment_runs ORDER BY id DESC LIMIT ?",
            (max(1, min(int(limit), 100)),),
        ).fetchall()
    return [dict(json.loads(payload), run_id=run_id, created_at=created_at)
            for run_id, created_at, payload in rows]
