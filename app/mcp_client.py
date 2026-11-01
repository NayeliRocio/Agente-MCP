import json
import os
import sys
from pathlib import Path
from time import perf_counter
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from psycopg.types.json import Jsonb
from .db import connect
ROOT = Path(__file__).resolve().parents[1]

async def raw_call(name: str, args: dict, user_id: str):
    params = StdioServerParameters(command=sys.executable,
        args=['-m','app.mcp_server'], cwd=str(ROOT),
        env={**os.environ, 'MCP_ACTOR_ID':user_id})
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, args)
            if result.isError:
                return {'ok':False, 'error':'MCP_TOOL_ERROR'}
            for item in result.content:
                if item.type == 'text':
                    try:
                        return json.loads(item.text)
                    except json.JSONDecodeError:
                        continue
            return {'ok':False, 'error':'RESPUESTA_MCP_INVALIDA'}

async def call(name: str, args: dict, user_id: str, conversation_id: str):
    start=perf_counter()
    try:
        result = await raw_call(name,args,user_id)
    except Exception:
        result = {'ok':False, 'error':'SERVICIO_MCP_NO_DISPONIBLE'}
    async with connect() as c:
        await c.execute('insert into agentlab.tool_executions '
            '(conversation_id,tool_name,status,duration_ms,result) values(%s,%s,%s,%s,%s)',
            (conversation_id,name,'ok' if result.get('ok') else 'error',
             int((perf_counter()-start)*1000),Jsonb(result)))
    return result
