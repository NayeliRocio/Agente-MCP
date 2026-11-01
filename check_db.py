import asyncio
import selectors
import sys

from app.db import connect


async def main():
    async with connect() as c:
        cursor = await c.execute(
            "select current_database() as db"
        )
        row = await cursor.fetchone()
        print("Conexión PostgreSQL correcta:", row["db"])

        cursor = await c.execute(
            "select id, name, stock "
            "from agentlab.products order by id"
        )
        rows = await cursor.fetchall()

        for producto in rows:
            print(producto)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(
            main(),
            loop_factory=lambda: asyncio.SelectorEventLoop(
                selectors.SelectSelector()
            ),
        )
    else:
        asyncio.run(main())