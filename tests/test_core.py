import json
from langchain_core.messages import HumanMessage,ToolMessage
from app.agent import demo_reply,SCHEMAS

def test_demo_reserve_first_checks_stock():
    r=demo_reply([HumanMessage(content='reserva 2 TEC-01')])
    assert r.tool_calls[0]['name']=='consultar_stock'

def test_insufficient_stock_never_proposes():
    result=demo_reply([HumanMessage(content='reserva 20 TEC-01'),
        ToolMessage(content=json.dumps({'ok':True,'stock':12}),name='consultar_stock',tool_call_id='x')])
    assert not result.tool_calls
    assert 'insuficiente' in result.content

def test_model_has_no_direct_write_tool():
    assert 'registrar_reserva' not in [t['name'] for t in SCHEMAS]
    assert 'proponer_reserva' in [t['name'] for t in SCHEMAS]
