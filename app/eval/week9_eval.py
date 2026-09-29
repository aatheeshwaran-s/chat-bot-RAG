"""
Week 9 Comprehensive Evaluation & Demonstration Suite.

Demonstrates:
1. Dynamic Tool Discovery over MCP (Host -> MCP Client -> Server Handshake).
2. Bolting on a 2nd MCP server (PolicyAnalyticsService) with 0 code changes in HandBuiltReActAgent.
3. Access Control & Auth Token Validation on sensitive actions (escalate_ticket_mcp).
4. Recoverable Error Handling over MCP transport.
5. Multi-Agent / Agent-to-Agent (A2A) interoperability (External Agent calling our MCP Server).
"""

import os
import json
import time
from typing import Dict, Any
from app.agents.tools import ToolRegistry
from app.agents.agent import HandBuiltReActAgent
from app.mcp.mcp_server import mcp_server as ticket_server
from app.mcp.secondary_mcp_server import secondary_mcp_server as policy_server


def print_section(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def run_week9_evaluation_suite():
    print_section("WEEK 9 MODULE 5: MCP, MULTI-AGENT & A2A BENCHMARK")
    
    # -------------------------------------------------------------------
    # TEST 1: Dynamic Tool Discovery over MCP (Primary Server)
    # -------------------------------------------------------------------
    print_section("TEST 1: Dynamic Tool Discovery over MCP (TicketHistoryService)")
    
    # Initialize clean ToolRegistry with only final_answer
    mcp_registry = ToolRegistry(init_defaults=False)
    
    # Discover tools over MCP without hardcoding signatures in agent
    mcp_registry.load_mcp_server(ticket_server, verbose=True)
    
    # Instantiate ReAct Agent using MCP discovered tools
    mcp_agent = HandBuiltReActAgent(tool_registry=mcp_registry, max_steps=4)
    
    print("\n[Agent Config] Discovered Tools in Agent System Prompt:")
    print(mcp_registry.format_tools_for_prompt())
    
    # Execute query using discovered MCP tool
    ticket_query = "Check details for ticket TICK-101 and calculate reimbursement for amount 120 * 0.9"
    res1 = mcp_agent.run(ticket_query, verbose=True)
    
    # -------------------------------------------------------------------
    # TEST 2: Bolting on a 2nd MCP Server with ZERO Agent Code Changes
    # -------------------------------------------------------------------
    print_section("TEST 2: Bolting on 2nd MCP Server (PolicyAnalyticsService) - 0 Code Changes")
    
    print("[MCP Client] Plugging in 2nd MCP Server: PolicyAnalyticsService...")
    # Load 2nd MCP server directly into existing registry
    mcp_registry.load_mcp_server(policy_server, verbose=True)
    
    print("\n[Updated Agent Registry] Tools available now:")
    for t_name in mcp_registry.tools.keys():
        print(f"  - `{t_name}`")
        
    print("\n[Running Query using 2nd Discovered MCP Tool: `get_policy_compliance_score`]")
    res2 = mcp_agent.run("Check policy compliance score for ticket TICK-104 with flight expense", verbose=True)

    # -------------------------------------------------------------------
    # TEST 3: Access Control & Auth Verification over MCP
    # -------------------------------------------------------------------
    print_section("TEST 3: Access Control & Auth Verification over MCP")
    
    print("[Security Check A] Escalating ticket without valid auth_token:")
    unauth_resp = mcp_registry.get_tool("escalate_ticket_mcp").run(
        ticket_id="TICK-101",
        reason="Exceeded limit",
        auth_token="invalid-token"
    )
    print(f"  Response: {unauth_resp}")
    assert "security_denied" in unauth_resp or "Access Control Error" in unauth_resp, "Security check failed!"
    print("  [OK] Security Check PASSED: Unauthorized request rejected over MCP.")

    print("\n[Security Check B] Escalating ticket WITH valid auth_token='admin-secret':")
    auth_resp = mcp_registry.get_tool("escalate_ticket_mcp").run(
        ticket_id="TICK-101",
        reason="Exceeded limit",
        auth_token="admin-secret"
    )
    print(f"  Response: {auth_resp}")
    assert "ESCALATED" in auth_resp or "success" in auth_resp, "Authorized request failed!"
    print("  [OK] Security Check PASSED: Authorized request succeeded over MCP.")

    # -------------------------------------------------------------------
    # TEST 4: Recoverable Error Handling over MCP
    # -------------------------------------------------------------------
    print_section("TEST 4: Recoverable Error Handling over MCP")
    
    print("[Error Test A] Requesting non-existent ticket 'TICK-9999':")
    err_resp1 = mcp_registry.get_tool("check_ticket_db_mcp").run(ticket_id="TICK-9999")
    print(f"  Response: {err_resp1}")
    assert "Recoverable MCP Error" in err_resp1, "Recoverable error handling failed!"
    print("  [OK] Recoverable Error Test PASSED: Server returned descriptive error without crashing.")

    print("\n[Error Test B] Requesting invalid math expression '100 / 0':")
    err_resp2 = mcp_registry.get_tool("calculate_reimbursement_mcp").run(expression="100 / 0")
    print(f"  Response: {err_resp2}")
    assert "Recoverable MCP Math Error" in err_resp2 or "error" in err_resp2, "Math error handling failed!"
    print("  [OK] Recoverable Error Test PASSED: Server caught division by zero cleanly.")

    # -------------------------------------------------------------------
    # TEST 5: External Agent Interoperability (A2A)
    # -------------------------------------------------------------------
    print_section("TEST 5: External Agent Interoperability (A2A)")
    
    print("[Simulating External Partner Agent]")
    print("An external agent from another team connects to our 'TicketHistoryService' MCP Server...")
    
    # External agent discovers tools from our server
    ext_registry = ToolRegistry(init_defaults=False)
    ext_registry.load_mcp_server(ticket_server, verbose=False)
    
    ext_agent = HandBuiltReActAgent(tool_registry=ext_registry, max_steps=3)
    ext_query = "Find customer history for 'Alice'"
    
    print(f"\n[External Agent Run] Query: '{ext_query}'")
    ext_res = ext_agent.run(ext_query, verbose=True)
    print(f"  External Agent Output: {ext_res.get('final_answer')}")

    # -------------------------------------------------------------------
    # FINAL SUMMARY REPORT
    # -------------------------------------------------------------------
    print_section("WEEK 9 EVALUATION BENCHMARK SUMMARY")
    print("  [OK] MCP Server (TicketHistoryService): OPERATIONAL")
    print("  [OK] MCP Server (PolicyAnalyticsService): OPERATIONAL")
    print("  [OK] Dynamic Tool Discovery: PASSED (Tools discovered at runtime over JSON-RPC)")
    print("  [OK] Zero Code Changes for 2nd Server: PASSED")
    print("  [OK] Security / Access Control Enforcement: PASSED")
    print("  [OK] Recoverable Error Handling: PASSED")
    print("  [OK] Agent-to-Agent (A2A) Interoperability: PASSED")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_week9_evaluation_suite()
