"""Usar SOLO una base de pruebas: crea y limpia los datos con UUID propios."""
import os
from pathlib import Path
from uuid import uuid4
import asyncio
import pytest
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from app.agent import build_agent
from app.db import connect
from app.service import reserve
from app.mcp_client import raw_call
pytestmark=pytest.mark.skipif(os.getenv('RUN_DB_TESTS')!='1',reason='Requiere BD de pruebas y RUN_DB_TESTS=1')

@pytest.mark.asyncio
async def test_confirmation_persistence_ownership_idempotence_and_stock():
    owner,other,conv,cancel_conv=[str(uuid4()) for _ in range(4)]
    product='TEST-'+uuid4().hex[:8].upper()
    async with connect() as c:
        await c.execute('insert into agentlab.products values(%s,%s,%s)',(product,'Teclado de prueba',2))
        for cid in (conv,cancel_conv):
            await c.execute('insert into agentlab.conversations(id,user_id) values(%s,%s)',(cid,owner))
    async def configure(c): await c.execute('SET search_path TO agentlab, public')
    async with AsyncConnectionPool(os.environ['DATABASE_URL'],min_size=1,max_size=3,
        kwargs={'autocommit':True,'prepare_threshold':None,'row_factory':dict_row},configure=configure,open=False) as pool:
        await pool.open();await pool.wait()
        saver=AsyncPostgresSaver(pool);await saver.setup()
        graph=build_agent(saver)
        cfg={'configurable':{'thread_id':conv}}
        state={'messages':[HumanMessage(content=f'reserva 2 {product}')],
               'user_id':owner,'conversation_id':conv,'pending':None,'approved':False,'result':{}}
        try:
            # Código demo acepta identificadores de producción TEC-01. Para prueba
            # se construye el plan inicial mediante el nodo de herramientas explícito.
            from langchain_core.messages import AIMessage
            tc=AIMessage(content='',tool_calls=[{'id':'test-proposal','name':'proponer_reserva',
                'args':{'producto_id':product,'cantidad':2}}])
            await graph.aupdate_state(cfg,{**state,'messages':[tc]},as_node='planner')
            await graph.ainvoke(None,cfg)
            snap=await graph.aget_state(cfg)
            assert snap.next==('approval',)
            confirmation=snap.values['pending']['confirmation_id']
            assert (await reserve(confirmation,owner))['ok'] is False
            assert (await reserve(confirmation,other))['ok'] is False
            # Otra instancia de grafo recupera el checkpoint de PostgreSQL.
            graph2=build_agent(saver)
            await graph2.ainvoke(Command(resume=True),cfg)
            snap=await graph2.aget_state(cfg)
            assert snap.values['result']['ok']
            repeated=await reserve(confirmation,owner)
            assert repeated['ok'] and repeated['replayed']
            assert (await raw_call('consultar_stock',{'producto_id':product},owner))['stock']==0
            assert not (await raw_call('consultar_reserva',{'reserva_id':repeated['reservation_id']},other))['ok']
            # Cancelar no crea reserva.
            cfg2={'configurable':{'thread_id':cancel_conv}}
            async with connect() as c:
                await c.execute('update agentlab.products set stock=1 where id=%s',(product,))
            tc2=AIMessage(content='',tool_calls=[{'id':'cancel','name':'proponer_reserva',
                'args':{'producto_id':product,'cantidad':1}}])
            await graph.aupdate_state(cfg2,{**state,'conversation_id':cancel_conv,'messages':[tc2]},as_node='planner')
            await graph.ainvoke(None,cfg2)
            await graph.ainvoke(Command(resume=False),cfg2)
            assert (await raw_call('consultar_stock',{'producto_id':product},owner))['stock']==1
            # Dos confirmaciones aprobadas compiten por una sola unidad.
            a,b=str(uuid4()),str(uuid4())
            async with connect() as c:
                for ident in (a,b):
                    await c.execute("insert into agentlab.confirmations(id,conversation_id,user_id,product_id,quantity,status) values(%s,%s,%s,%s,1,'approved')",(ident,conv,owner,product))
            results=await asyncio.gather(reserve(a,owner),reserve(b,owner))
            assert sum(r['ok'] for r in results)==1
        finally:
            async with connect() as c:
                await c.execute('delete from agentlab.reservations where product_id=%s',(product,))
                await c.execute('delete from agentlab.confirmations where product_id=%s',(product,))
                for cid in (conv,cancel_conv):
                    await c.execute('delete from agentlab.tool_executions where conversation_id=%s',(cid,))
                    for table in ('checkpoint_writes','checkpoint_blobs','checkpoints'):
                        await c.execute(f'delete from agentlab.{table} where thread_id=%s',(cid,))
                    await c.execute('delete from agentlab.conversations where id=%s',(cid,))
                await c.execute('delete from agentlab.products where id=%s',(product,))
