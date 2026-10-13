<!-- Soft Suave · The AI Engineering League -->
# Tuesday's Integration Seam List (Unedited)

**System**: Track A — Tier-1 Deflection Assistant (Customer Support Tickets)  
**Date Logged**: Tuesday, Week 12  
**Status Legend**: `[FIXED]` · `[ACCEPTED]` · `[RAN-OUT-OF-TIME]`

---

## 1. Context & Purpose
When individual weekly modules (Week 3 RAG, Week 7 ReAct Agent, Week 9 MCP Tool Discovery, Week 10 Multi-Agent Triage, Week 11 Observability) were integrated into a single entry point application, six critical subsystem boundaries ("seams") broke. This document records the unedited seam list as logged on Tuesday, with the operational resolution applied before Friday's AI Summit evaluation.

---

## 2. Unedited Seam Register

### SEAM-01: Agent ReAct Loop ↔ FastMCP Tool Invocation (NameError)
- **Subsystem Boundary**: Hand-Built Agent Loop (`app/agent.py` / `app/capstone_agent.py`) ↔ FastMCP Server (`app/mcp_server.py`).
- **Observed Failure**: When the agent invoked `search_help_center_mcp` over the dynamic MCP transport, execution crashed with `NameError: name 're' is not defined` inside the regex tokenizer.
- **Root Cause**: FastMCP tool methods run in isolated execution scopes; `import re` was missing at the module top level in `app/mcp_server.py`.
- **Status**: **`[FIXED]`**
- **Resolution**: Added explicit standard library imports (`import re`, `import glob`) and validated tool call serialization across all 7 FastMCP endpoints.

---

### SEAM-02: Scratchpad Memory ↔ Reasoner Keyword Desynchronization
- **Subsystem Boundary**: Agent Scratchpad Memory (`app/memory.py`) ↔ Offline Support Reasoner (`app/capstone_agent.py`).
- **Observed Failure**: Agent repeatedly called `order_lookup_mcp` three times on the same ticket, prematurely halting with `"Terminated due to duplicate tool loop"`.
- **Root Cause**: `_offline_support_reasoner` checked `if "observe" not in s_lower:`. However, `ShortTermMemory.get_scratchpad_str()` outputs `"Observation: ..."`, and `"observe"` is not a substring of `"observation"` due to character inflection.
- **Status**: **`[FIXED]`**
- **Resolution**: Updated parser condition to `if "observation:" not in s_lower:`, allowing phase-2 entitlement check and phase-3 help-center lookup to proceed smoothly.

---

### SEAM-03: Eval Benchmark Dataset Collision (W6 vs W10 File Overwrite)
- **Subsystem Boundary**: Week 6 Ticket Reply Judge Validation (`app/w6_eval.py`) ↔ Week 10 Multi-Agent Race (`app/week10_eval.py`).
- **Observed Failure**: `python -m app.w6_eval` crashed with `KeyError: 'ticket_eval_set'`.
- **Root Cause**: In Week 10, `tests/ticket_eval_set.json` was overwritten with a 10-ticket dataset keyed by `"tickets"`, removing the 26-case dataset expected by Week 6's judge calibration.
- **Status**: **`[FIXED]`**
- **Resolution**: Decoupled dataset storage into:
  1. `tests/w6_eval_set.json` (26 cases + 25 blind hand-labels for judge calibration).
  2. `tests/ticket_eval_set.json` (10 tickets for single vs multi-agent races).
  3. `tests/capstone_eval_set.json` (30 integrated cases across all 6 taxonomy modes).

---

### SEAM-04: Distributed Trace ID Preservation Across MCP Client-Server Hop
- **Subsystem Boundary**: Observability Manager (`app/capstone_logger.py`) ↔ MCP Client (`app/mcp_client.py`) ↔ MCP Server (`app/mcp_server.py`).
- **Observed Failure**: When the ReAct agent invoked tools over FastMCP, child tool spans generated new random trace IDs, breaking end-to-end request tracing.
- **Root Cause**: Tool parameters did not accept trace context envelopes, discarding incoming caller metadata.
- **Status**: **`[FIXED]`**
- **Resolution**: Injected `trace_id: str = ""` into all MCP tool signatures (`order_lookup_mcp`, `entitlement_check_mcp`, `search_help_center_mcp`, `escalate_ticket_mcp`). Passed caller's active trace ID through `_parse_input` and validated 100% preservation across hops in `tests/test_closed_failure_loop.py`.

---

### SEAM-05: Customer Data Privacy Line (PII Leakage in Squad-Readable Logs)
- **Subsystem Boundary**: Customer Entitlements DB (`customer_orders_entitlements.json`) ↔ Request Logger (`logs/capstone_traces.jsonl`).
- **Observed Failure**: Raw customer email addresses (`alice.j@corpnet.org`) and residential street addresses (`742 Evergreen Terrace, Springfield, OR`) were written verbatim into the request log.
- **Root Cause**: Database payload was dumped directly into trace record metadata without sanitization.
- **Status**: **`[FIXED]`**
- **Resolution**: Built recursive regex sanitizer `sanitize_pii()` in `app/capstone_logger.py` masking all emails to `[REDACTED_EMAIL]` and addresses to `[REDACTED_ADDRESS]`. Verified zero PII leakage in automated unit tests.

---

### SEAM-06: RAG Semantic Similarity ↔ Entitlement Tool Priority Desync
- **Subsystem Boundary**: Help-Center RAG Retriever (`app/retrieval.py` / `search_help_center_mcp`) ↔ Entitlement Checker (`entitlement_check_mcp`).
- **Observed Failure**: For Customer Charlie (Day 18), naive dense vector search retrieved Zendesk macro `MACRO-03` ("retired 14-day snippet") with 0.88 cosine similarity, causing the model to cite the superseded 14-day window and reject the customer.
- **Root Cause**: Retrieval scored text relevance without conditioning on the customer's actual plan entitlement in the database.
- **Status**: **`[FIXED]`**
- **Resolution**: Implemented two-stage decision guard:
  1. The agent MUST execute `entitlement_check_mcp` BEFORE generating refund resolution.
  2. If customer tier is `STANDARD_CURRENT`, the prompt strictly filters out the legacy 14-day policy and binds citations to `help-center/refund-policy-current-30day`.

---

## 3. Accepted Seams (Documented Constraints)

### SEAM-07: In-Memory BM25 Corpus Re-tokenization Overhead
- **Subsystem Boundary**: Lexical BM25 Engine (`app/hybrid.py`) ↔ Server Initialization.
- **Behavior**: On first invocation, BM25 tokenizes the 120 help-center documents in-memory (~120ms latency hit on cold start).
- **Status**: **`[ACCEPTED]`**
- **Rationale**: For Tier-1 volume (~2,000 tickets/month, ~3 req/hour), an initial 120ms cold-start delay is negligible. In-memory indexing avoids maintaining external Elastic/OpenSearch daemon dependencies.

---

## 4. Ran-Out-of-Time Seams (Backlog for v2)

### SEAM-08: Streaming Token SSE Over MCP WebSockets
- **Subsystem Boundary**: FastMCP Stdio Transport ↔ Real-Time Agent Streaming.
- **Behavior**: Currently, tool execution over FastMCP waits for full execution completion rather than streaming token deltas.
- **Status**: **`[RAN-OUT-OF-TIME]`**
- **Rationale**: Stdio transport delivers sub-20ms latency locally, which satisfies the SLA. WebSocket chunk streaming deferred to Q1 infrastructure refactor.
