# MVP Data Generation + Demo Bot UI with Agent Flow Visualization

> **Date:** 18 February 2026  
> **Status:** Draft — Pending Approval  
> **Project:** Endeavour Group — LLPG Reactive Price Beat Agent

---

## TL;DR

Generate CSV data files (product catalogue with image/URL/screenshot fields, competitor pricing, RSA config) and build a polished demo bot UI using **React + Vite (TypeScript)** with a split-panel design: left panel shows the customer chatbot conversation, right panel shows a real-time **"Agent Thinking"** visualization that reveals the multi-agent orchestration flow as each step happens. Backend is **Python FastAPI + Semantic Kernel** using **real Azure OpenAI models deployed in Microsoft AI Foundry** (GPT-4o, GPT-4o Vision, text-embedding-3-large), falling back to pre-computed responses only when inference fails. All agent steps and decisions are traced and stored (SQLite for demo, aligning with Req 7.1 audit trail and Req 7.2 decision traceability). The demo is designed to impress Endeavour Group decision-makers by making the AI agent pipeline transparent and understandable.

---

## Part A: Data Generation (CSV Files with Image/URL/Screenshot Support)

### Steps

1. Create `data/` directory structure:
   - `data/dan_murphys_catalogue.csv` — 50 products with image URLs and product page URLs
   - `data/competitor_prices.csv` — ~100 rows with competitor URLs and screenshot paths
   - `data/rsa_config.csv` — RSA floor prices by category & state
   - `data/beat_formula_config.csv` — beat price thresholds for auto/review/reject tiers
   - `data/screenshots/` — placeholder directory for competitor page screenshots (PNG)

2. **Enhanced product catalogue schema** — adds image/URL/screenshot columns:

   | Column | Type | Description |
   |---|---|---|
   | `sku` | string | Internal product SKU (e.g., "DM-001234") |
   | `barcode` | string | EAN-13 barcode |
   | `product_name` | string | Full product name |
   | `brand` | string | Brand name (e.g., "James Boag's") |
   | `category` | enum | `beer`, `wine`, `spirits`, `rtd`, `cider`, `non_alc` |
   | `subcategory` | string | E.g., "Pale Ale", "Shiraz", "Vodka" |
   | `volume_ml` | int | Container volume in mL |
   | `pack_size` | int | Number of units (1 for single, 6 for six-pack, etc.) |
   | `alcohol_pct` | float | ABV percentage (e.g., 4.6) |
   | `standard_drinks` | float | Standard drinks per unit (1 std drink = 10g ethanol) |
   | `current_price` | float | Current retail price (AUD) |
   | `cost_price` | float | Invoice/cost price (AUD) — for RSA floor calc |
   | `rsa_floor_price` | float | Pre-calculated minimum sell price |
   | `region` | string | Wine region or origin (e.g., "Barossa Valley") |
   | `country` | string | Country of origin |
   | `active` | boolean | Whether product is currently listed |
   | `product_url` | string | Dan Murphy's product page URL |
   | `image_url` | string | Product image URL (CDN path) |
   | `thumbnail_url` | string | Smaller image for chat display |

3. **Enhanced competitor prices schema** — adds screenshot/proof columns:

   | Column | Type | Description |
   |---|---|---|
   | `competitor` | enum | `liquorland`, `liquorland_warehouse`, `boozebud` |
   | `competitor_url` | string | Full product page URL |
   | `competitor_product_name` | string | Product name as shown on competitor site |
   | `competitor_price` | float | Competitor's current price (AUD) |
   | `competitor_barcode` | string | EAN-13 if available |
   | `matched_sku` | string | Matched Dan Murphy's SKU (nullable) |
   | `match_confidence` | float | AI matching confidence score (0.0–1.0) |
   | `scrape_timestamp` | datetime | When the price was captured |
   | `price_per_litre` | float | Normalised price for comparison |
   | `in_stock` | boolean | Whether product is in stock at competitor |
   | `promotion` | string | Any promo text (e.g., "2 for $40") |
   | `screenshot_path` | string | Local path to captured screenshot |
   | `screenshot_url` | string | Blob storage URL for the screenshot |
   | `competitor_image_url` | string | Competitor's product image for visual matching |

4. Generate **50 realistic products** using a Python script (`scripts/generate_data.py`):
   - 15 beers: Victoria Bitter, Carlton Draught, James Boag's Premium, Coopers Pale Ale, Great Northern, XXXX Gold, etc.
   - 15 wines: Penfolds Bin 389, Yellow Tail Shiraz, Jacob's Creek, Oyster Bay Sauvignon Blanc, etc.
   - 10 spirits: Johnnie Walker Red, Smirnoff, Tanqueray, Bundaberg Rum, etc.
   - 5 RTDs: Canadian Club & Dry, Jim Beam & Cola, Smirnoff Ice, etc.
   - 5 ciders/non-alc: Somersby, Apple Blossom, Heaps Normal, etc.
   - Price ranges: beer 6-pack $16–$25, wine bottle $8–$50, spirits 700mL $36–$70
   - Image URLs: Use placeholder pattern `https://media.danmurphys.com.au/dmo/product/{sku}-1.png`

5. Generate **~100 competitor price rows** with realistic price variance:
   - ~30% of competitor prices cheaper than Dan Murphy's (LLPG trigger scenarios)
   - ~50% same or within $0.50 (no action)
   - ~20% more expensive (no action)
   - Each competitor entry includes a `screenshot_path` pointing to `data/screenshots/{competitor}_{sku}_{date}.png`
   - Generate placeholder screenshot images (simple HTML-to-PNG with product info for demo)

6. Generate config CSVs:
   - `rsa_config.csv`: floor prices per category (beer $1.50/std, wine $1.20/std, spirits $1.80/std, RTD $1.60/std) plus cost+5% floor
   - `beat_formula_config.csv`: auto-approve/review/reject thresholds as defined below

---

## Part A.1: RSA Compliance Floor Price — Recommended Thresholds

> **Background:** NSW has no legislated numerical floor price. The NT is the only Australian jurisdiction with one ($1.30/standard drink since Oct 2018). The floor price in this system is an **internal business policy**.

### Per-Category Floor Price Model

| Category | Suggested Floor Price | Rationale |
|---|---|---|
| Beer (per standard drink) | **$1.50/std drink** | Above NT minimum ($1.30), covers excise + GST + margin |
| Wine (per standard drink) | **$1.20/std drink** | Wine Equalisation Tax (WET) applies differently; lower excise |
| Spirits (per standard drink) | **$1.80/std drink** | Highest excise rate (~$100.16/LAL), need higher floor |
| RTDs / Pre-mix (per standard drink) | **$1.60/std drink** | Mid-range excise, popular binge-drinking category |

### Simplified MVP Model

**Flat floor = cost price + 5% minimum margin** — the system refuses to beat below invoice cost plus 5%.

> The `check_rsa_compliance` plugin loads thresholds from config (Azure App Configuration or `rsa_config.csv` for MVP), making it adjustable per state/territory.

---

## Part A.2: Beat Price Formula Thresholds

### Formula

```
beat_price = competitor_price - beat_amount
```

### Risk Tier Routing

| Rule | Value | Description |
|---|---|---|
| **Beat amount (default)** | **$0.01** | Standard price-beat by 1 cent (industry norm) |
| **Maximum beat %** | **10%** of own current price | Triggers human review if exceeded |
| **Minimum sale price** | RSA floor price | Hard stop — never sell below RSA floor |
| **Auto-approve threshold** | Beat $0.01–$5.00, price diff < 15% | Auto-approve if change is small |
| **Human review threshold** | Beat $5.01–$20.00, or diff 15%–30% | Route to CHUB for review |
| **Auto-reject threshold** | Beat > $20.00, or diff > 30%, or below RSA floor | Auto-reject with reason code |

---

## Part A.3: Top 3 Competitor Sites

| # | Competitor | Website | Owner | Rationale |
|---|---|---|---|---|
| **1** | **Liquorland** | `liquorland.com.au` | Coles Group | Largest rival chain (~743+ stores, absorbing First Choice & Vintage Cellars by Dec 2025) |
| **2** | **Liquorland Warehouse** (formerly First Choice Liquor Market) | `liquorland.com.au/warehouse` | Coles Group | Large-format discount competitor — directly analogous to Dan Murphy's warehouse model |
| **3** | **BoozeBud** | `boozebud.com` | Independent (online) | Leading independent online alcohol retailer. Pure e-commerce with clean product pages |

> For MVP, 3 competitors keeps scraping manageable. Liquorland and Liquorland Warehouse share a domain (`liquorland.com.au`). BoozeBud is a pure-online competitor with structured product data.

---

## Part B: Demo Bot UI — Dual-Panel Design

### Layout

```
┌─────────────────────────────────────────────────────┐
│              Endeavour LLPG Price Beat Agent         │
│                    Demo Dashboard                    │
├─────────────────────┬───────────────────────────────┤
│                     │                               │
│   CUSTOMER CHAT     │    AGENT THINKING PANEL       │
│                     │    (Real-time Flow)            │
│  ┌───────────────┐  │  ┌─────────────────────────┐  │
│  │ Bot: Hi! How   │  │  │ ● Orchestrator Agent    │  │
│  │ can I help?   │  │  │   ├─ Intent: LLPG ✓     │  │
│  │               │  │  │   ├─ URL Validated ✓     │  │
│  │ User: I found │  │  │   │                      │  │
│  │ VB cheaper at │  │  │ ● Vision Agent           │  │
│  │ Liquorland    │  │  │   ├─ Screenshot taken ✓  │  │
│  │ $48.99!       │  │  │   ├─ Label matched ✓     │  │
│  │ [image]       │  │  │   │                      │  │
│  │               │  │  │ ● Product Matching Agent  │  │
│  │ Bot: Let me   │  │  │   ├─ SKU: DM-VB24 ✓     │  │
│  │ check that... │  │  │   ├─ Confidence: 97% ✓   │  │
│  │               │  │  │   │                      │  │
│  │               │  │  │ ● LLPG Rule Evaluator    │  │
│  │               │  │  │   ├─ Stock-for-stock ✓   │  │
│  │               │  │  │   ├─ RSA floor: OK ✓     │  │
│  │               │  │  │   ├─ Beat: $48.98 ✓      │  │
│  │               │  │  │   │                      │  │
│  │ Bot: Great    │  │  │ ● Pricing Analyst         │  │
│  │ news! We can  │  │  │   ├─ Tier: AUTO-APPROVE  │  │
│  │ beat that at  │  │  │   ├─ Saving: $3.01       │  │
│  │ $48.98!       │  │  │   └─ Decision: APPROVED ✓│  │
│  └───────────────┘  │  └─────────────────────────┘  │
│  [Type message...]  │  [Expand/Collapse details]    │
├─────────────────────┴───────────────────────────────┤
│ ⚙ Admin | 📊 Audit Trail | 📷 Screenshots | ❓Help │
└─────────────────────────────────────────────────────┘
```

### Steps

7. **Scaffold the React frontend** at `frontend/`:
   - `npx create-vite frontend --template react-ts`
   - Install: `@fluentui/react-components` (Microsoft Fluent UI), `react-markdown`, `framer-motion` (animations), `axios`

8. **Build 3 main UI components** in `frontend/src/components/`:

   - **`ChatPanel.tsx`** — Left panel (50% width):
     - Clean chat bubble interface (user messages right, bot messages left)
     - Support for image attachments (user can paste/upload screenshot or URL)
     - Product cards with images, prices, and beat-price result
     - Typing indicator with "Agent is analyzing..." animation
     - "Upload screenshot" and "Paste URL" quick-action buttons
     - Conversation starter suggestions: "I found a cheaper price", "Check this URL", "Can you beat this?"

   - **`AgentFlowPanel.tsx`** — Right panel (50% width):
     - Vertical timeline/stepper showing each agent step in real-time
     - Each step node shows: Agent name, status (pending/running/done/failed), duration, key output
     - Color-coded: green (passed), amber (warning/review), red (failed/rejected)
     - Expandable detail cards — click to see raw data (matched SKU, rule results, screenshots)
     - Animated transitions as each agent completes
     - Final decision badge: "AUTO-APPROVED", "SENT TO REVIEW", or "REJECTED" with reason

   - **`ProductComparisonCard.tsx`** — Shown inside chat when a beat decision is made:
     - Side-by-side: Dan Murphy's product (image, price) vs Competitor product (image, screenshot, price)
     - Beat price highlighted in green
     - RSA compliance badge
     - Savings amount displayed prominently

9. **Build `AgentOrchestrationBar.tsx`** — A horizontal progress bar at the top:
   ```
   [Intent Detection] → [URL Validation] → [Scraping] → [Product Matching] → [LLPG Rules] → [Decision]
   ```
   Each stage lights up as it's being processed.

10. **Create `frontend/src/pages/DemoPage.tsx`**:
    - Responsive layout with Fluent UI `Panel` and `Stack` components
    - Header: Endeavour Group branding + "LLPG Price Beat Agent — AI Demo"
    - Footer: Admin links, audit trail viewer, help
    - Dark/light theme toggle (Fluent UI theme provider)

---

## Part C: Backend — FastAPI + Semantic Kernel + Azure AI Foundry

### Part C.1: Azure AI Foundry Configuration

11. **Configure Azure OpenAI connection** — real models used by default, fallback on failure:
    - Create `backend/.env.example` with required Azure OpenAI settings:
      ```
      AZURE_OPENAI_ENDPOINT=https://<your-foundry-project>.openai.azure.com/
      AZURE_OPENAI_API_KEY=<key>           # or use DefaultAzureCredential
      AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o  # GPT-4o deployment name
      AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4o-vision  # GPT-4o Vision deployment name
      AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
      AZURE_OPENAI_API_VERSION=2024-12-01-preview
      ```
    - Create `backend/config.py`:
      - Loads `.env` via `python-dotenv`, validates Azure credentials are present
      - Exposes `get_kernel()` factory that creates a Semantic Kernel instance with `AzureChatCompletion` service
      - Supports both API key auth and `DefaultAzureCredential` (managed identity for production)

12. **Implement inference fallback wrapper** in `backend/inference.py`:
    - **Primary path**: Real Azure OpenAI inference via Semantic Kernel
    - **Fallback path**: Pre-computed responses from `data/fallback_responses.json` — activated **only** when inference fails:
      - `HttpResponseError` (401, 403, 429 quota exceeded)
      - `ServiceResponseException` (deployment unavailable)
      - `asyncio.TimeoutError` (network timeout)
      - `ConnectionError` (endpoint unreachable)
    - All fallback invocations are flagged in the trace as `"inference_mode": "fallback"`
    - Non-fallback (successful) invocations are recorded as `"inference_mode": "real"`
    - Create `data/fallback_responses.json` — pre-computed responses keyed by agent name, matching expected output schemas

### Part C.2: Agent Tracing & Audit Storage

> Aligned with solution architecture: Req 7.1 (audit trail capture) and Req 7.2 (decision traceability). Simplified for demo — local SQLite replaces Event Hubs `audit-events` → Fabric Eventhouse `AuditTrail` KQL table.

13. **Create `backend/tracing/` module**:
    - `trace_models.py` — Pydantic models:
      - `AgentTrace`: `trace_id`, `session_id`, `timestamp`, `total_duration_ms`, `final_decision`, `user_message`
      - `AgentStep`: `step_id`, `trace_id`, `agent_name`, `status` (pending/running/completed/failed), `start_time`, `end_time`, `duration_ms`, `input_summary`, `output_summary`, `inference_mode` (real/fallback), `raw_json`
      - `TraceDecision`: `decision` (auto-approved/review/rejected), `reason_code`, `beat_price`, `rsa_compliant`
    - `trace_store.py` — async SQLite storage (`data/traces.db`, auto-created at runtime):
      - Table `traces`: `trace_id TEXT PK`, `session_id`, `timestamp`, `total_duration_ms`, `final_decision`, `user_message`
      - Table `trace_steps`: `step_id TEXT PK`, `trace_id FK`, `agent_name`, `status`, `start_time`, `end_time`, `duration_ms`, `input_summary`, `output_summary`, `inference_mode`, `raw_json TEXT`
    - `trace_context.py` — async context manager that auto-captures each agent step:
      - Records start/end timestamps, input/output summaries
      - Captures whether real or fallback inference was used
      - On exception: records `status=failed` with error details in `raw_json`
    - **Req 7.1 mapping**: Each trace captures competitor name, matched SKU, competitor price, own price, and all rule decisions
    - **Req 7.2 mapping**: `LLPGRuleAgent` step `raw_json` stores structured rule evaluations:
      ```json
      {
        "rsa_check": { "floor_price": 47.25, "beat_price": 48.98, "compliant": true },
        "stock_for_stock": { "same_product": true, "same_volume": true, "same_pack": true },
        "beat_formula": { "competitor_price": 48.99, "beat_amount": 0.01, "beat_price": 48.98, "diff_pct": 3.2, "tier": "auto-approve" }
      }
      ```

14. **Add trace REST endpoints** in `backend/main.py`:
    - `GET /api/traces` — list recent traces with summary (paginated, most recent first)
    - `GET /api/traces/{trace_id}` — full trace with all agent steps and raw JSON details
    - Used by the frontend `AgentFlowPanel` "View Full Trace" feature and admin audit panel

### Part C.3: Backend Core

15. **Create Python backend** at `backend/`:
    - `backend/main.py` — FastAPI app with WebSocket endpoint for real-time chat + agent flow events, plus trace REST endpoints
    - `backend/agents/` — Semantic Kernel agent definitions (using real Azure OpenAI models)
    - `backend/plugins/` — SK plugins (`compute_beat_price`, `check_rsa_compliance`, etc.)
    - `backend/data/` — CSV data loaders using pandas

16. **WebSocket protocol** for real-time dual-panel updates:
    - Frontend connects via `ws://localhost:8000/ws/chat`
    - Each message from backend includes payload types:

    **Chat message (for ChatPanel):**
    ```json
    {
      "type": "chat_message",
      "content": "Let me check that for you...",
      "images": ["url1.png"]
    }
    ```

    **Agent step (for AgentFlowPanel):**
    ```json
    {
      "type": "agent_step",
      "agent": "Product Matching Agent",
      "status": "completed",
      "duration_ms": 1200,
      "inference_mode": "real",
      "details": { "matched_sku": "DM-VB24", "confidence": 0.97 }
    }
    ```

    **Trace complete (after all agents finish):**
    ```json
    {
      "type": "trace_complete",
      "trace_id": "550e8400-e29b-41d4-a716-446655440000",
      "view_url": "/api/traces/550e8400-e29b-41d4-a716-446655440000"
    }
    ```

17. **Implement 6 agent steps** in Semantic Kernel (real Azure OpenAI inference with per-agent fallback):
    - `IntentAgent` — Detect LLPG intent from user message (GPT-4o)
    - `URLValidationAgent` — Validate competitor URL against allow-list (rule-based, no LLM needed)
    - `ScrapingAgent` — **Two-mode scraping** (real scrape first, CSV fallback):
      - **Primary (real scrape)**: When customer provides a competitor URL, use **Playwright** to navigate to the page, render JavaScript, extract product name + price + promo text, and capture a page screenshot. Aligns with Req 2.1 (real-time scraping) and Req 8.1 (scrape + decision < 3–6 sec)
      - **Fallback (CSV lookup)**: When no URL is provided (e.g., user says "VB is cheaper at Liquorland") or when scraping fails (site blocks, timeout, anti-bot), look up the product in `competitor_prices.csv` by competitor name + product name match
      - **Hybrid mode** per Req 2.3: If batch/CSV result exists but customer disputes it, trigger a real-time re-scrape of the URL
      - Output: product name, price, promo text, screenshot path, scrape timestamp, `scrape_mode` ("real" or "csv_fallback")
      - Trace `raw_json` records: URL attempted, HTTP status, extraction method, time to scrape, fallback reason (if any)
    - `ProductMatchingAgent` — Match competitor product to Dan Murphy's catalogue (GPT-4o + embeddings)
    - `LLPGRuleAgent` — Apply all LLPG rules: RSA, stock-for-stock, beat formula (rule-based + GPT-4o for edge cases)
    - `DecisionAgent` — Final pricing decision with natural language explanation (GPT-4o)
    - Each agent is wrapped in `trace_context` — auto-records timing, input/output, inference mode
    - If one agent's inference fails, it falls back independently; other agents continue using real AI

18. **Update orchestrator** (`backend/agents/orchestrator.py`):
    - Wrap each agent invocation in `trace_context` for automatic step capture
    - Pass `AzureChatCompletion` kernel to each agent
    - After all agents complete, persist full trace to SQLite via `trace_store`
    - Emit `trace_complete` WebSocket event with `trace_id`

19. **Add screenshot handling**:
    - Endpoint `POST /api/upload-screenshot` — accepts image file, stores in `data/screenshots/`
    - GPT-4o Vision integration for label/price extraction from screenshots (real Azure OpenAI)
    - Falls back to pre-computed extraction result only when Vision inference fails

---

## Part D: Project Structure

```
c:\Code\priceagent\
├── package.json                          (existing)
├── data/
│   ├── dan_murphys_catalogue.csv         (50 products + image/URL columns)
│   ├── competitor_prices.csv             (100 rows + screenshot paths)
│   ├── rsa_config.csv                    (floor prices per category)
│   ├── beat_formula_config.csv           (auto/review/reject thresholds)
│   ├── fallback_responses.json           (pre-computed agent responses for inference fallback)
│   ├── traces.db                         (auto-created at runtime — SQLite trace store)
│   └── screenshots/                      (competitor page screenshots)
├── scripts/
│   └── generate_data.py                  (Python script to generate all CSVs)
├── backend/
│   ├── requirements.txt                  (fastapi, uvicorn, semantic-kernel, pandas, azure-identity, playwright, etc.)
│   ├── .env.example                      (Azure OpenAI configuration template)
│   ├── .env                              (local — git-ignored — actual Azure credentials)
│   ├── config.py                         (Azure OpenAI + SK kernel factory)
│   ├── inference.py                      (real inference with per-agent fallback wrapper)
│   ├── main.py                           (FastAPI + WebSocket + trace REST endpoints)
│   ├── agents/
│   │   ├── orchestrator.py               (SK orchestration with trace capture)
│   │   ├── intent_agent.py
│   │   ├── url_validation_agent.py
│   │   ├── scraping_agent.py
│   │   ├── product_matching_agent.py
│   │   ├── llpg_rule_agent.py
│   │   └── decision_agent.py
│   ├── plugins/
│   │   ├── compute_beat_price.py
│   │   ├── check_rsa_compliance.py
│   │   ├── normalize_unit_price.py
│   │   └── ...
│   ├── tracing/
│   │   ├── trace_models.py               (Pydantic: AgentTrace, AgentStep, TraceDecision)
│   │   ├── trace_store.py                (async SQLite read/write for traces)
│   │   └── trace_context.py              (context manager — auto-captures agent steps)
│   └── data/
│       └── loader.py                     (CSV data access layer)
├── frontend/
│   ├── package.json                      (React + Vite + TypeScript)
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── App.tsx
│       ├── pages/
│       │   └── DemoPage.tsx              (Main dual-panel layout)
│       ├── components/
│       │   ├── ChatPanel.tsx             (Left — conversation)
│       │   ├── AgentFlowPanel.tsx        (Right — agent steps timeline + trace viewer)
│       │   ├── AgentOrchestrationBar.tsx (Top — pipeline progress)
│       │   ├── ProductComparisonCard.tsx (Side-by-side product comparison)
│       │   ├── MessageBubble.tsx         (Chat message with image support)
│       │   ├── ScreenshotViewer.tsx      (Lightbox for screenshots)
│       │   └── TraceViewer.tsx           (Collapsible JSON tree for full trace)
│       ├── hooks/
│       │   └── useWebSocket.ts           (WebSocket connection hook)
│       ├── types/
│       │   └── index.ts                  (TypeScript interfaces)
│       └── styles/
│           └── theme.ts                  (Fluent UI theme customization)
├── plan/
│   └── mvp-data-generation-demo-ui-plan.md  (this file)
└── docs/                                 (existing architecture docs)
```

---

## Assumptions

| # | Assumption | Impact |
|---|---|---|
| 1 | Image URLs are placeholder patterns for generated data | Real CDN URLs come from actual product feed in production |
| 2 | ScrapingAgent uses real Playwright scraping when URL is provided, CSV fallback otherwise | Aligns with Req 2.1 (real-time scraping), Req 2.3 (hybrid), Req 8.1 (< 3–6 sec SLA). Screenshots captured during real scrapes; placeholder images used for CSV fallback |
| 3 | Semantic Kernel agents use **real Azure OpenAI models** deployed in Microsoft AI Foundry | Inference is attempted first; falls back to pre-computed responses **only** on failure (network error, quota exceeded, deployment unavailable) |
| 4 | WebSocket used for real-time agent flow visualization | Gives the "live thinking" effect for decision-makers |
| 5 | Fluent UI chosen for UI framework | Aligns with Microsoft ecosystem (Azure, Teams), enterprise-grade look |
| 6 | Demo runs locally | `uvicorn` backend on port 8000, Vite frontend on port 5173, CORS configured |
| 7 | RSA floor price is an internal business policy, not NSW law | NSW has no legislated minimum unit price; NT is the only Aus jurisdiction with one ($1.30/std drink) |
| 8 | Beat amount of $0.01 is industry standard | Standard practice for "lowest price guarantee" programs |
| 9 | CSV files are the temporary data source for MVP | Production will use Azure Cosmos DB, Azure AI Search, and real product feeds |
| 10 | Product catalogue of 50 items is sufficient for demo | Covers all major categories (beer, wine, spirits, RTD, cider) |
| 11 | Agent traces stored in local SQLite for demo | Production uses Event Hubs `audit-events` → Fabric Eventhouse `AuditTrail` KQL table |
| 12 | Trace captures per Req 7.1 (audit trail) and Req 7.2 (decision traceability) | Simplified storage but same data fidelity as production design |
| 13 | Azure AI Foundry credentials provided via `.env` file | Production uses managed identity via `DefaultAzureCredential` |
| 14 | Playwright used for web scraping (replacing Puppeteer in `package.json`) | Aligns with architecture spec (Azure Container Apps + KEDA + Playwright Workers); first-class Python SDK |

---

## Verification

| Check | How to Verify |
|---|---|
| Data generation | Run `python scripts/generate_data.py` — verify 50 products + 100 competitor rows with valid image/URL/screenshot fields |
| Backend starts | Run `cd backend && uvicorn main:app --reload` — verify FastAPI starts and WebSocket responds |
| Frontend loads | Run `cd frontend && npm run dev` — verify React app loads with dual-panel layout |
| End-to-end test | Send "I found VB 24-pack cheaper at Liquorland for $48.99" → ChatPanel shows bot response with product comparison card, AgentFlowPanel shows all 6 steps green, decision badge shows "AUTO-APPROVED" |
| RSA compliance | Verify no competitor beat price falls below `cost_price * 1.05` |
| Beat formula routing | Verify auto-approve/review/reject routing matches defined thresholds |
| Real inference | Set valid Azure OpenAI credentials in `.env` → send a message → `AgentFlowPanel` shows green "AI" badges on all agent steps |
| Fallback mode | Remove/invalidate Azure credentials → send same message → agents still respond, `AgentFlowPanel` shows amber "Fallback" badges, trace records `"inference_mode": "fallback"` |
| Trace storage | After a completed flow → `GET /api/traces` returns the trace → `GET /api/traces/{id}` returns all 6 agent steps with timing, input/output, and rule-level JSON |
| Trace in UI | After flow completes → "View Full Trace" link appears in AgentFlowPanel → clicking opens trace viewer with collapsible JSON tree |
| Req 7.1 compliance | Trace includes competitor name, matched SKU, competitor price, own price, and all rule decisions |
| Req 7.2 compliance | `LLPGRuleAgent` step `raw_json` contains RSA check result, beat formula result, stock-for-stock evaluation |
| Real scraping (URL) | Send a message with a valid competitor URL (e.g., `liquorland.com.au/...`) → ScrapingAgent navigates via Playwright, extracts price, captures screenshot → `AgentFlowPanel` shows scrape step with "Real" badge and screenshot thumbnail |
| Scraping fallback (no URL) | Send "VB is cheaper at Liquorland for $48.99" (no URL) → ScrapingAgent falls back to CSV lookup → trace records `"scrape_mode": "csv_fallback"` with reason |
| Scrape SLA | Real Playwright scrape completes within 3–6 seconds (Req 8.1) |

---

## Key Decisions

| Decision | Chose | Over | Rationale |
|---|---|---|---|
| Frontend framework | React + Vite + TypeScript | Next.js | Simpler setup, aligns with Azure Static Web Apps, no SSR needed |
| Backend framework | Python FastAPI + Semantic Kernel | Node.js Express | Aligns with multi-agent architecture, SK Python SDK is mature, pandas for CSV |
| UI component library | Fluent UI | Material UI / Tailwind | Microsoft ecosystem alignment, enterprise look for Endeavour demo |
| Real-time protocol | WebSocket | Server-Sent Events | Bidirectional communication needed for chat + agent updates |
| Layout design | Dual-panel (Chat + Agent Flow) | Single chat panel | "Agent Thinking" panel is the key differentiator — makes AI transparent |
| RSA floor model | Cost + 5% margin (MVP) | Per-standard-drink model | Simpler for MVP; per-drink model can be added in Phase 2 |
| Competitors | Liquorland + Liquorland Warehouse + BoozeBud | IGA / independents | Fragmented web presence of independents unsuitable for MVP |
| Data format | CSV files | Mock API / database | Fastest for MVP; easy to replace with real data feeds later |
| Default inference mode | Real Azure OpenAI first, fallback on failure | Mock-first with opt-in real AI | User requirement — MVP uses real models deployed in AI Foundry; fallback is safety net only |
| Fallback granularity | Per-agent independent fallback | All-or-nothing | If one agent's inference fails, others continue using real AI; maximizes real inference usage |
| Trace storage (demo) | Local SQLite | Event Hubs + KQL Eventhouse | Simplifies demo setup while preserving same data schema; easy to swap for production |
| Credential management | `.env` + `DefaultAzureCredential` | Hardcoded keys | Secure; supports local dev (API key) and Azure deployment (managed identity) |
| Scraping technology | Playwright (Python) | Puppeteer (Node.js in `package.json`) | Architecture spec mandates Playwright; first-class Python SDK; better Azure Container Apps + KEDA integration |
| Scraping mode | Real scrape first, CSV fallback | CSV-only simulation | Aligns with Req 2.1 (real-time scraping), Req 2.3 (hybrid), and corrected Assumption #3 philosophy (real-first) |
