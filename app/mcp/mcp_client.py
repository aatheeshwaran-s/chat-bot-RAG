"""
Week 9: MCP Client & Dynamic Tool Discovery Manager.

Connects agents to MCP servers over standard transports (FastMCP / stdio / JSON-RPC).
Dynamically discovers available tools via `list_tools()` without hard-coding signatures,
wrapping them into standard `Tool` objects for `ToolRegistry`.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from app.agents.tools import Tool, ToolRegistry


class MCPClientManager:
    """
    Client Manager that connects to MCP Servers and dynamically discovers tools.
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.connected_servers: List[FastMCP] = []

    def connect_and_discover(
        self,
        server: FastMCP,
        registry: ToolRegistry,
        prefix_name: bool = False
    ) -> List[str]:
        """
        Connects to an MCP Server, executes the tools discovery handshake,
        and automatically registers all discovered tools into ToolRegistry.
        
        Returns list of newly registered tool names.
        """
        if self.verbose:
            print(f"\n[MCP Client] Initiating MCP Handshake with Server: '{server.name}'...")
        
        # Run tool discovery over MCP protocol
        try:
            mcp_tools = asyncio.run(server.list_tools())
        except Exception:
            mcp_tools = server.get_tools()

        discovered_names = []
        for mcp_tool in mcp_tools:
            tool_name = mcp_tool.name
            description = mcp_tool.description or f"MCP tool from {server.name}"

            # Define dynamic runner closure that forwards calls over MCP
            def create_mcp_runner(srv: FastMCP, t_name: str):
                def mcp_runner(**kwargs) -> str:
                    if self.verbose:
                        print(f"  -> [MCP Client -> {srv.name}] Calling tool '{t_name}' with args: {kwargs}")
                    try:
                        # Invoke tool over MCP transport
                        result = asyncio.run(srv.call_tool(t_name, kwargs))
                        
                        # Extract text cleanly from FastMCP CallToolResult / Content blocks
                        if hasattr(result, 'content') and isinstance(result.content, list):
                            texts = []
                            for block in result.content:
                                if hasattr(block, 'text'):
                                    texts.append(block.text)
                                else:
                                    texts.append(str(block))
                            if texts:
                                return "\n".join(texts)
                        
                        if isinstance(result, list):
                            content_blocks = []
                            for block in result:
                                if hasattr(block, 'text'):
                                    content_blocks.append(block.text)
                                else:
                                    content_blocks.append(str(block))
                            return "\n".join(content_blocks)
                        elif hasattr(result, 'text'):
                            return result.text
                        elif isinstance(result, dict) or isinstance(result, list):
                            return json.dumps(result)
                        return str(result)
                    except Exception as e:
                        return f"MCP Recoverable Transport Error: {str(e)}"
                return mcp_runner

            mcp_func = create_mcp_runner(server, tool_name)
            
            # Create wrapped Tool object for ReAct Agent
            wrapped_tool = Tool(
                name=tool_name,
                description=f"[MCP Discovered from {server.name}] {description}",
                func=mcp_func
            )
            
            registry.register(wrapped_tool)
            discovered_names.append(tool_name)
            
            if self.verbose:
                print(f"  [OK] [MCP Discovered] Registered Tool: `{tool_name}` (Description: {description[:60]}...)")

        self.connected_servers.append(server)
        if self.verbose:
            print(f"[MCP Client] Completed discovery for '{server.name}'. Total tools registered: {len(discovered_names)}\n")
        
        return discovered_names
