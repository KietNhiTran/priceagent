"""
Async SQLite storage for agent traces.

Tables:
  - traces: top-level trace records
  - trace_steps: individual agent step records

Auto-creates tables on first use.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import aiosqlite

from backend.tracing.trace_models import AgentTrace, AgentStep

logger = logging.getLogger(__name__)

_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS traces (
    trace_id TEXT PRIMARY KEY,
    session_id TEXT,
    timestamp TEXT,
    total_duration_ms INTEGER,
    final_decision TEXT,
    user_message TEXT,
    decision_json TEXT
);

CREATE TABLE IF NOT EXISTS trace_steps (
    step_id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    agent_name TEXT,
    status TEXT,
    start_time TEXT,
    end_time TEXT,
    duration_ms INTEGER,
    input_summary TEXT,
    output_summary TEXT,
    inference_mode TEXT,
    raw_json TEXT,
    FOREIGN KEY (trace_id) REFERENCES traces(trace_id)
);

CREATE INDEX IF NOT EXISTS idx_trace_steps_trace_id ON trace_steps(trace_id);
CREATE INDEX IF NOT EXISTS idx_traces_timestamp ON traces(timestamp DESC);
"""


class TraceStore:
    """Async SQLite-backed trace storage."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._initialized = False

    async def _ensure_tables(self, db: aiosqlite.Connection):
        if not self._initialized:
            await db.executescript(_CREATE_TABLES_SQL)
            await db.commit()
            self._initialized = True

    async def save_trace(self, trace: AgentTrace) -> None:
        """Persist a complete trace with all its steps."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_tables(db)

            decision_json = trace.decision.model_dump_json() if trace.decision else None

            await db.execute(
                """INSERT OR REPLACE INTO traces
                   (trace_id, session_id, timestamp, total_duration_ms, final_decision, user_message, decision_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    trace.trace_id,
                    trace.session_id,
                    trace.timestamp.isoformat(),
                    trace.total_duration_ms,
                    trace.final_decision,
                    trace.user_message,
                    decision_json,
                ),
            )

            for step in trace.steps:
                await db.execute(
                    """INSERT OR REPLACE INTO trace_steps
                       (step_id, trace_id, agent_name, status, start_time, end_time,
                        duration_ms, input_summary, output_summary, inference_mode, raw_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        step.step_id,
                        step.trace_id,
                        step.agent_name,
                        step.status.value,
                        step.start_time.isoformat() if step.start_time else None,
                        step.end_time.isoformat() if step.end_time else None,
                        step.duration_ms,
                        step.input_summary,
                        step.output_summary,
                        step.inference_mode.value,
                        json.dumps(step.raw_json),
                    ),
                )

            await db.commit()
            logger.info("Saved trace %s with %d steps", trace.trace_id, len(trace.steps))

    async def get_trace(self, trace_id: str) -> Optional[dict]:
        """Retrieve a full trace with all steps."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_tables(db)
            db.row_factory = aiosqlite.Row

            cursor = await db.execute("SELECT * FROM traces WHERE trace_id = ?", (trace_id,))
            row = await cursor.fetchone()
            if not row:
                return None

            trace_dict = dict(row)
            if trace_dict.get("decision_json"):
                trace_dict["decision"] = json.loads(trace_dict["decision_json"])
            del trace_dict["decision_json"]

            cursor = await db.execute(
                "SELECT * FROM trace_steps WHERE trace_id = ? ORDER BY start_time",
                (trace_id,),
            )
            steps = []
            async for step_row in cursor:
                step_dict = dict(step_row)
                if step_dict.get("raw_json"):
                    step_dict["raw_json"] = json.loads(step_dict["raw_json"])
                steps.append(step_dict)

            trace_dict["steps"] = steps
            return trace_dict

    async def list_traces(self, limit: int = 20, offset: int = 0) -> list[dict]:
        """List recent traces (summary only, no steps)."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_tables(db)
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                "SELECT trace_id, session_id, timestamp, total_duration_ms, final_decision, user_message "
                "FROM traces ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            traces = []
            async for row in cursor:
                traces.append(dict(row))
            return traces
