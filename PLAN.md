# Capstone Implementation & Verification Roadmap (Track A: Tier-1 Deflection)

> **Soft Suave AI Engineering League — Week 12 Final Capstone**  
> **Status**: 100% Complete & Verified

---

## 1. Milestone Tracking

- [x] **Milestone 1: Corpus & Multi-Policy Data Foundation**
  - Current 30-day policy: [`data/help_center/refund-policy-current-30day.md`](file:///d:/chat%20bot/data/help_center/refund-policy-current-30day.md)
  - Legacy 14-day policy: [`data/help_center/refund-policy-legacy-14day.md`](file:///d:/chat%20bot/data/help_center/refund-policy-legacy-14day.md)
  - Shipping SLA matrix: [`data/help_center/shipping-sla-matrix.md`](file:///d:/chat%20bot/data/help_center/shipping-sla-matrix.md)
  - Product changelog: [`data/help_center/product-changelog.md`](file:///d:/chat%20bot/data/help_center/product-changelog.md)
  - 40 Zendesk macros: [`data/help_center/zendesk-macros.json`](file:///d:/chat%20bot/data/help_center/zendesk-macros.json)
  - Customer DB with PII: [`data/help_center/customer_orders_entitlements.json`](file:///d:/chat%20bot/data/help_center/customer_orders_entitlements.json)

- [x] **Milestone 2: FastMCP Service Implementation**
  - Server: [`app/mcp_server.py`](file:///d:/chat%20bot/app/mcp_server.py) (`SupportTriageMCPService`)
  - Tools: `order_lookup_mcp`, `entitlement_check_mcp`, `search_help_center_mcp`, `escalate_ticket_mcp`
  - External reviewer client: [`fresh_eyes_client.py`](file:///d:/chat%20bot/fresh_eyes_client.py)

- [x] **Milestone 3: Span-Level Observability & Strict PII Redaction**
  - Engine: [`app/capstone_logger.py`](file:///d:/chat%20bot/app/capstone_logger.py)
  - Structured logs: [`logs/capstone_traces.jsonl`](file:///d:/chat%20bot/logs/capstone_traces.jsonl)
  - Zero email / address leakage to disk.

- [x] **Milestone 4: ReAct Agent Loop with Dynamic Tool Discovery**
  - Core Assistant: [`app/capstone_agent.py`](file:///d:/chat%20bot/app/capstone_agent.py)
  - Enforces entitlement verification before refund / shipping commitments.
  - Generates version-qualified slug citations (`help-center/refund-policy-current-30day` vs `help-center/refund-policy-legacy-14day`).

- [x] **Milestone 5: 30-Case Integrated Evaluation Suite**
  - Benchmark: [`tests/capstone_eval_set.json`](file:///d:/chat%20bot/tests/capstone_eval_set.json)
  - Evaluator: [`app/capstone_eval.py`](file:///d:/chat%20bot/app/capstone_eval.py)
  - 5 deterministic assertions before judge.
  - Validated Judge Agreement: 96.0% (24/25) against [`labels_25.json`](file:///d:/chat%20bot/labels_25.json).

- [x] **Milestone 6: Trajectory Benchmark & Gap Analysis**
  - Benchmark: [`app/capstone_trajectory.py`](file:///d:/chat%20bot/app/capstone_trajectory.py)
  - 10 multi-hop cases; tool accuracy 86.7%; outcome-vs-trajectory gap 20.0%.

- [x] **Milestone 7: Bonus Challenge — Second-Contact Simulation**
  - Evaluator: [`app/capstone_second_contact.py`](file:///d:/chat%20bot/app/capstone_second_contact.py)
  - Gross Deflection (100.0%) vs Simulated Re-Open (50.0%) $\to$ Net Deflection (50.0%).

- [x] **Milestone 8: Closed Failure-to-Test Loop**
  - Unit Tests: [`tests/test_closed_failure_loop.py`](file:///d:/chat%20bot/tests/test_closed_failure_loop.py)
  - 3 automated unit tests permanently guarding Charlie's Day 18 ticket.

- [x] **Milestone 9: Single Entry Point CLI**
  - Entry point: [`app/main.py`](file:///d:/chat%20bot/app/main.py)
  - `python -m app.main capstone [--eval | --trajectory | --second-contact | --failure-loop | --fresh-eyes]`

- [x] **Milestone 10: Complete Submission Deliverables Documentation**
  - [`README.md`](file:///d:/chat%20bot/README.md)
  - [`SEAM_LIST.md`](file:///d:/chat%20bot/SEAM_LIST.md)
  - [`ARCHITECTURE.md`](file:///d:/chat%20bot/ARCHITECTURE.md)
  - [`EVAL_REPORT.md`](file:///d:/chat%20bot/EVAL_REPORT.md)
  - [`ERROR_TAXONOMY.md`](file:///d:/chat%20bot/ERROR_TAXONOMY.md)
  - [`TRAJECTORY_REPORT.md`](file:///d:/chat%20bot/TRAJECTORY_REPORT.md)
  - [`TRACE_LOG.md`](file:///d:/chat%20bot/TRACE_LOG.md)
  - [`KNOWN_WEAKNESSES.md`](file:///d:/chat%20bot/KNOWN_WEAKNESSES.md)
  - [`COST_AND_CAPACITY.md`](file:///d:/chat%20bot/COST_AND_CAPACITY.md)
  - [`FRESH_EYES_REVIEW.md`](file:///d:/chat%20bot/FRESH_EYES_REVIEW.md)
  - [`DEMO_SCRIPT.md`](file:///d:/chat%20bot/DEMO_SCRIPT.md)
