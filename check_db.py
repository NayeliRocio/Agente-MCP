import asyncio
from app.db import connect
async def main():
    async with connect() as c:
        row=await (await c.execute('select current_database() as db')).fetchone()
        print('Conexión PostgreSQL correcta:',row['db'])
        rows=await (await c.execute('select id,name,stock from agentlab.products order by id')).fetchall()
        for p in rows:
            print(p)
asyncio.run(main())
