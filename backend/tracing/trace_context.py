"""
Async context manager for automatic agent step tracing.

Usage:
    async with trace_step(trace, "IntentAgent", user_msg) as step:
        result, mode = await invoke_with_fallback(...)
        step.output_summary = json.dumps(result)
        step.inference_mode = InferenceMode(mode)
        step.raw_json = result
"""

from __future__ import annotations

import uuid
import time
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from backend.tracing.trace_models import AgentStep, AgentTrace, StepStatus, InferenceMode

logger = logging.getLogger(__name__)


@asynccontextmanager
async def trace_step(
    trace: AgentTrace,
    agent_name: str,
    input_summary: str = "",
) -> AsyncGenerator[AgentStep, None]:
    """
    Context manager that auto-captures timing and status for an agent step.

    On entry: creates step with RUNNING status and start_time.
    On success: sets COMPLETED status with end_time and duration.
    On exception: sets FAILED status with error details in raw_json.
    """
    step = AgentStep(
        step_id=str(uuid.uuid4()),
        trace_id=trace.trace_id,
        agent_name=agent_name,
        status=StepStatus.RUNNING,
        start_time=datetime.now(timezone.utc),
        input_summary=input_summary[:500],  # truncate long inputs
    )
    trace.steps.append(step)

    start = time.perf_counter()
    try:
        yield step
        step.status = StepStatus.COMPLETED
    except Exception as e:
        step.status = StepStatus.FAILED
        step.raw_json = {
            "error": str(e),
            "error_type": type(e).__name__,
            **(step.raw_json or {}),
        }
        logger.error("[%s] Step failed: %s", agent_name, e)
        raise
    finally:
        elapsed = time.perf_counter() - start
        step.end_time = datetime.now(timezone.utc)
        step.duration_ms = int(elapsed * 1000)
