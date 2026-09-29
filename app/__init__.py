import sys
from app import rag, agents, mcp, eval

# Expose sub-modules at top-level app.* namespace for full backward compatibility
sys.modules["app.embeddings"] = rag.embeddings
sys.modules["app.retrieval"] = rag.retrieval
sys.modules["app.reranker"] = rag.reranker
sys.modules["app.hybrid"] = rag.hybrid
sys.modules["app.ingest"] = rag.ingest
sys.modules["app.generation"] = rag.generation

sys.modules["app.agent"] = agents.agent
sys.modules["app.multi_agent"] = agents.multi_agent
sys.modules["app.workflow"] = agents.workflow
sys.modules["app.memory"] = agents.memory
sys.modules["app.tools"] = agents.tools

sys.modules["app.mcp_client"] = mcp.mcp_client
sys.modules["app.mcp_server"] = mcp.mcp_server
sys.modules["app.secondary_mcp_server"] = mcp.secondary_mcp_server

sys.modules["app.evaluate"] = eval.evaluate
sys.modules["app.w6_eval"] = eval.w6_eval
sys.modules["app.week8_eval"] = eval.week8_eval
sys.modules["app.week9_eval"] = eval.week9_eval
sys.modules["app.week10_eval"] = eval.week10_eval
sys.modules["app.error_analysis"] = eval.error_analysis
sys.modules["app.failure_analysis"] = eval.failure_analysis
sys.modules["app.inspection"] = eval.inspection
sys.modules["app.injection_defense"] = eval.injection_defense
sys.modules["app.race"] = eval.race
sys.modules["app.trace_collector"] = eval.trace_collector
sys.modules["app.trajectory_eval"] = eval.trajectory_eval
sys.modules["app.experiments"] = eval.experiments

__all__ = ["rag", "agents", "mcp", "eval"]
