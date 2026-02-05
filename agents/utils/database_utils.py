import asyncio
import os
import logging
from dotenv import load_dotenv

load_dotenv()

import psycopg_pool
from psycopg.rows import dict_row

POOL = None

POSTGRES_DB_USER = os.getenv('POSTGRES_DB_USER')
POSTGRES_DB_PASS = os.getenv('POSTGRES_DB_PASS')
POSTGRES_DB_NAME = os.getenv('POSTGRES_DB_NAME')
POSTGRES_DB_HOST = os.getenv('POSTGRES_DB_HOST')
POSTGRES_DB_PORT = os.getenv('POSTGRES_DB_PORT')


if POOL is None:
    conninfo = " ".join(
        f"{key}={val}"
        for key, val in {
            "user": POSTGRES_DB_USER,
            "password": POSTGRES_DB_PASS,
            "dbname": POSTGRES_DB_NAME,
            "host": POSTGRES_DB_HOST,
            "port": POSTGRES_DB_PORT
        }.items()
        if val is not None
    )

    POOL = psycopg_pool.AsyncConnectionPool(
        conninfo,
        min_size = 5,
        max_size = 20,
    )
    logging.debug(f"Database `{POSTGRES_DB_NAME}` connection pool created.")


def get_db_pool():
    """Synchronous accessor to get the initialized pool."""
    if POOL is None:
        raise RuntimeError("Database pool has not been initialized. Call init_db() first.")

    return POOL

    