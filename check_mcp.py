import asyncio
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.config import setting
async def main():
    params=StdioServerParameters(command=sys.executable,args=['-m','app.mcp_server'],
        cwd=str(Path(__file__).resolve().parent),env={**os.environ,'MCP_ACTOR_ID':setting('DEMO_USER_ID')})
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            tools=await session.list_tools()
            print('Herramientas descubiertas:',[t.name for t in tools.tools])
            result=await session.call_tool('consultar_stock',{'producto_id':'TEC-01'})
            for content in result.content:
                if content.type=='text': print(content.text)
asyncio.run(main())
