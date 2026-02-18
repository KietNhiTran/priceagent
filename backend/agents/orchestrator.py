"""
Orchestrator — Coordinates all 6 agents in sequence.

Wraps each agent invocation in trace_context for automatic step capture.
Emits WebSocket events for real-time UI updates.
Persists full trace to SQLite after completion.
"""

from __future__ import annotations

import uuid
import time
import json
import logging
from datetime import datetime
from typing import Any, Callable, Awaitable, Optional

from backend.tracing.trace_models import AgentTrace, TraceDecision, InferenceMode
from backend.tracing.trace_context import trace_step
from backend.tracing.trace_store import TraceStore

from backend.agents.intent_agent import run_intent_agent
from backend.agents.url_validation_agent import run_url_validation_agent
from backend.agents.scraping_agent import run_scraping_agent
from backend.agents.product_matching_agent import run_product_matching_agent
from backend.agents.llpg_rule_agent import run_llpg_rule_agent
from backend.agents.decision_agent import run_decision_agent

logger = logging.getLogger(__name__)


async def orchestrate(
    kernel,
    has_real_ai: bool,
    user_message: str,
    session_id: str,
    trace_store: TraceStore,
    send_ws: Optional[Callable[[dict], Awaitable[None]]] = None,
) -> dict[str, Any]:
    """
    Run the full 6-agent LLPG pipeline.

    Args:
        kernel: Semantic Kernel instance
        has_real_ai: Whether real AI is available
        user_message: Customer's chat message
        session_id: WebSocket session ID
        trace_store: SQLite trace store
        send_ws: Optional async callback to send WebSocket messages

    Returns:
        Final result dict with decision, trace_id, etc.
    """
    trace = AgentTrace(
        trace_id=str(uuid.uuid4()),
        session_id=session_id,
        timestamp=datetime.utcnow(),
        user_message=user_message,
    )
    start_time = time.perf_counter()

    async def _emit(event_type: str, data: dict):
        if send_ws:
            await send_ws({"type": event_type, **data})

    # Send initial chat message
    await _emit("chat_message", {
        "message": "Let me check that for you...",
        "sender": "bot",
    })

    # ─────────────────────────────────────────────────────────────────────
    # Step 1: Intent Detection
    # ─────────────────────────────────────────────────────────────────────
    async with trace_step(trace, "IntentAgent", user_message) as step:
        await _emit("agent_step", {
            "agent": "Intent Detection",
            "status": "running",
            "details": {},
        })
        intent_result, intent_mode = await run_intent_agent(kernel, user_message, has_real_ai)
        step.output_summary = json.dumps(intent_result)[:500]
        step.inference_mode = InferenceMode(intent_mode)
        step.raw_json = intent_result

    await _emit("agent_step", {
        "agent": "Intent Detection",
        "status": "completed",
        "duration_ms": step.duration_ms,
        "inference_mode": intent_mode,
        "details": {
            "intent": intent_result.get("intent"),
            "confidence": intent_result.get("confidence"),
        },
    })

    # Check if this is an LLPG request
    if intent_result.get("intent") != "llpg_price_beat":
        await _emit("chat_message", {
            "message": "I can help with that! However, this doesn't seem to be a price-beat request. "
                       "If you've found a product cheaper elsewhere, please share the details and I'll check our Lowest Liquor Price Guarantee for you.",
            "sender": "bot",
        })
        trace.final_decision = "NOT_LLPG"
        trace.total_duration_ms = int((time.perf_counter() - start_time) * 1000)
        await trace_store.save_trace(trace)
        return {"decision": "NOT_LLPG", "trace_id": trace.trace_id, "message": "Not an LLPG request"}

    entities = intent_result.get("entities", {})
    competitor_url = entities.get("competitor_url")
    competitor_name = entities.get("competitor")
    product_name_hint = entities.get("product_name")
    stated_price = entities.get("competitor_price")

    # ─────────────────────────────────────────────────────────────────────
    # Step 2: URL Validation
    # ─────────────────────────────────────────────────────────────────────
    async with trace_step(trace, "URLValidationAgent", competitor_url or "no URL") as step:
        await _emit("agent_step", {
            "agent": "URL Validation",
            "status": "running",
            "details": {},
        })
        url_result, url_mode = await run_url_validation_agent(competitor_url)
        step.output_summary = json.dumps(url_result)[:500]
        step.inference_mode = InferenceMode(url_mode)
        step.raw_json = url_result

    await _emit("agent_step", {
        "agent": "URL Validation",
        "status": "completed",
        "duration_ms": step.duration_ms,
        "inference_mode": url_mode,
        "details": {
            "is_valid": url_result.get("is_valid"),
            "competitor": url_result.get("competitor"),
        },
    })

    # Use competitor from URL validation if available
    if url_result.get("competitor"):
        competitor_name = url_result["competitor"]

    if competitor_url and not url_result.get("is_valid"):
        await _emit("chat_message", {
            "message": f"Sorry, I couldn't verify that URL. {url_result.get('reason', '')} "
                       f"Could you double-check the link or tell me the competitor name and price?",
            "sender": "bot",
        })

    # ─────────────────────────────────────────────────────────────────────
    # Step 3: Scraping
    # ─────────────────────────────────────────────────────────────────────
    async with trace_step(trace, "ScrapingAgent", f"URL={competitor_url}, comp={competitor_name}") as step:
        await _emit("agent_step", {
            "agent": "Competitor Scraping",
            "status": "running",
            "details": {},
        })

        scrape_url = competitor_url if url_result.get("is_valid") else None
        scrape_result, scrape_mode = await run_scraping_agent(
            url=scrape_url,
            competitor=competitor_name,
            product_name=product_name_hint,
            competitor_price=stated_price,
        )
        step.output_summary = json.dumps(scrape_result)[:500]
        step.inference_mode = InferenceMode(scrape_mode)
        step.raw_json = scrape_result

    await _emit("agent_step", {
        "agent": "Competitor Scraping",
        "status": "completed",
        "duration_ms": step.duration_ms,
        "inference_mode": scrape_mode,
        "details": {
            "scrape_mode": scrape_result.get("scrape_mode"),
            "competitor_price": scrape_result.get("competitor_price"),
            "competitor": scrape_result.get("competitor"),
        },
    })

    competitor_price = scrape_result.get("competitor_price") or stated_price
    if not competitor_price:
        await _emit("chat_message", {
            "message": "I couldn't find the competitor's price. Could you tell me the exact price you saw?",
            "sender": "bot",
        })
        trace.final_decision = "INCOMPLETE"
        trace.total_duration_ms = int((time.perf_counter() - start_time) * 1000)
        await trace_store.save_trace(trace)
        return {"decision": "INCOMPLETE", "trace_id": trace.trace_id, "message": "Missing competitor price"}

    # ─────────────────────────────────────────────────────────────────────
    # Step 4: Product Matching
    # ─────────────────────────────────────────────────────────────────────
    comp_product_name = scrape_result.get("competitor_product_name", product_name_hint or "")
    matched_sku_from_csv = scrape_result.get("matched_sku")

    async with trace_step(trace, "ProductMatchingAgent", comp_product_name) as step:
        await _emit("agent_step", {
            "agent": "Product Matching",
            "status": "running",
            "details": {},
        })
        match_result, match_mode = await run_product_matching_agent(
            kernel,
            competitor_product_name=comp_product_name,
            competitor_price=competitor_price,
            competitor=competitor_name or "",
            matched_sku=matched_sku_from_csv,
            has_real_ai=has_real_ai,
        )
        step.output_summary = json.dumps(match_result)[:500]
        step.inference_mode = InferenceMode(match_mode)
        step.raw_json = match_result

    await _emit("agent_step", {
        "agent": "Product Matching",
        "status": "completed",
        "duration_ms": step.duration_ms,
        "inference_mode": match_mode,
        "details": {
            "matched_sku": match_result.get("matched_sku"),
            "confidence": match_result.get("match_confidence"),
            "product_name": match_result.get("product_name"),
        },
    })

    if not match_result.get("matched_sku"):
        await _emit("chat_message", {
            "message": "I couldn't find a matching product in our catalogue. Could you provide more details about the product?",
            "sender": "bot",
        })
        trace.final_decision = "NO_MATCH"
        trace.total_duration_ms = int((time.perf_counter() - start_time) * 1000)
        await trace_store.save_trace(trace)
        return {"decision": "NO_MATCH", "trace_id": trace.trace_id, "message": "No product match"}

    our_product_name = match_result.get("product_name", "")
    own_price = match_result.get("current_price", 0)
    cost_price = match_result.get("cost_price", 0)
    category = match_result.get("category", "beer")

    # ─────────────────────────────────────────────────────────────────────
    # Step 5: LLPG Rule Evaluation
    # ─────────────────────────────────────────────────────────────────────
    async with trace_step(trace, "LLPGRuleAgent", f"comp=${competitor_price}, own=${own_price}") as step:
        await _emit("agent_step", {
            "agent": "LLPG Rules",
            "status": "running",
            "details": {},
        })
        rule_result, rule_mode = await run_llpg_rule_agent(
            kernel,
            competitor_price=competitor_price,
            own_price=own_price,
            cost_price=cost_price,
            category=category,
            competitor_product_name=comp_product_name,
            our_product_name=our_product_name,
            has_real_ai=has_real_ai,
        )
        step.output_summary = json.dumps(rule_result)[:500]
        step.inference_mode = InferenceMode(rule_mode)
        step.raw_json = rule_result

    await _emit("agent_step", {
        "agent": "LLPG Rules",
        "status": "completed",
        "duration_ms": step.duration_ms,
        "inference_mode": rule_mode,
        "details": {
            "decision": rule_result.get("decision"),
            "beat_price": rule_result.get("beat_price"),
            "rsa_compliant": rule_result.get("rsa_compliant"),
            "tier": rule_result.get("tier"),
        },
    })

    # ─────────────────────────────────────────────────────────────────────
    # Step 6: Decision
    # ─────────────────────────────────────────────────────────────────────
    async with trace_step(trace, "DecisionAgent", json.dumps(rule_result)[:300]) as step:
        await _emit("agent_step", {
            "agent": "Decision",
            "status": "running",
            "details": {},
        })
        decision_result, decision_mode = await run_decision_agent(
            kernel,
            rule_result=rule_result,
            product_name=our_product_name,
            competitor=competitor_name or "competitor",
            own_price=own_price,
            competitor_price=competitor_price,
            has_real_ai=has_real_ai,
        )
        step.output_summary = json.dumps(decision_result)[:500]
        step.inference_mode = InferenceMode(decision_mode)
        step.raw_json = decision_result

    await _emit("agent_step", {
        "agent": "Decision",
        "status": "completed",
        "duration_ms": step.duration_ms,
        "inference_mode": decision_mode,
        "details": {
            "decision": decision_result.get("decision"),
            "beat_price": decision_result.get("beat_price"),
            "saving": decision_result.get("saving"),
        },
    })

    # ─────────────────────────────────────────────────────────────────────
    # Finalize trace
    # ─────────────────────────────────────────────────────────────────────
    trace.final_decision = decision_result.get("decision", "UNKNOWN")
    trace.total_duration_ms = int((time.perf_counter() - start_time) * 1000)

    trace.decision = TraceDecision(
        decision=rule_result.get("decision", "AUTO_REJECT"),
        reason_code=rule_result.get("tier", ""),
        beat_price=rule_result.get("beat_price"),
        rsa_compliant=rule_result.get("rsa_compliant", False),
        competitor=competitor_name or "",
        product_name=our_product_name,
        competitor_price=competitor_price,
        own_price=own_price,
        saving=decision_result.get("saving"),
    )

    await trace_store.save_trace(trace)

    # Send final chat message
    await _emit("chat_message", {
        "message": decision_result.get("message", "Processing complete."),
        "sender": "bot",
        "product_comparison": {
            "our_product": {
                "name": our_product_name,
                "price": own_price,
                "sku": match_result.get("matched_sku"),
                "image_url": "",
            },
            "competitor_product": {
                "name": comp_product_name,
                "price": competitor_price,
                "competitor": competitor_name,
                "image_url": "",
            },
            "beat_price": rule_result.get("beat_price"),
            "decision": decision_result.get("decision"),
            "saving": decision_result.get("saving"),
        },
    })

    # Send trace complete event
    await _emit("trace_complete", {
        "trace_id": trace.trace_id,
        "view_url": f"/api/traces/{trace.trace_id}",
    })

    return {
        "decision": decision_result.get("decision"),
        "message": decision_result.get("message"),
        "beat_price": rule_result.get("beat_price"),
        "trace_id": trace.trace_id,
        "total_duration_ms": trace.total_duration_ms,
    }
