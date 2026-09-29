# Agentic Support & Policy Chatbot (Week 7 - Week 9 Implementation)

An autonomous, multi-agent Customer & Employee Support ReAct Engine built with Agentic RAG, Trajectory Evaluation, Prompt Injection Defenses, and Model Context Protocol (MCP) tool discovery.

---

## 🌟 Key Features Across Modules

### 1. Hand-Built ReAct Agent Loop (Week 7)
* Autonomous step-by-step reasoning (Plan -> Act -> Observe -> Repeat).
* Budget Guardrails: Max Steps (5), Token Budget (4,000 tokens), Timeout (15s), and Loop Detection.
* Memory architecture: Short-Term Scratchpad & Long-Term JSON ticket resolution persistence.

### 2. Failure Mode Evaluation & Prompt Injection Defense (Week 8)
* Trajectory Evaluation: Detects outcome-vs-trajectory gaps (correct final answer via flawed/looped path).
* Injection Defense: Detects direct & indirect prompt injection attacks, sanitizes inputs, and wraps untrusted retrieved documents in `[UNTRUSTED DOCUMENT CONTENT]` tags.

### 3. Model Context Protocol (MCP) & A2A Integration (Week 9)
* **MCP Host & Client**: Dynamically discovers available tools over JSON-RPC handshakes without hard-coded signatures.
* **Ticket History MCP Server (Track A)**: Independent FastMCP server (`TicketHistoryService`) exposing ticket lookup, resolution history, math reimbursement, and auth-protected escalation.
* **Zero-Code-Change Expansion**: Demonstrates bolting on a 2nd MCP server (`PolicyAnalyticsService`) with zero changes to `HandBuiltReActAgent`.
* **Security & Access Control**: Requires `auth_token='admin-secret'` on restricted tools.
* **Recoverable Error Handling**: Returns structured JSON errors over MCP without server/client crashes.
* **Agent-to-Agent (A2A)**: External partner agents can plug into and call our MCP server.

---

## 🚀 Quick Start & Evaluation Demos

### Run Week 9 MCP Benchmark
```bash
python -m app.week9_eval
```

### Run Week 8 Trajectory & Security Benchmark
```bash
python -m app.week8_eval
```

### Run Main Agent CLI
```bash
python -m app.main agent "Check details for ticket TICK-101 and calculate reimbursement"
```

---

## 📚 Technical Documentation

* [`WEEK_7_IMPLEMENTATION.md`](file:///d:/chat%20bot/WEEK_7_IMPLEMENTATION.md): Agentic RAG & ReAct Loop Architecture.
* [`WEEK_8_IMPLEMENTATION.md`](file:///d:/chat%20bot/WEEK_8_IMPLEMENTATION.md): Trajectory Evaluation, Loop Detection & Injection Defenses.
* [`WEEK_9_IMPLEMENTATION.md`](file:///d:/chat%20bot/WEEK_9_IMPLEMENTATION.md): MCP Concepts, Host/Client/Server Roles, JSON-RPC Messages, & Mentor Q&A.
