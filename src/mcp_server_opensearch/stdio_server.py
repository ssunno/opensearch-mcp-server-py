# Copyright OpenSearch Contributors
# SPDX-License-Identifier: Apache-2.0

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from tools.tools import TOOL_REGISTRY
from mcp_server_opensearch.common import is_tool_compatible
from opensearch.helper import get_opensearch_version
import os


# --- Server setup ---
async def serve() -> None:
    server = Server("opensearch-mcp-server")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        tools = []
        opensearch_url = os.getenv("OPENSEARCH_URL", "")
        version = get_opensearch_version(opensearch_url)
        for tool_name, tool_info in TOOL_REGISTRY.items():
            if is_tool_compatible(version, tool_info):
                tools.append(
                    Tool(
                        name=tool_name,
                        description=tool_info["description"],
                        inputSchema=tool_info["input_schema"],
                    )
                )
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        tool = TOOL_REGISTRY[name]
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        parsed = tool["args_model"](**arguments)
        return await tool["function"](parsed)

    # Start stdio-based MCP server
    options = server.create_initialization_options()
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, options, raise_exceptions=True)
