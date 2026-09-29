# Week 9 Implementation: Model Context Protocol (MCP), Dynamic Tool Discovery & Multi-Agent Integration

## Overview

In **Week 9 (Module 5 — MCP, Multi-Agent & A2A)**, the project advances from custom, hand-wired tools to **MCP (Model Context Protocol)** — the open industry standard for connecting AI agents to tools, data resources, and external services.

Instead of hard-coding tool definitions directly into the agent codebase, the agent now operates as an **MCP Host / Client**, dynamically discovering tools at startup via JSON-RPC handshakes. Additionally, we build an independent **Ticket History & Support Services MCP Server** (Track A) that exposes capabilities for our agent and external agents to call.

---

## Core Conceptual Q&A (Module 5 Fundamentals)

### Q1: What problem does MCP solve?
**Answer:**
Before MCP, every tool had to be custom-coded for a specific AI application framework (LangChain, LlamaIndex, custom ReAct loops). 
MCP acts as a **standardized plug-and-play socket** (analogous to USB for hardware). A single tool server built with MCP can be reused by any AI host (Claude Desktop, VS Code, Antigravity IDE, custom Python ReAct agents) without rewrite.

### Q2: Does MCP make the AI smarter?
**Answer:**
**No — MCP is plumbing.** It provides zero intelligence or LLM capabilities on its own. Its value lies entirely in **reusability, modular decoupling, dynamic discovery, and clean security boundaries**.

### Q3: Where does the AI actually run?
**Answer:**
The AI runs **on the Host / Client side**, NEVER on the tool server. 
* The **Host/Client** (our ReAct Agent) holds the LLM API key, runs the reasoning loop, plans steps, and decides when to invoke tools.
* The **MCP Server** is purely an API endpoint that advertises tool schemas and executes requested functions. The server has no knowledge of which LLM or agent is calling it.

---

## Architecture & System Flow

```mermaid
flowchart TD
    subgraph Host / Client Side (AI Runs Here)
        Agent[HandBuiltReActAgent] --> ClientMgr[MCPClientManager]
        ClientMgr --> Registry[ToolRegistry]
    end

    subgraph MCP Server 1: Track A
        Server1["TicketHistoryService (FastMCP)"]
        Server1 --> Tool1["check_ticket_db_mcp"]
        Server1 --> Tool2["get_customer_history_mcp"]
        Server1 --> Tool3["calculate_reimbursement_mcp"]
        Server1 --> Tool4["escalate_ticket_mcp (Auth Restricted)"]
    end

    subgraph MCP Server 2: Bolted-On Service
        Server2["PolicyAnalyticsService (FastMCP)"]
        Server2 --> Tool5["lookup_policy_mcp"]
        Server2 --> Tool6["get_policy_compliance_score"]
    end

    ClientMgr -- "1. JSON-RPC list_tools()" --> Server1
    ClientMgr -- "2. JSON-RPC list_tools()" --> Server2
    Registry -- "3. Dynamic Registration" --> Agent
    Agent -- "4. JSON-RPC call_tool()" --> Server1
    Agent -- "5. JSON-RPC call_tool()" --> Server2
```

---

## JSON-RPC Message Format Walkthrough

MCP relies on lightweight **JSON-RPC 2.0** messages over stdio or HTTP/SSE transports.

### 1. Tool Discovery (`tools/list`)
**Request (Client -> Server):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**Response (Server -> Client):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "check_ticket_db_mcp",
        "description": "Look up ticket details by ticket ID.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "ticket_id": {"type": "string"}
          },
          "required": ["ticket_id"]
        }
      }
    ]
  }
}
```

### 2. Tool Execution (`tools/call`)
**Request (Client -> Server):**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "check_ticket_db_mcp",
    "arguments": {
      "ticket_id": "TICK-101"
    }
  }
}
```

**Response (Server -> Client):**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"status\": \"success\", \"ticket\": {\"ticket_id\": \"TICK-101\", \"amount\": 120.0}}"
      }
    ]
  }
}
```

---

## File Implementations

| File Path | Component | Description |
| :--- | :--- | :--- |
| [`app/mcp_server.py`](file:///d:/chat%20bot/app/mcp_server.py) | **Primary MCP Server (Track A)** | Exposes ticket DB, customer history, reimbursement math, and auth-protected escalation over FastMCP. |
| [`app/secondary_mcp_server.py`](file:///d:/chat%20bot/app/secondary_mcp_server.py) | **Secondary MCP Server** | Exposes policy document search and policy compliance scoring to prove 0 agent code changes required. |
| [`app/mcp_client.py`](file:///d:/chat%20bot/app/mcp_client.py) | **MCP Client Manager** | Manages JSON-RPC handshakes, tool discovery via `list_tools()`, and dynamic tool wrapping. |
| [`app/tools.py`](file:///d:/chat%20bot/app/tools.py) | **Tool Registry** | Updated with `load_mcp_server()` method to load tools dynamically from MCP servers. |
| [`app/agent.py`](file:///d:/chat%20bot/app/agent.py) | **ReAct Agent** | Supports running with dynamically discovered MCP tools without hard-coded function maps. |
| [`app/week9_eval.py`](file:///d:/chat%20bot/app/week9_eval.py) | **Evaluation Suite** | Automated benchmark verifying tool discovery, 0-code-change server addition, security controls, error recovery, and A2A interoperability. |

---

## Mentor Check Cheat-Sheet

| Mentor Check Question | Project Verification & Answer |
| :--- | :--- |
| **Does the agent use a tool through MCP, discovered rather than hard-coded?** | **YES.** `MCPClientManager.connect_and_discover()` calls `list_tools()` at startup and populates `ToolRegistry`. The agent code contains 0 hard-coded tool function signatures. |
| **Can they add a second tool without changing the agent's code?** | **YES.** In Test 2 of `app/week9_eval.py`, `PolicyAnalyticsService` is bolted on via `mcp_registry.load_mcp_server(secondary_mcp_server)`. Zero lines of `HandBuiltReActAgent` code were changed. |
| **Did they build their own server that another person's agent could call?** | **YES.** `app/mcp_server.py` implements `TicketHistoryService`. In Test 5, a simulated external partner agent connects over MCP and queries customer ticket history. |
| **Can they explain, in plain words, where the AI runs and where it doesn't?** | **YES.** The AI (LLM) runs strictly on the **Host/Client side** inside `HandBuiltReActAgent`. The MCP Server has **no AI** — it is an API executor. |
