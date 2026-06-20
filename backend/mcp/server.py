"""Expose the read-only agent tool registry through MCP."""

import json
from typing import Any

import mcp.types as types
from mcp.server import Server

from backend.agent.tools.market_tools import build_default_registry
from backend.agent.tools.registry import ToolRegistry

SERVER_NAME = "openterminalui"


def list_tools_for(registry: ToolRegistry) -> list[types.Tool]:
    """Map the registry's ToolDefs to MCP Tool descriptors."""
    return [
        types.Tool(name=definition.name, description=definition.description, inputSchema=definition.parameters)
        for definition in registry.tool_defs()
    ]


async def call_tool_for(
    registry: ToolRegistry, name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """Execute a tool and return a JSON response without raising to the client."""
    try:
        result = await registry.execute(name, arguments or {})
    except KeyError:
        result = {"error": f"unknown tool: {name}"}
    except Exception as exc:  # tool failures are returned to the MCP client
        result = {"error": str(exc)}
    return [types.TextContent(type="text", text=json.dumps(result, default=str))]


def build_mcp_server(registry: ToolRegistry | None = None) -> Server:
    """Build an MCP server backed by the existing agent tool registry."""
    reg = registry or build_default_registry()
    server = Server(SERVER_NAME)

    @server.list_tools()
    async def _list() -> list[types.Tool]:
        return list_tools_for(reg)

    @server.call_tool()
    async def _call(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
        return await call_tool_for(reg, name, arguments)

    return server


async def run_stdio() -> None:
    """Run the default registry adapter over MCP stdio."""
    from mcp.server.stdio import stdio_server

    server = build_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
