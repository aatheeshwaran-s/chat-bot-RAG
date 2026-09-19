"""
Week 9: Secondary MCP Server Implementation (PolicyAnalyticsService).

Proves that a 2nd tool server can be dynamically "bolted on" over MCP
without modifying a single line of code in the ReAct Agent!
"""

import json
from fastmcp import FastMCP

secondary_mcp_server = FastMCP(
    name="PolicyAnalyticsService",
    instructions="MCP Server exposing Document Policy Search and Compliance Scoring."
)


@secondary_mcp_server.tool(
    name="lookup_policy_mcp",
    description="Search company policies, return terms, travel guidelines, and expense rules over MCP."
)
def lookup_policy_mcp(query: str) -> str:
    """
    Simulates / connects to hybrid vector + BM25 search over MCP.
    """
    from app.tools import get_hybrid_searcher
    try:
        searcher = get_hybrid_searcher()
        results = searcher.search(query, top_k=2)
        formatted_chunks = []
        for r in results:
            formatted_chunks.append({
                "source": r.chunk.source_filename,
                "text": r.chunk.text,
                "score": round(r.score, 4)
            })
        return json.dumps({
            "status": "success",
            "query": query,
            "results": formatted_chunks
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Recoverable MCP Search Error: {str(e)}"
        })


@secondary_mcp_server.tool(
    name="get_policy_compliance_score",
    description="Evaluate policy compliance score (0-100) for a given ticket ID and expense type."
)
def get_policy_compliance_score(ticket_id: str, expense_type: str = "general") -> str:
    """
    Evaluates policy compliance metrics over MCP.
    """
    # Deterministic mock compliance calculation
    score = 95
    reasons = ["Submission within deadline", "Valid category"]
    if "flight" in expense_type.lower() or "104" in ticket_id:
        score = 40
        reasons = ["Submission delayed > 30 days", "Requires manager pre-approval"]
    
    return json.dumps({
        "status": "success",
        "ticket_id": ticket_id,
        "compliance_score": score,
        "assessment": "COMPLIANT" if score >= 70 else "NON_COMPLIANT_NEEDS_ESCALATION",
        "reasons": reasons
    })


if __name__ == "__main__":
    print("[MCP Server 2] Starting PolicyAnalyticsService on stdio transport...")
    secondary_mcp_server.run()
