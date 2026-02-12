import logging
import os

import chromadb
import chromadb.config
import requests
from agents.utils.database_utils import POOL  # Reuse existing pool

# Environment variables
CHROMADB_HOST = os.getenv("CHROMADB_HOST")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))
CHROMADB_COLLECTION_NAME = os.getenv("CHROMADB_COLLECTION_NAME")
TEXT_EMBEDDING_MODEL_URL = os.getenv("TEXT_EMBEDDING_MODEL_URL")
TEXT_EMBEDDING_MODEL_NAME = os.getenv("TEXT_EMBEDDING_MODEL_NAME")


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
