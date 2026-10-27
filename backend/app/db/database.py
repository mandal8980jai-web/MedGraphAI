import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from app.core.config import settings
from app.core.logging import logger


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS analyses (
  id TEXT PRIMARY KEY,
  created_at TEXT,
  original_name TEXT,
  stored_name TEXT,
  file_kind TEXT,
  text_source TEXT,
  page_count INTEGER,
  extracted_text TEXT,
  medicines_json TEXT,
  context_json TEXT,
  results_json TEXT,
  status TEXT
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  analysis_id TEXT,
  run_id TEXT,
  time TEXT,
  component TEXT,
  status TEXT,
  task TEXT,
  detail TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_analysis_run ON events(analysis_id, run_id);
"""


def get_db_path() -> Path:
    db_path = settings.sqlite_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_db() -> None:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=30.0)
    try:
        conn.execute("PRAGMA busy_timeout=10000;")
        row = conn.execute("PRAGMA journal_mode;").fetchone()
        if row and str(row[0]).lower() != "wal":
            try:
                conn.execute("PRAGMA journal_mode=WAL;")
            except Exception:
                pass
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
    conn.execute("PRAGMA busy_timeout=10000;")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
