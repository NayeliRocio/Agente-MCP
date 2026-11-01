from uuid import uuid4
from .db import connect

async def search_product(text: str):
    async with connect() as c:
        cur = await c.execute(
            'select id,name,stock from agentlab.products '
            'where name ilike %s or id ilike %s order by id limit 10',
            ('%' + text + '%', '%' + text + '%'))
        return {'ok': True, 'products': await cur.fetchall()}

async def stock(product_id: str):
    async with connect() as c:
        cur = await c.execute('select id,name,stock from agentlab.products where id=%s', (product_id,))
        p = await cur.fetchone()
        return {'ok': True, **p} if p else {'ok': False, 'error': 'PRODUCTO_NO_ENCONTRADO'}

async def reserve(confirmation_id: str, user_id: str):
    """Transacción: la confirmación fija producto, cantidad e identidad."""
    async with connect() as c:
        async with c.transaction():
            cur = await c.execute(
                'select *, expires_at > now() as valid from agentlab.confirmations '
                'where id=%s and user_id=%s for update', (confirmation_id, user_id))
            a = await cur.fetchone()
            if not a:
                return {'ok': False, 'error': 'CONFIRMACION_NO_ENCONTRADA'}
            # Reintentar la misma operación devuelve la reserva ya creada.
            cur = await c.execute('select id,product_id,quantity from agentlab.reservations '
                                  'where confirmation_id=%s', (confirmation_id,))
            old = await cur.fetchone()
            if old:
                return {'ok': True, 'reservation_id': str(old['id']),
                        'product_id': old['product_id'], 'quantity': old['quantity'], 'replayed': True}
            if a['status'] != 'approved' or not a['valid']:
                return {'ok': False, 'error': 'CONFIRMACION_NO_AUTORIZADA_O_VENCIDA'}
            cur = await c.execute('update agentlab.products set stock=stock-%s '
                                  'where id=%s and stock >= %s returning stock',
                                  (a['quantity'], a['product_id'], a['quantity']))
            updated = await cur.fetchone()
            if not updated:
                return {'ok': False, 'error': 'STOCK_INSUFICIENTE'}
            rid = str(uuid4())
            await c.execute('insert into agentlab.reservations '
                            '(id,user_id,product_id,quantity,confirmation_id) values(%s,%s,%s,%s,%s)',
                            (rid,user_id,a['product_id'],a['quantity'],confirmation_id))
            await c.execute("update agentlab.confirmations set status='used' where id=%s", (confirmation_id,))
            return {'ok': True, 'reservation_id': rid, 'product_id': a['product_id'],
                    'quantity': a['quantity'], 'remaining_stock': updated['stock']}

async def get_reservation(reservation_id: str, user_id: str):
    async with connect() as c:
        cur = await c.execute('select id,product_id,quantity,created_at from agentlab.reservations '
                              'where id=%s and user_id=%s', (reservation_id,user_id))
        row = await cur.fetchone()
        if not row:
            return {'ok': False, 'error': 'RESERVA_NO_ENCONTRADA'}
        return {'ok': True, **{k:str(v) if k in ('id','created_at') else v for k,v in row.items()}}
