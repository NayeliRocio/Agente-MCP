import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID, uuid4
import httpx
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from .config import setting
from .db import connect
from .auth import current_user
from .agent import build_agent

# Práctica: un proceso y una ejecución a la vez. Evita reanudar dos veces el mismo hilo.
run_lock=asyncio.Lock()
async def configure(conn):
    await conn.execute('SET search_path TO agentlab, public')

@asynccontextmanager
async def lifespan(app):
    async with AsyncConnectionPool(setting('DATABASE_URL'),min_size=1,max_size=4,
        kwargs={'autocommit':True,'prepare_threshold':None,'row_factory':dict_row},
        configure=configure,open=False) as pool:
        await pool.open()
        await pool.wait(timeout=20)
        saver=AsyncPostgresSaver(pool)
        await saver.setup()
        # Tablas de checkpoint quedan en esquema privado agentlab.
        async with pool.connection() as c:
            for table in ('checkpoints','checkpoint_blobs','checkpoint_writes','checkpoint_migrations'):
                await c.execute(f'ALTER TABLE agentlab.{table} ENABLE ROW LEVEL SECURITY')
        app.state.graph=build_agent(saver)
        yield

app=FastAPI(title='Laboratorio LangGraph + MCP + Supabase',lifespan=lifespan)
class Login(BaseModel):
    email:str
    password:str
class Chat(BaseModel):
    text:str=Field(min_length=1,max_length=2000)
class Confirmation(BaseModel):
    approved:bool
    confirmation_id:UUID

class ReservationProposal(BaseModel):
    product_id:str=Field(min_length=1,max_length=100)
    quantity:int=Field(ge=1,le=100,strict=True)

@app.get('/')
async def index():
    return FileResponse(Path(__file__).with_name('index.html'))

@app.get('/config')
async def config():
    return {'auth_mode':setting('AUTH_MODE','demo'),'model_mode':setting('MODEL_MODE','demo')}

@app.get('/health')
async def health():
    async with connect() as c:
        await c.execute('select 1')
    return {'ok':True}

@app.get('/products')
async def products(user:str=Depends(current_user)):
    async with connect() as c:
        cur=await c.execute('select id,name,stock from agentlab.products order by name')
        return {'products':await cur.fetchall()}

@app.get('/reservations')
async def reservations(user:str=Depends(current_user)):
    async with connect() as c:
        cur=await c.execute("""
            select c.id as confirmation_id, c.product_id, p.name, c.quantity,
                   case when r.id is not null then 'confirmed'
                        when c.status='cancelled' then 'cancelled'
                        when c.expires_at<=now() then 'expired'
                        else 'pending' end as status,
                   r.id as reservation_id, c.conversation_id,
                   coalesce(r.created_at,c.expires_at-interval '10 minutes') as created_at
            from agentlab.confirmations c
            join agentlab.products p on p.id=c.product_id
            left join agentlab.reservations r on r.confirmation_id=c.id
            where c.user_id=%s
            order by created_at desc, c.id desc limit 100
        """,(user,))
        return {'reservations':await cur.fetchall()}

@app.get('/conversations')
async def conversations(user:str=Depends(current_user)):
    async with connect() as c:
        cur=await c.execute("""
            select c.id,c.created_at,coalesce(m.content,'Nueva conversación') as title
            from agentlab.conversations c
            left join lateral (
                select content from agentlab.messages
                where conversation_id=c.id and role='user' order by id limit 1
            ) m on true
            where c.user_id=%s order by c.created_at desc limit 30
        """,(user,))
        return {'conversations':await cur.fetchall()}

@app.post('/login')
async def login(body:Login):
    if setting('AUTH_MODE','demo')!='supabase':
        raise HTTPException(400,'Usa el token de práctica en modo demo')
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.post(setting('SUPABASE_URL')+'/auth/v1/token?grant_type=password',
            headers={'apikey':setting('SUPABASE_PUBLISHABLE_KEY')},json=body.model_dump())
    if r.status_code!=200:
        raise HTTPException(401,'Revisa usuario, contraseña y confirmación del correo')
    data=r.json()
    return {'access_token':data['access_token'],'expires_in':data['expires_in']}

async def owner(cid:UUID,user:str):
    async with connect() as c:
        cur=await c.execute('select id from agentlab.conversations where id=%s and user_id=%s',(str(cid),user))
        if not await cur.fetchone():
            raise HTTPException(404,'Conversación no encontrada')

def cfg(cid):
    return {'configurable':{'thread_id':str(cid)},'recursion_limit':16}

async def render(cid):
    snap=await app.state.graph.aget_state(cfg(cid))
    val=snap.values
    pending=val.get('pending') if snap.next else None
    assistant=next((str(m.content) for m in reversed(val.get('messages',[])) if m.type=='ai' and m.content),'')
    return {'conversation_id':str(cid),'pending':pending,'reply':assistant}

async def log_message(cid,role,content):
    async with connect() as c:
        await c.execute('insert into agentlab.messages(conversation_id,role,content) values(%s,%s,%s)',(str(cid),role,content))

@app.post('/conversations')
async def create(user:str=Depends(current_user)):
    cid=str(uuid4())
    async with connect() as c:
        await c.execute('insert into agentlab.conversations(id,user_id) values(%s,%s)',(cid,user))
    return {'conversation_id':cid}

@app.get('/conversations/{cid}')
async def get(cid:UUID,user:str=Depends(current_user)):
    await owner(cid,user)
    response=await render(cid)
    async with connect() as c:
        cur=await c.execute('select role,content,created_at from agentlab.messages '
                            'where conversation_id=%s order by id',(str(cid),))
        response['messages']=await cur.fetchall()
    return response

@app.post('/conversations/{cid}/reserve')
async def propose(cid:UUID,body:ReservationProposal,user:str=Depends(current_user)):
    await owner(cid,user)
    async with run_lock:
        graph=app.state.graph
        snapshot=await graph.aget_state(cfg(cid))
        if snapshot.next:
            raise HTTPException(409,'Confirma o cancela la operación pendiente primero.')
        text=f'Reserva {body.quantity} unidades de {body.product_id}.'
        # Los botones entran al mismo grafo, validación MCP y aprobación humana.
        # Ninguna escritura de reserva se realiza en este endpoint.
        proposal=AIMessage(content='',tool_calls=[{
            'id':str(uuid4()),'name':'proponer_reserva',
            'args':{'producto_id':body.product_id,'cantidad':body.quantity}}])
        await log_message(cid,'user',text)
        try:
            await graph.aupdate_state(cfg(cid),{
                'messages':[HumanMessage(content=text),proposal],
                'user_id':user,'conversation_id':str(cid),
                'pending':None,'approved':False,'result':{}},as_node='planner')
            await graph.ainvoke(None,cfg(cid))
        except Exception:
            logging.exception('Fallo al proponer reserva')
            raise HTTPException(503,'No se pudo preparar la reserva. Consulta el estado antes de repetir.')
        response=await render(cid)
        await log_message(cid,'assistant','Revisa la propuesta para confirmar la reserva.'
                          if response['pending'] else response['reply'])
        return response

@app.post('/conversations/{cid}/messages')
async def chat(cid:UUID,body:Chat,user:str=Depends(current_user)):
    await owner(cid,user)
    async with run_lock:
        graph=app.state.graph
        snapshot=await graph.aget_state(cfg(cid))
        if snapshot.next:
            raise HTTPException(409,'Hay una operación pendiente. Confirma o cancela primero.')
        await log_message(cid,'user',body.text)
        try:
            await graph.ainvoke({'messages':[HumanMessage(content=body.text)],'user_id':user,
                'conversation_id':str(cid),'pending':None,'approved':False,'result':{}},cfg(cid))
        except Exception:
            logging.exception('Fallo del agente')
            raise HTTPException(503,'El flujo falló. Revisa la terminal y consulta el estado antes de repetir.')
        response=await render(cid)
        await log_message(cid,'assistant',response['reply'] or 'Esperando confirmación')
        return response

@app.post('/conversations/{cid}/confirm')
async def confirm(cid:UUID,body:Confirmation,user:str=Depends(current_user)):
    await owner(cid,user)
    async with run_lock:
        graph=app.state.graph
        snap=await graph.aget_state(cfg(cid))
        if not snap.next:
            return await render(cid)  # Reenvío HTTP: no ejecuta de nuevo una reserva terminada.
        if snap.values.get('pending',{}).get('confirmation_id') != str(body.confirmation_id):
            raise HTTPException(409,'La confirmación pertenece a otra operación')
        if not any(getattr(t,'interrupts',()) for t in snap.tasks):
            raise HTTPException(409,'El flujo falló fuera de una confirmación. Revisa la terminal.')
        await log_message(cid,'user','CONFIRMAR' if body.approved else 'CANCELAR')
        try:
            await graph.ainvoke(Command(resume=body.approved),cfg(cid))
        except Exception:
            logging.exception('Fallo al reanudar')
            raise HTTPException(503,'No se pudo reanudar. Consulta el estado y las reservas antes de repetir.')
        response=await render(cid)
        await log_message(cid,'assistant',response['reply'])
        return response
