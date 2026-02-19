"""
FastAPI application — WebSocket chat + REST trace endpoints.

Endpoints:
  WS  /ws/chat           — Real-time chat + agent flow events
  GET /api/traces         — List recent traces
  GET /api/traces/{id}    — Full trace with steps
  POST /api/upload-screenshot — Upload competitor screenshot
  GET /api/health         — Health check
"""

from __future__ import annotations

import json
import os
import re
import uuid
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings, get_kernel
from backend.tracing.trace_store import TraceStore
from backend.tracing.trace_models import AgentStep, StepStatus
from backend.agents.orchestrator import orchestrate

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLPG Reactive Price Beat Agent",
    description="Endeavour Group — Lowest Liquor Price Guarantee MVP",
    version="0.1.0",
)

# CORS — allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globals (initialized on startup)
_kernel = None
_has_real_ai = False
_trace_store: Optional[TraceStore] = None


@app.on_event("startup")
async def startup():
    global _kernel, _has_real_ai, _trace_store

    settings = get_settings()
    logger.info("Starting LLPG Price Beat Agent backend")
    logger.info("Data dir: %s", settings.resolved_data_dir)
    logger.info("Trace DB: %s", settings.resolved_trace_db_path)

    # Initialize kernel
    _kernel, _has_real_ai = get_kernel()
    logger.info("Real AI available: %s", _has_real_ai)

    # Initialize trace store
    _trace_store = TraceStore(settings.resolved_trace_db_path)

    # Mount screenshots as static files
    screenshots_dir = settings.resolved_data_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/screenshots", StaticFiles(directory=str(screenshots_dir)), name="screenshots")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health():
    settings = get_settings()
    return {
        "status": "ok",
        "real_ai": _has_real_ai,
        "data_dir_exists": settings.resolved_data_dir.exists(),
        "version": "0.1.0",
    }


# ---------------------------------------------------------------------------
# WebSocket Chat
# ---------------------------------------------------------------------------
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info("WebSocket connected: session=%s", session_id)

    async def send_ws(data: dict):
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.warning("Failed to send WS message: %s", e)

    # Send welcome message
    await send_ws({
        "type": "chat_message",
        "message": "Hi! I'm the Dan Murphy's Price Beat Assistant. "
                   "If you've found a product cheaper elsewhere, share the details "
                   "and I'll check our Lowest Liquor Price Guarantee for you! 🍷",
    })

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                user_message = msg.get("message", msg.get("content", data))
            except json.JSONDecodeError:
                user_message = data

            if not user_message.strip():
                continue

            logger.info("[session=%s] User: %s", session_id, user_message[:100])

            # Echo user message back (for chat panel)
            await send_ws({
                "type": "chat_message",
                "message": user_message,
            })

            # Run orchestration
            try:
                result = await orchestrate(
                    kernel=_kernel,
                    has_real_ai=_has_real_ai,
                    user_message=user_message,
                    session_id=session_id,
                    trace_store=_trace_store,
                    send_ws=send_ws,
                )
                logger.info("[session=%s] Result: %s", session_id, result.get("decision"))
            except Exception as e:
                logger.error("[session=%s] Orchestration error: %s", session_id, e, exc_info=True)
                await send_ws({
                    "type": "chat_message",
                    "message": "I'm sorry, something went wrong. Please try again.",
                })
                error_step = AgentStep(
                    step_id=str(uuid.uuid4()),
                    trace_id="error",
                    agent_name="System",
                    status=StepStatus.FAILED,
                    raw_json={"error": str(e)},
                )
                await send_ws({
                    "type": "agent_step",
                    "step": error_step.model_dump(by_alias=True),
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: session=%s", session_id)


# ---------------------------------------------------------------------------
# Trace REST Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/traces")
async def list_traces(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List recent traces with summary."""
    traces = await _trace_store.list_traces(limit=limit, offset=offset)
    return {"traces": traces, "count": len(traces)}


@app.get("/api/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get full trace with all agent steps."""
    trace = await _trace_store.get_trace(trace_id)
    if not trace:
        return JSONResponse(status_code=404, content={"error": "Trace not found"})
    return trace


# ---------------------------------------------------------------------------
# Screenshot Upload
# ---------------------------------------------------------------------------
@app.post("/api/upload-screenshot")
async def upload_screenshot(file: UploadFile = File(...)):
    """Upload a competitor screenshot for analysis."""
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Validate size with streaming to prevent memory exhaustion (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    content_size = 0
    chunks = []
    
    async for chunk in file.stream():
        content_size += len(chunk)
        if content_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of 10MB"
            )
        chunks.append(chunk)
    
    content = b''.join(chunks)
    
    settings = get_settings()
    screenshots_dir = settings.resolved_data_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename - extract basename and remove unsafe characters
    safe_filename = os.path.basename(file.filename) if file.filename else "upload.png"
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', safe_filename)
    filename = f"upload_{uuid.uuid4().hex[:8]}_{safe_filename}"
    file_path = screenshots_dir / filename

    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "filename": filename,
        "path": f"data/screenshots/{filename}",
        "url": f"/screenshots/{filename}",
        "size_bytes": len(content),
    }


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
