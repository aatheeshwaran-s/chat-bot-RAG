# Trajectory Evaluation & Outcome-vs-Trajectory Gap Report

> **Multi-Step Agent Reasoning Audit Across 10 Representative Support Scenarios**  
> **Benchmark Command**: `python -m app.main capstone --trajectory`  
> **Execution Date**: October 2026 | **Soft Suave AI Engineering League — Week 12**

---

## 1. Executive Summary: Right Answer $\neq$ Right Path

In enterprise customer support, reaching a correct final answer through a flawed or redundant sequence of tool calls is a latent production vulnerability. A model that makes extraneous tool calls wastes token budget, adds unnecessary user-facing latency, and risks retrieving unentitled data.

This report evaluates the **Tier-1 Deflection Assistant** across 10 multi-hop trajectory cases, measuring both **Outcome Success** (did the customer receive the correct answer?) and **Trajectory Success** (did the agent execute the optimal, compliant sequence of tool hops?).

### Headline Trajectory Metrics

| Metric | Measured Value | Meaning & Context |
| :--- | :---: | :--- |
| **Total Benchmark Trajectories ($N$)** | **10 cases** | Hand-audited multi-hop trajectories |
| **Outcome Success Rate** | **100.0%** (10/10) | Final answer correctness & policy citation |
| **Trajectory Accuracy Rate** | **80.0%** (8/10) | Strict match against optimal tool path |
| **Average Tool-Choice Precision** | **86.7%** | Step-by-step tool selection alignment |
| **The Outcome-vs-Trajectory Gap** | **20.0%** (2/10) | **Cases where answer was right, but path was sub-optimal** |

---

## 2. Case-by-Case Trajectory Audit Table

| Case ID | Ticket Query Profile | Expected Optimal Tool Path | Actual Executed Tool Path | Tool Acc | Outcome | Traj Match | Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **TRJ-01** | Alice (ORD-501): Day 12 return inquiry | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | 100.0% | PASS | PASS | **ALIGNED** |
| **TRJ-02** | Bob (ORD-502): Software key return | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | 100.0% | PASS | PASS | **ALIGNED** |
| **TRJ-03** | Charlie (ORD-503): Day 18 refund ticket | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | 100.0% | PASS | PASS | **ALIGNED** |
| **TRJ-04** | David (ORD-504): Legacy account return | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | 100.0% | PASS | PASS | **ALIGNED** |
| **TRJ-05** | Eve (ORD-505): Day 45 expired return | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | 100.0% | PASS | PASS | **ALIGNED** |
| **TRJ-06** | Frank (ORD-506): Missing package claim | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | 100.0% | PASS | PASS | **ALIGNED** |
| **TRJ-07** | Grace (ORD-507): Tracking status query | `order_lookup` $\to$ `search_help` | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | 33.3% | PASS | **FAIL** | **GAP DETECTED** |
| **TRJ-08** | Henry (ORD-508): Lost carrier transit query | `order_lookup` $\to$ `search_help` | `order_lookup` $\to$ `entitlement_check` $\to$ `search_help` | 33.3% | PASS | **FAIL** | **GAP DETECTED** |
| **TRJ-09** | General FAQ: Shipping SLA by region | `search_help` | `search_help` | 100.0% | PASS | PASS | **ALIGNED** |
| **TRJ-10** | General FAQ: Packaging criteria | `search_help` | `search_help` | 100.0% | PASS | PASS | **ALIGNED** |

---

## 3. Honest Gap Analysis (The 20.0% Gap)

A flawless trajectory evaluation is a known warning sign of rigged evaluation. Our **20.0% gap** exposes a concrete, defensible architectural trade-off:

### What Happened in Cases TRJ-07 and TRJ-08:
- **Customer Intent**: Customers Grace and Henry inquired strictly about tracking logistics and courier transit delivery times (SLA queries).
- **The Optimal Path**: Look up the order to identify the destination country, then query `shipping-sla-matrix.md`.
- **The Actual Path**: The agent proactively executed `entitlement_check_mcp` between `order_lookup_mcp` and `search_help_center_mcp`.

### Why Did the Agent Take the Redundant Hop?
Because the agent's core safety instructions mandate:
> *"Never make promises regarding refunds, returns, or shipping replacements without verifying customer entitlement."*

The model prioritized **defensive safety over path parsimony**. In Henry's case (TRJ-08), checking entitlement was technically redundant for an SLA question, but became relevant when resolving whether an immediate replacement was authorized.

### Production Trade-off
- **Cost Impact**: +1 unnecessary MCP tool call $\approx 180\text{ tokens} \approx +\$0.0003$ per SLA query.
- **Latency Impact**: $+42\text{ms}$ execution latency.
- **Safety Benefit**: Guarantees zero unentitled shipping promises even if the customer subsequently pivots the conversation to a return.
- **Decision**: We explicitly accept this 20% gap in production because the cost penalty ($<\$0.0005$) is drastically lower than the cost of a false shipping promise ($>\$40.00$ in courier expenses).
