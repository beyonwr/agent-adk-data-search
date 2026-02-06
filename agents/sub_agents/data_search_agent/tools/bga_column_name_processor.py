import logging
import os

import chromadb
import chromadb.config
import requests

CHROMADB_HOST = os.getenv("CHROMADB_HOST")
CHROMADB_PORT = os.getenv("CHROMADB_PORT", "8000")
CHROMADB_COLLECTION_NAME = os.getenv("CHROMADB_COLLECTION_NAME")
TEXT_EMBEDDING_MODEL_URL = os.getenv("TEXT_EMBEDDING_MODEL_URL")
TEXT_EMBEDDING_MODEL_NAME = os.getenv("TEXT_EMBEDDING_MODEL_NAME")


def _get_embedding(text_list: list[str]) -> list[list[float]]:
    """get embedding from the BGE-M3-KO model"""
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

def get_sim_search(query_list: list[str], n_results: int=3):
    chroma_client = chromadb.HttpClient(
        host=CHROMADB_HOST,
        port=int(CHROMADB_PORT),
        settings=chromadb.config.Settings(allow_reset=True, annoymized_telemetry=False)
    )

    collection = chroma_client.get_collection(CHROMADB_COLLECTION_NAME)

    embeddings = _get_embedding(query_list)

    query_res = collection.query(query_embeddings=embeddings, n_results=n_results)
    logging.debug(f"{query_res}")
    return query_res["documents"]