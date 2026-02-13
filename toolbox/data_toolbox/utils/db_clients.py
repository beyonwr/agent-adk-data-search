import logging
import os

import chromadb
import chromadb.config
import psycopg_pool
import requests

# PostgreSQL Environment variables
POSTGRES_DB_USER = os.getenv('POSTGRESQL_DB_USER')
POSTGRES_DB_PASS = os.getenv('POSTGRESQL_DB_PASS')
POSTGRES_DB_NAME = os.getenv('POSTGRESQL_DB_NAME')
POSTGRES_DB_HOST = os.getenv('POSTGRESQL_DB_HOST')
POSTGRES_DB_PORT = os.getenv('POSTGRESQL_DB_PORT')

# ChromaDB Environment variables
CHROMADB_HOST = os.getenv("CHROMADB_HOST")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))
CHROMADB_COLLECTION_NAME = os.getenv("CHROMADB_COLLECTION_NAME")

# Embedding Environment variables
TEXT_EMBEDDING_MODEL_URL = os.getenv("TEXT_EMBEDDING_MODEL_URL")
TEXT_EMBEDDING_MODEL_NAME = os.getenv("TEXT_EMBEDDING_MODEL_NAME")

# PostgreSQL connection pool (lazy initialization)
_POOL = None


def get_pool():
    """
    Get or create PostgreSQL connection pool.

    Uses lazy initialization to avoid creating pool during module import
    (which would fail if there's no async event loop).

    Returns:
        AsyncConnectionPool: PostgreSQL connection pool
    """
    global _POOL

    if _POOL is None:
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

        _POOL = psycopg_pool.AsyncConnectionPool(
            conninfo,
            min_size=5,
            max_size=20,
        )
        logging.debug(f"data_toolbox: Database `{POSTGRES_DB_NAME}` connection pool created.")

    return _POOL


def get_chromadb_client():
    """Create ChromaDB HttpClient using environment variables."""
    return chromadb.HttpClient(
        host=CHROMADB_HOST,
        port=CHROMADB_PORT,
        settings=chromadb.config.Settings(allow_reset=True, anonymized_telemetry=False)
    )


def get_embedding(text_list: list[str]) -> list[list[float]]:
    """Get embeddings from BGE-M3-KO model."""
    response = requests.post(
        TEXT_EMBEDDING_MODEL_URL,
        json={
            "input": text_list,
            "model": TEXT_EMBEDDING_MODEL_NAME,
        },
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    res_data = response.json()["data"]
    logging.debug(f"vectorDB res {len(res_data)=} {len(res_data[0]['embedding'])}")
    embeddings = list(map(lambda data: data["embedding"], res_data))
    return embeddings
