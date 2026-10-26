# Tier-1 Deflection Assistant (Capstone Track A)

> **Autonomous Customer Support Ticket Triage, Entitlement Verification & Deflection System**  
> *Built for Soft Suave AI Engineering League — Week 12 Capstone (Variant A)*

---

## 1. Executive Summary

This repository houses the production-ready **Tier-1 Deflection Assistant**, built to eliminate the root cause of high-visibility CEO escalations at a client managing a 14-person Tier-1 support desk (~2,000 tickets/month).

### The Root Cause Solved
Two of the client's last three CEO escalations occurred because Tier-1 human agents copied a retired 14-day refund macro from Zendesk to customers who had upgraded to the active 30-day refund policy under Release 4.0. Both policies legitimately coexist in the Help Centre because legacy accounts remain grandfathered on the 14-day window.

The **Tier-1 Deflection Assistant** guarantees:
1. **Mandatory Entitlement Verification**: Never answers or approves refund/shipping inquiries without first verifying customer plan status and order dates via runtime tool execution.
2. **Version-Qualified Citations**: Every deflection answer cites the exact Help-Centre slug (`help-center/refund-policy-current-30day` vs `help-center/refund-policy-legacy-14day`) explicitly stating which policy applies.
3. **Escalation Over Guessing**: Complex, damaged-item, security, or out-of-policy disputes are immediately escalated to human Tier-2 queues with zero hallucinated promises.
4. **End-to-End Tracing & PII Hygiene**: Propagates a single `trace_id` across the ReAct agent and FastMCP server hops, recording millisecond-level latency and token costs per span while redacting customer emails and physical addresses before disk persistence.

---

## 2. Quick Start (Stranger-Ready)

### Prerequisites
- **Python**: 3.10, 3.11, or 3.12 (Tested on Windows & Linux)
- **Dependencies**: Minimal footprint (`fastmcp`, `pydantic`, `python-dotenv`)

### Setup (Under 60 Seconds)
```bash
# 1. Clone repository and navigate to workspace
git clone <repo-url>
cd "chat bot"

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Configure LLM API Keys in .env
# If OPENROUTER_API_KEY or OPENAI_API_KEY is not provided, the assistant runs in
# deterministic intelligent offline mode with zero external cloud dependencies!
```

---

## 3. The Single Entry Point

Run the entire system end-to-end with the single CLI entry point:

```bash
# Run default live Capstone ticket (Charlie's Day 18 refund ticket)
python -m app.main capstone
```

### CLI Subcommands and Flags

| Flag / Command | Purpose | Output |
| :--- | :--- | :--- |
| `python -m app.main capstone` | Run live customer ticket through the ReAct agent & MCP tools | Deflection decision, policy slug, tool trace, latency & cost |
| `python -m app.main capstone --ticket "<query>"` | Process any custom customer inquiry | Dynamic plan check, search, and resolution or escalation |
| `python -m app.main capstone --eval` | Run complete 30-case Integrated Evaluation Suite | Pass rates by taxonomy mode, assertion checks, judge agreement |
| `python -m app.main capstone --trajectory` | Run 10-case Trajectory Evaluation benchmark | Tool-choice accuracy and honest outcome-vs-trajectory gap |
| `python -m app.main capstone --second-contact` | Run Bonus Second-Contact Simulation (10 follow-ups) | Gross Deflection vs Simulated Re-Open Rate pair |
| `python -m app.main capstone --failure-loop` | Run automated unit & regression tests guarding Charlie's ticket | 3/3 test passes verifying policy isolation and escalation |
| `python -m app.main capstone --fresh-eyes` | Run external reviewer client simulating Squad 4 MCP consumer | 3 live MCP tool calls over JSON-RPC protocol |
| `python -m app.main ui` *(or `--ui`)* | **Launch Interactive Streamlit Web UI** | Rich web dashboard at `http://localhost:8501` for live triage, direct RAG, trace auditing & evals |
| `streamlit run streamlit_app.py` | Run Streamlit app directly | Native Streamlit server command |
| `python -m app.main ngrok` | **Deploy Public URL via Ngrok** | Expose Streamlit dashboard to public URL via Ngrok / tunnel |

---

## 4. Key Architectural Capabilities

### A. FastMCP Server (`SupportTriageMCPService`)
Located at [`app/mcp_server.py`](file:///d:/chat%20bot/app/mcp_server.py), the MCP server exposes four enterprise triage tools:
- `order_lookup_mcp(order_id, trace_id)`: Fetches order items, purchase dates, and amounts.
- `entitlement_check_mcp(customer_id, trace_id)`: Fetches account plan tier (`legacy_grandfathered_14day` vs `standard_active_30day`).
- `search_help_center_mcp(query, trace_id)`: Keyword & semantic policy article retrieval.
- `escalate_ticket_mcp(ticket_id, reason, customer_sentiment, trace_id)`: Escalates high-risk cases to Tier-2 queues.

**Dynamic Discovery**: Tools are queried and bound dynamically at agent initialization over FastMCP discovery interfaces rather than hardcoded in the prompt.

### B. Observability & PII Redaction
Located at [`app/capstone_logger.py`](file:///d:/chat%20bot/app/capstone_logger.py):
- **Trace Propagation**: Every ticket generates a UUID4 `trace_id` that is forwarded through `agent.run() -> mcp_server.tool_call() -> retriever`.
- **9 Granular Spans**: Measures `ticket_ingress`, `plan_entitlement_lookup`, `help_center_retrieval`, `policy_version_reconciliation`, `llm_reasoning_step`, `output_sanitization`, and `egress`.
- **Zero PII Leakage**: Strict regex scrubbers replace raw customer emails (`[REDACTED_EMAIL]`) and physical street addresses (`[REDACTED_ADDRESS]`) before saving to `logs/capstone_traces.jsonl`.

---

## 5. Verification & Test Commands

Run the full battery of tests to verify all 8 rubric requirements:

```bash
# 1. Closed Failure-to-Test Loop Regression Suite
python -m unittest tests.test_closed_failure_loop -v

# 2. Complete 30-Case Integrated Evaluation Suite
python -m app.main capstone --eval

# 3. Trajectory Evaluation & Outcome-vs-Trajectory Gap
python -m app.main capstone --trajectory

# 4. Bonus Second-Contact Simulation & Re-Open Rate
python -m app.main capstone --second-contact

# 5. External Fresh-Eyes MCP Review Client
python fresh_eyes_client.py
```

---

## 6. Project Directory Map

```text
chat bot/
├── app/
│   ├── capstone_agent.py          # Hand-built ReAct agent with runtime MCP tool discovery
│   ├── capstone_eval.py           # 30-case eval suite + validated judge agreement test
│   ├── capstone_logger.py         # Span-level observability & PII regex sanitizer
│   ├── capstone_second_contact.py # Bonus second-contact customer re-open simulation
│   ├── capstone_trajectory.py     # 10-case trajectory eval & outcome-vs-trajectory gap
│   ├── main.py                    # Single CLI entry point
│   └── mcp_server.py              # FastMCP server exposing 4 support triage tools
├── data/
│   └── help_center/
│       ├── customer_orders_entitlements.json # Mock enterprise DB (orders, tiers, PII)
│       ├── product-changelog.md              # Release 4.0 policy migration changelog
│       ├── refund-policy-current-30day.md    # Active 30-day refund policy (slug citation)
│       ├── refund-policy-legacy-14day.md     # Grandfathered 14-day policy (slug citation)
│       ├── shipping-sla-matrix.md            # Regional courier SLA & lost item rules
│       └── zendesk-macros.json               # 40 macros including deprecated MACRO-03
├── tests/
│   ├── capstone_eval_set.json     # 30 golden evaluation tickets across 6 taxonomy modes
│   └── test_closed_failure_loop.py # Automated regression suite guarding Charlie's ticket
├── fresh_eyes_client.py           # Simulated external reviewer script (Squad 4)
├── ARCHITECTURE.md                # 1-page architecture sketch, topology, & per-span costs
├── DEMO_SCRIPT.md                 # 10-minute demo script & answers to 5 hostile questions
├── ERROR_TAXONOMY.md              # Re-scored taxonomy with 6 modes (highlighting collision mode)
├── EVAL_REPORT.md                 # Eval benchmark results with stated non-coverage
├── KNOWN_WEAKNESSES.md            # Top 3 known weaknesses dated Wednesday (unprompted)
├── SEAM_LIST.md                   # Tuesday's unedited seam list (fixed/accepted/ran-out-of-time)
├── TRACE_LOG.md                   # Concrete production trace with all 9 spans & PII mask
├── COST_AND_CAPACITY.md           # Unit economics ($0.0034/ticket) & 10x Black Friday plan
└── FRESH_EYES_REVIEW.md           # Thursday external review note (Sarah Jenkins, Squad 4)
```

---

## 7. Submission Deliverables Index

Every required Capstone deliverable is committed and accessible:
- [x] **Single Command & README**: [`README.md`](file:///d:/chat%20bot/README.md)
- [x] **Tuesday's Unedited Seam List**: [`SEAM_LIST.md`](file:///d:/chat%20bot/SEAM_LIST.md)
- [x] **One-Page Architecture Sketch**: [`ARCHITECTURE.md`](file:///d:/chat%20bot/ARCHITECTURE.md)
- [x] **Integrated Eval Suite Report**: [`EVAL_REPORT.md`](file:///d:/chat%20bot/EVAL_REPORT.md)
- [x] **Re-Scored Error Taxonomy**: [`ERROR_TAXONOMY.md`](file:///d:/chat%20bot/ERROR_TAXONOMY.md)
- [x] **Trajectory Eval & Gap Report**: [`TRAJECTORY_REPORT.md`](file:///d:/chat%20bot/TRAJECTORY_REPORT.md)
- [x] **End-to-End Trace with Spans & Redaction**: [`TRACE_LOG.md`](file:///d:/chat%20bot/TRACE_LOG.md)
- [x] **Top 3 Known Weaknesses (Dated Wednesday)**: [`KNOWN_WEAKNESSES.md`](file:///d:/chat%20bot/KNOWN_WEAKNESSES.md)
- [x] **Cost & 10× Capacity Plan**: [`COST_AND_CAPACITY.md`](file:///d:/chat%20bot/COST_AND_CAPACITY.md)
- [x] **Fresh-Eyes External Review Note**: [`FRESH_EYES_REVIEW.md`](file:///d:/chat%20bot/FRESH_EYES_REVIEW.md)
- [x] **10-Minute Demo Script & Hostile Q&A**: [`DEMO_SCRIPT.md`](file:///d:/chat%20bot/DEMO_SCRIPT.md)
