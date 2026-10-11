# Production End-to-End Trace Audit

> **Full Span-Level Telemetry for Charlie's Day 18 Refund Ticket**  
> **Trace File Source**: [`logs/capstone_traces.jsonl`](file:///d:/chat%20bot/logs/capstone_traces.jsonl)  
> **Trace Identifier**: `tr-capstone-7f0bb843`  
> **Soft Suave AI Engineering League — Week 12 Capstone**

---

## 1. Trace Overview & Request Context

This trace captures the complete execution of the historical CEO escalation failure scenario: Customer Charlie (Order #ORD-503) requesting a refund 18 days after delivery.

```json
{
  "trace_id": "tr-capstone-7f0bb843",
  "ticket_id": "TICK-103",
  "timestamp": "2026-10-11T11:29:13.609047+00:00",
  "customer_inquiry": "Customer Charlie (Order #ORD-503) requests a refund for wireless headset purchased 18 days ago ($85.00). The old macro says 14 days is expired. Can we approve?",
  "resolution_status": "ok",
  "deflected": true,
  "cited_policy_slug": "help-center/refund-policy-current-30day",
  "entitlement_checked": true,
  "pii_redacted": true,
  "total_latency_ms": 12.11,
  "total_tokens": 1599,
  "total_cost_usd": 0.000559
}
```

---

## 2. Span Waterfall & Latency/Cost Breakdown

The trace survives 9 distinct spans across the ReAct agent boundary, the FastMCP JSON-RPC boundary, and the Help Centre retrieval engine.

| Span ID | Span Name | Layer / Hop | Latency | Tokens | Cost (USD) | Trace ID Preserved | PII Redacted |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `sp-4e5fed` | `ticket_ingress` | API Gateway | 0.00 ms | 39 | $0.000006 | `tr-capstone-7f0bb843` | YES |
| `sp-837224` | `agent_react_step_1` | ReAct Agent | 0.01 ms | 175 | $0.000042 | `tr-capstone-7f0bb843` | YES |
| `sp-3db7a8` | `mcp_hop_order_lookup_mcp` | FastMCP Server | 4.22 ms | 122 | $0.000060 | `tr-capstone-7f0bb843` | YES |
| `sp-60f0dd` | `agent_react_step_2` | ReAct Agent | 0.02 ms | 220 | $0.000051 | `tr-capstone-7f0bb843` | YES |
| `sp-f2247e` | `mcp_hop_entitlement_check_mcp` | FastMCP Server | 4.28 ms | 108 | $0.000051 | `tr-capstone-7f0bb843` | YES |
| `sp-92c8b9` | `agent_react_step_3` | ReAct Agent | 0.01 ms | 230 | $0.000053 | `tr-capstone-7f0bb843` | YES |
| `sp-cfe506` | `mcp_hop_search_help_center_mcp` | FastMCP Server | 3.26 ms | 390 | $0.000220 | `tr-capstone-7f0bb843` | YES |
| `sp-e42401` | `agent_react_step_4` | ReAct Agent | 0.01 ms | 315 | $0.000076 | `tr-capstone-7f0bb843` | YES |
| `sp-4e16c9` | `ticket_egress` | API Gateway | 0.00 ms | 0 | $0.000000 | `tr-capstone-7f0bb843` | YES |
| **TOTAL** | **End-to-End Ticket Lifecycle** | **Full System** | **12.11 ms** | **1,599** | **$0.000559** | **100% Intact** | **100% Held** |

---

## 3. Span Event Details & Metadata

### Span 1: `ticket_ingress`
- **Span ID**: `sp-4e5fed`
- **Metadata**: `{"ticket_id": "TICK-103", "ingress_channel": "cli_capstone"}`
- **Action**: Ingestion of customer ticket text into observable pipeline.

### Span 2: `agent_react_step_1`
- **Span ID**: `sp-837224`
- **Thought**: *"Check order and customer purchase record for ORD-503."*
- **Action**: Invokes `order_lookup_mcp(order_id="ORD-503", trace_id="tr-capstone-7f0bb843")`.

### Span 3: `mcp_hop_order_lookup_mcp` (MCP Hop 1)
- **Span ID**: `sp-3db7a8`
- **Tool Executed**: `order_lookup_mcp` over FastMCP RPC.
- **Trace Context**: `trace_id` successfully passed into tool parameters and verified in log record.
- **Observation**:
  ```json
  {
    "order_id": "ORD-503",
    "customer_id": "CUST-103",
    "customer_name": "Charlie",
    "product": "Wireless Noise-Canceling Headset",
    "amount": 85.00,
    "purchase_days_ago": 18,
    "condition": "unopened",
    "customer_email": "[REDACTED_EMAIL]",
    "shipping_address": "[REDACTED_ADDRESS]"
  }
  ```

### Span 4: `agent_react_step_2`
- **Span ID**: `sp-60f0dd`
- **Thought**: *"Verify customer account plan tier and refund terms for CUST-103 before making commitments."*
- **Action**: Invokes `entitlement_check_mcp(customer_id="CUST-103", trace_id="tr-capstone-7f0bb843")`.

### Span 5: `mcp_hop_entitlement_check_mcp` (MCP Hop 2)
- **Span ID**: `sp-f2247e`
- **Tool Executed**: `entitlement_check_mcp` over FastMCP RPC.
- **Trace Context**: Same `trace_id: tr-capstone-7f0bb843` preserved.
- **Observation**:
  ```json
  {
    "customer_id": "CUST-103",
    "plan_tier": "standard_active_30day",
    "refund_window_days": 30,
    "applicable_policy_slug": "help-center/refund-policy-current-30day",
    "is_legacy_account": false
  }
  ```

### Span 6: `agent_react_step_3`
- **Span ID**: `sp-92c8b9`
- **Thought**: *"Retrieve official customer refund and returns policy terms."*
- **Action**: Invokes `search_help_center_mcp(query="refund policy current 30 day return window", trace_id="tr-capstone-7f0bb843")`.

### Span 7: `mcp_hop_search_help_center_mcp` (MCP Hop 3)
- **Span ID**: `sp-cfe506`
- **Tool Executed**: `search_help_center_mcp` over FastMCP RPC.
- **Observation**: Retrieves `help-center/refund-policy-current-30day` Section 1: Standard 30-day calendar return window with original packaging.

### Span 8: `agent_react_step_4`
- **Span ID**: `sp-e42401`
- **Thought**: *"Customer Charlie requested refund 18 days after purchase. Verified account is STANDARD_CURRENT on Current 30-Day Policy [help-center/refund-policy-current-30day] (NOT the retired 14-day terms). Full refund of $85 approved."*
- **Action**: Generates final deflection answer.

### Span 9: `ticket_egress`
- **Span ID**: `sp-4e16c9`
- **Metadata**: `{"deflected": true, "cited_slug": "help-center/refund-policy-current-30day"}`
- **Final Output**:
  > *"For Ticket TICK-103 (Order #ORD-503): Your refund request of $85.00 for the unopened wireless headset is approved under our Current 30-Day Return Policy [help-center/refund-policy-current-30day] (Version 2.0 Current, applicable to active standard accounts). Approved refund will be credited in 5 to 7 business days."*

---

## 4. PII Hygiene & Redaction Proof

The PII line was strictly held across all hops:
1. **Raw Database State**: Contains `"email": "charlie.davis@techconsult.org"` and `"shipping_address": "789 Pine Road, Austin, TX 78701"`.
2. **Log Record State**: Intercepted and sanitized by `CapstoneObservabilityManager.sanitize_pii()`:
   - Email scrubbed to `[REDACTED_EMAIL]`.
   - Street address scrubbed to `[REDACTED_ADDRESS]`.
3. **Audit Verification**: Grepping `logs/capstone_traces.jsonl` for `"@techconsult.org"` or `"Austin, TX"` yields **0 matches**. Zero customer PII leaked to disk.
