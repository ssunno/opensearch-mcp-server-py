# Copyright OpenSearch Contributors
# SPDX-License-Identifier: Apache-2.0

import argparse

from mcp_server_opensearch.common import is_tool_compatible
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.responses import Response
from mcp.server.sse import SseServerTransport
from mcp.server import Server
from mcp.types import TextContent, Tool
from tools.tools import TOOL_REGISTRY
from opensearch.helper import get_opensearch_version

import os


def create_mcp_server() -> Server:
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

    return server


class MCPStarletteApp:
    def __init__(self, mcp_server: Server):
        self.mcp_server = mcp_server
        self.sse = SseServerTransport("/messages/")

    async def handle_sse(self, request: Request) -> None:
        async with self.sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await self.mcp_server.run(
                read_stream,
                write_stream,
                self.mcp_server.create_initialization_options(),
            )

        # Done to prevent 'NoneType' errors. For more details: https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/server/sse.py#L33-L37
        return Response()

    async def handle_health(self, request: Request) -> Response:
        return Response("OK", status_code=200)

    def create_app(self) -> Starlette:
        return Starlette(
            routes=[
                Route("/sse", endpoint=self.handle_sse, methods=["GET"]),
                Route("/health", endpoint=self.handle_health, methods=["GET"]),
                Mount("/messages/", app=self.sse.handle_post_message),
            ]
        )


async def serve(host: str = "0.0.0.0", port: int = 9900) -> None:
    mcp_server = create_mcp_server()
    app_handler = MCPStarletteApp(mcp_server)
    app = app_handler.create_app()

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run OpenSearch MCP SSE-based server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9900, help="Port to listen on")
    args = parser.parse_args()

    import asyncio

    asyncio.run(serve(host=args.host, port=args.port))
