from contextlib import asynccontextmanager
import psycopg
from psycopg.rows import dict_row
from .config import setting

@asynccontextmanager
async def connect():
    async with await psycopg.AsyncConnection.connect(
        setting('DATABASE_URL'), autocommit=True,
        prepare_threshold=None, row_factory=dict_row, connect_timeout=12
    ) as conn:
        yield conn
