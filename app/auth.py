import hmac
from uuid import UUID
import httpx
from fastapi import Header, HTTPException
from .config import setting

async def current_user(authorization: str = Header(default='')) -> str:
    if not authorization.startswith('Bearer '):
        raise HTTPException(401,'Falta iniciar sesión')
    token=authorization[7:]
    if setting('AUTH_MODE','demo')=='demo':
        expected=setting('DEMO_TOKEN')
        if len(expected)<24 or expected=='CAMBIAR_POR_UN_TOKEN_LARGO_ALEATORIO':
            raise HTTPException(503,'Configura DEMO_TOKEN con al menos 24 caracteres aleatorios')
        if not hmac.compare_digest(token,expected):
            raise HTTPException(401,'Token de práctica incorrecto')
        return str(UUID(setting('DEMO_USER_ID')))
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            response=await client.get(setting('SUPABASE_URL')+'/auth/v1/user',headers={
                'apikey':setting('SUPABASE_PUBLISHABLE_KEY'),'Authorization':'Bearer '+token})
        except httpx.RequestError:
            raise HTTPException(503,'No se puede verificar la sesión')
    if response.status_code!=200:
        raise HTTPException(401,'Sesión inválida o vencida')
    return str(UUID(response.json()['id']))
