import os
import sys
from pathlib import Path
import pytest
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_real_stdio_discovery_without_database():
    root=Path(__file__).resolve().parents[1]
    params=StdioServerParameters(command=sys.executable,args=['-m','app.mcp_server'],
        cwd=str(root),env={**os.environ,'MCP_ACTOR_ID':'11111111-1111-4111-8111-111111111111'})
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            response=await session.list_tools()
            names={t.name for t in response.tools}
            assert names=={'buscar_producto','consultar_stock','registrar_reserva','consultar_reserva'}
            write_tool=next(t for t in response.tools if t.name=='registrar_reserva')
            assert set(write_tool.inputSchema['properties'])=={'confirmacion_id'}
