import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def call_mcp_tool(tool_name: str, args: dict):
    async with sse_client("http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args)
            return result.content[0].text
