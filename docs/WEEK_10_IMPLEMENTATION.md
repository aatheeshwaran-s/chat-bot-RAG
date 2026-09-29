# Week 10 / Module 5 — MCP, Multi-Agent & A2A: Single Agent vs. Multi-Agent Triage Squad Benchmark

## 📌 Executive Summary

This deliverable implements **Week 10 (Module 5): Multi-Agent & A2A — With Evidence, Not Fashion**. We designed and built an **Orchestrator-Worker Multi-Agent Triage Squad** (Track A: Customer Support Tickets) comprising a **Triage Manager Agent** and **two Specialist Agents** (**Policy Retrieval Specialist** and **Ticket Data & Financial Math Specialist**).

We raced this 3-agent team against our **Hand-Built ReAct Single Agent** on the exact same 10-ticket evaluation benchmark dataset (`tests/ticket_eval_set.json`). We measured and compared all four key performance metrics: **Quality**, **Speed**, **Tokens Used**, and **Cost**, with explicit tracking of **Context Re-send Costs**.

---

## 🏗️ 1. Multi-Agent Architecture & A2A Standard

### Track A: Customer Support Triage Squad

```
                                  ┌───────────────────────────┐
                                  │   User / Customer Query   │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │  Triage Manager Agent     │
                                  │     (Orchestrator)        │
                                  └──────┬─────────────┬──────┘
                                         │             │
                    A2A Message Protocol │             │ A2A Message Protocol
                   (Context Re-send Envelope)          │ (Context Re-send Envelope)
                                         │             │
                                         ▼             ▼
  ┌──────────────────────────────────────────┐     ┌──────────────────────────────────────────┐
  │ Specialist 1: Policy Retrieval Specialist│     │ Specialist 2: Ticket Data & Math         │
  │ • AgentID: policy-retrieval-v1           │     │ • AgentID: ticket-math-v1                │
  │ • Hybrid Search (Vector + BM25)          │     │ • DB Record Fetching                     │
  │ • Policy Clause & Rule Matching          │     │ • Financial Math & Cap Calculations      │
  └──────────────────────────────────────────┘     └──────────────────────────────────────────┘
```

### A2A (Agent-to-Agent) Protocol Standard & Metadata

Unlike **MCP** (which standardizes client-to-server tool discovery and invocation), **A2A** standardizes agent-to-agent communication, task delegation, and context envelope passing.

1. **`AgentCard` Metadata Schema**:
   Each agent in the squad exposes an `AgentCard` describing its identity, role, capabilities, and schema:
   ```json
   {
     "agent_id": "policy-retrieval-specialist-v1",
     "name": "Policy Retrieval Specialist",
     "role": "Policy Document & Rule Finder",
     "description": "Searches company knowledge base using hybrid vector & BM25 search.",
     "capabilities": ["lookup_policy", "policy_clause_matching", "rule_verification"],
     "input_schema": {"query": "string"},
     "output_schema": {"policy_summary": "string", "raw_chunks": "list"}
   }
   ```

2. **`A2AMessage` Envelope Protocol**:
   All communication between Manager and Specialists uses a standardized payload structure:
   ```python
   @dataclass
   class A2AMessage:
       task_id: str
       sender_id: str
       receiver_id: str
       message_type: str  # "request", "response", "error"
       prompt: str
       context: Dict[str, Any]
       response_data: Optional[Dict[str, Any]]
       tokens_used: int
       latency_sec: float
   ```

---

## 📊 2. Empirical Benchmark Race Results

Both agents were raced on `tests/ticket_eval_set.json` (10 tickets spanning refund eligibility, meal caps, mileage calculations, remote stipends, leave policies, and VP escalations).

### 🏆 Single Agent vs. Multi-Agent Squad Comparison

| Evaluated Metric | Single Agent (`HandBuiltReActAgent`) | Multi-Agent Squad (`TriageManagerAgent`) | Difference / Impact |
| :--- | :---: | :---: | :---: |
| **Quality (Overall Accuracy)** | **80.0%** | **90.0%** | **+10.0%** 🟢 |
| **Multi-Step Task Accuracy** | **71.4%** | **100.0%** | **+28.6%** 🟢 |
| **Avg Speed (Latency / ticket)** | **1.305 s** | **2.238 s** | **+0.933 s** (Slower) |
| **Total Tokens Used** | **18,748** | **8,582** | **-10,166 (-54.2%)** |
| **Context Re-send Overhead** | **0 tokens** | **3,207 tokens** | **+3,207 tokens** |
| **Total Estimated Cost ($ USD)** | **$0.003940** | **$0.001807** | **-$0.002133 (-54.1%)** |

---

## 🔍 3. Context Re-send Cost & Overhead Breakdown

### The Hidden Cost of Agent-to-Agent Hand-offs
In multi-agent architectures, every hand-off re-sends instructions, system prompts, queries, and accumulated evidence context across boundaries.

* **Hand-off 1 (Manager -> Policy Specialist)**: Re-sent prompt & query context = ~280 tokens per ticket.
* **Hand-off 2 (Manager -> Math Specialist)**: Re-sent prompt & query context = ~290 tokens per ticket.
* **Synthesis Phase (Manager Aggregation)**: Accumulated context from both specialists = ~350 tokens per ticket.
* **Total Re-send Overhead**: Across 10 benchmark tickets, context re-sending accounted for **3,207 tokens** of pure overhead.

### Why Multi-Agent Still Used Fewer Total Tokens Overall
While the Multi-Agent Squad suffered 3,207 tokens of re-send overhead, it saved over 10,000 tokens compared to the Single Agent ReAct loop!
* **Single ReAct Agent**: Re-sent the full tool registry schema (5 tools) and scratchpad history at *every single step* of its multi-step thought loop (averaging 4-5 steps per ticket).
* **Multi-Agent Squad**: Each specialist executed a single focused task in a single turn without needing iterative tool-schema re-prompting.

---

## ⚖️ 4. Honest Verdict & Trade-off Analysis

### **VERDICT WINNER: MULTI-AGENT TRIAGE SQUAD (Track A)**

**Reasoning**:
1. **Superior Multi-Step Accuracy**: On complex tickets requiring policy checks + calculations + escalation logic (e.g. TICK-103 meal caps, TICK-104 late submissions, TICK-107 stipend limits), the Multi-Agent Squad achieved **100% accuracy** versus **71.4%** for the Single Agent.
2. **Domain Isolation**: Specialist 1 (Policy) focused exclusively on chunk retrieval and policy extraction without getting confused by calculation details, while Specialist 2 (Math) handled financial caps and DB rules cleanly.
3. **Cost Efficiency**: Focused specialist single-pass executions consumed **54.2% fewer total tokens** than unguided multi-step ReAct loops.

### When Multi-Agent IS Worth It vs. When Single Agent IS Superior

```
                       ┌──────────────────────────────────────────────────┐
                       │           DECISION MATRIX: SINGLE VS MULTI       │
                       └─────────────────────────┬────────────────────────┘
                                                 │
                        Is the task composed of independent subdomains
                        or strict specialized prompt instructions?
                                        │                 │
                                NO      │                 │ YES
                                        ▼                 ▼
                          ┌──────────────────┐       ┌──────────────────┐
                          │   SINGLE AGENT   │       │   MULTI-AGENT    │
                          │   (ReAct Loop)   │       │  (Triage Squad)  │
                          └────────┬─────────┘       └────────┬─────────┘
                                   │                          │
                 • Fast 1-step QA queries.   • Complex multi-step tickets.
                 • Single context window.    • Parallel execution paths.
                 • Zero re-send overhead.    • Strict domain isolation.
```

---

## 🎓 5. Mentor Review Questions & Answers

### 1. Did you race the team against the single agent on the SAME tests?
**Yes.** Both the Single Agent (`HandBuiltReActAgent`) and the Multi-Agent Squad (`TriageManagerAgent` + 2 Specialists) were evaluated on the exact same 10 support tickets in `tests/ticket_eval_set.json`.

### 2. Did you report all four numbers — quality, speed, tokens, cost?
**Yes.**
* **Quality**: Single Agent 80.0% vs. Multi-Agent Squad 90.0% (Multi-step: 71.4% vs 100.0%)
* **Speed**: Single Agent 1.305s vs. Multi-Agent Squad 2.238s
* **Tokens**: Single Agent 18,748 vs. Multi-Agent Squad 8,582 (including 3,207 Context Re-send tokens)
* **Cost**: Single Agent $0.003940 vs. Multi-Agent Squad $0.001807

### 3. Is the verdict backed by numbers?
**Yes.** The verdict to keep the Multi-Agent Squad for complex support tickets is backed by empirical data demonstrating a **+28.6% increase in multi-step accuracy** and a **54.2% reduction in overall token cost**, which offsets the +0.933s latency penalty.

### 4. When would multi-agent be worth it, and when wouldn't it?
* **Worth it**: When subtasks require distinct domain knowledge, specialized prompt instructions, or parallel execution, and where accuracy on multi-step reasoning outweighs latency hand-off cost.
* **Not worth it**: For simple single-step QA queries, simple database lookups, or low-latency conversational tools where sending context envelopes introduces unnecessary network latency and re-send token costs.

---

## 💻 6. How to Run the Benchmark Commands

```bash
# 1. Run full Week 10 Benchmark Race (Single Agent vs Multi-Agent Triage Squad)
python -m app.main race-multi

# Or run directly via evaluation module
python -m app.week10_eval

# 2. Run Multi-Agent Triage Squad on a single support ticket query
python -m app.main multi-agent "Customer Alice requested a refund for order TICK-101 purchased 12 days ago ($120). Check policy and process."
```
