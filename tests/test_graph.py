import json
from contextlib import asynccontextmanager
import pytest
from langchain_core.messages import AIMessage,HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
import app.agent as agent

@pytest.mark.asyncio
@pytest.mark.parametrize('approved',[True,False])
async def test_pause_resume_and_cancel(monkeypatch,approved):
    effects=[]
    class Cursor:
        async def fetchone(self): return {'id':'confirmation'}
    class Connection:
        async def execute(self,*args): return Cursor()
    @asynccontextmanager
    async def fake_connect(): yield Connection()
    async def fake_call(name,args,user,cid):
        if name=='consultar_stock':return {'ok':True,'stock':12,'name':'Teclado USB'}
        if name=='registrar_reserva':
            effects.append(args)
            return {'ok':True,'reservation_id':'R-TEST','product_id':'TEC-01','quantity':2}
        raise AssertionError(name)
    monkeypatch.setenv('MODEL_MODE','demo')
    monkeypatch.setattr(agent,'connect',fake_connect)
    monkeypatch.setattr(agent,'call',fake_call)
    saver=InMemorySaver();graph=agent.build_agent(saver)
    cfg={'configurable':{'thread_id':'test-thread'}}
    await graph.ainvoke({'messages':[HumanMessage(content='reserva 2 TEC-01')],
        'user_id':'u','conversation_id':'c','pending':None,'approved':False,'result':{}},cfg)
    state=await graph.aget_state(cfg)
    assert state.next==('approval',)
    assert effects==[]
    assert state.values['pending']['quantity']==2
    # Una nueva instancia del grafo recupera el mismo estado del saver.
    graph=agent.build_agent(saver)
    await graph.ainvoke(Command(resume=approved),cfg)
    state=await graph.aget_state(cfg)
    assert not state.next
    assert len(effects)==int(approved)
    assert ('Reserva registrada' if approved else 'No se registró') in state.values['messages'][-1].content
