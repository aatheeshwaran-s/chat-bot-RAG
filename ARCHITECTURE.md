<!-- Soft Suave · The AI Engineering League -->
# One-Page Architecture Sketch: Tier-1 Deflection Assistant

**Track**: A — Customer Support Tickets  
**System**: Tier-1 Deflection Assistant with Entitlement Verification & FastMCP Integration  
**Author**: Capstone Engineering Lead  

---

## 1. System Topology & Data Flow

```
                                      [ INCOMING SUPPORT TICKET ]
                                  (Email / Portal / Webhook Payload)
                                                 │
                                                 ▼
               ┌──────────────────────────────────────────────────────────────────┐
               │              SINGLE CLI ENTRY POINT (app/main.py)                │
               │                   - Trace ID Generation                          │
               │                   - Ingress PII Scrubbing Layer                  │
               └─────────────────────────────────┬────────────────────────────────┘
                                                 │
                                                 ▼
        ┌─────────────────────────────────────────────────────────────────────────────────┐
        │                 HAND-BUILT REACT AGENT LOOP (app/capstone_agent.py)              │
        │                  Budget Controls: Max 5 Steps | 15s Timeout | 4,000 Tokens      │
        └───────┬───────────────────────────────┬─────────────────────────────────┬───────┘
                │                               │                                 │
         Step 1: Order Data              Step 2: Entitlement              Step 3: Policy Retrieval
                │                               │                                 │
                ▼                               ▼                                 ▼
   ┌──────────────────────────┐    ┌──────────────────────────┐    ┌──────────────────────────┐
   │    order_lookup_mcp      │    │  entitlement_check_mcp   │    │  search_help_center_mcp  │
   │  (Customer Order DB)     │    │  (Terms: 30-day vs 14-d) │    │  (Dual Help-Center RAG)  │
   └────────────┬─────────────┘    └────────────┬─────────────┘    └────────────┬─────────────┘
                │                               │                               │
                └───────────────────────┬───────┴───────────────────────────────┘
                                        │
                                        ▼  [ FastMCP Tool Transport (stdio / JSON-RPC) ]
   ┌──────────────────────────────────────────────────────────────────────────────────────┐
   │                    SupportTriageMCPService (app/mcp_server.py)                       │
   │      - Propagates trace_id across process hops                                       │
   │      - Enforces read-only DB scoping                                                 │
   │      - Sanitizes PII before responding                                               │
   └────────────────────────────────────┬─────────────────────────────────────────────────┘
                                        │
                                        ▼
   ┌──────────────────────────────────────────────────────────────────────────────────────┐
   │                          SYNTHESIS & CITATION ENGINE                                 │
   │      - Formulates final customer reply with clickable Help-Centre slug               │
   │      - Explicitly names policy version: Current 30-Day vs Retired 14-Day Terms       │
   │      - Routes out-of-scope / VIP tickets to escalate_ticket_mcp                      │
   └────────────────────────────────────┬─────────────────────────────────────────────────┘
                                        │
                                        ▼
   ┌──────────────────────────────────────────────────────────────────────────────────────┐
   │                    DISTRIBUTED OBSERVABILITY (app/capstone_logger.py)                │
   │      - Unified Trace ID intact from Ticket In to Answer Out                          │
   │      - Per-Span Latency & Token Cost Breakdown                                       │
   │      - Zero customer email or address logged to disk                                 │
   └──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Where the Model Calls Happen

Every ticket execution involves **two distinct model touchpoints** (or deterministic intelligent rule-based equivalents during offline mode):

1. **ReAct Planner Model Calls** (`app/capstone_agent.py::_step_reasoner`):
   - **Invocation**: 2 to 4 sequential prompt loops per ticket.
   - **Context Window**: System instructions + dynamic MCP tool signatures + scratchpad history.
   - **Average Size**: ~450 prompt tokens, ~55 completion tokens per step.
   - **Task**: Decides whether to query order DB, verify entitlement, search help center, or output final resolution.

2. **Resolution Synthesis Model Call** (`app/capstone_agent.py` Step 4):
   - **Invocation**: Final step.
   - **Context Window**: Grounded observations from `order_lookup_mcp`, `entitlement_check_mcp`, and `search_help_center_mcp`.
   - **Task**: Drafts empathetic, compliant customer resolution quoting the verified policy slug.

---

## 3. Where the Money Goes (Unit Economics & Cost Flow)

### Per-Ticket Financial Breakdown (Gemini 2.5 Flash / GPT-4o-mini Pricing):
- **Input Token Price**: \$0.15 per 1,000,000 tokens (\$0.00000015 / token)
- **Output Token Price**: \$0.60 per 1,000,000 tokens (\$0.00000060 / token)

| Execution Span | Operations Performed | Tokens (Prompt + Compl) | Cost per Span (\$ USD) | % of Total Cost |
|---|---|---|---|---|
| **Span 1: `ticket_ingress`** | Parse ticket string, PII scrub | 60 in + 0 out | \$0.000009 | 1.6% |
| **Span 2: `agent_react_step_1`** | Plan order lookup | 410 in + 35 out | \$0.000083 | 14.8% |
| **Span 3: `mcp_order_lookup`** | MCP Tool Hop + DB retrieval | 30 in + 42 out | \$0.000030 | 5.4% |
| **Span 4: `agent_react_step_2`** | Plan entitlement check | 490 in + 40 out | \$0.000098 | 17.5% |
| **Span 5: `mcp_entitlement_check`** | MCP Tool Hop + terms check | 30 in + 38 out | \$0.000027 | 4.8% |
| **Span 6: `agent_react_step_3`** | Plan policy search | 560 in + 40 out | \$0.000108 | 19.3% |
| **Span 7: `mcp_search_help_center`**| MCP Tool Hop + RAG search | 30 in + 65 out | \$0.000044 | 7.9% |
| **Span 8: `agent_react_step_4`** | Synthesis & Citation Drafting | 680 in + 65 out | \$0.000141 | 25.2% |
| **Span 9: `ticket_egress`** | Final trace commit to JSONL | 0 in + 0 out | \$0.000000 | 0.0% |
| **TOTAL PER TICKET** | **End-to-End Deflected Request** | **2,290 Prompt / 325 Compl** | **\$0.000559** | **100.0%** |

### Macro Business Economics:
- **Human Tier-1 Agent Loaded Cost**: \$3.50 per ticket (\$21.00/hr ÷ 6 tickets/hr).
- **AI Deflection Assistant Cost**: \$0.0034 per ticket (including embedding index amortizations & logging storage).
- **Net Margin Improvement**: **\$3.4966 saved per deflected ticket (99.9% cost reduction)**.
- **Monthly Savings at 2,000 Tickets (65% Deflection = 1,300 tickets)**: **\$4,545.58 per month net savings**.

---

## 4. Architectural Guardrails & Invariants

1. **The Entitlement Precondition Invariant**: The agent cannot commit to a refund or quote delivery SLAs without calling `entitlement_check_mcp`. If violated, deterministic assertion 4 rejects the output.
2. **The Dual-Corpus Disambiguation Invariant**: Both `refund-policy-current-30day` and `refund-policy-legacy-14day` live in the knowledge store. The prompt binds active customers to the 30-day slug, permanently guarding against the CEO escalation failure mode.
3. **The PII Perimeter Invariant**: Zero raw customer emails or addresses enter `logs/capstone_traces.jsonl`. Sanitization is executed recursively at the logger boundary before serialization.
