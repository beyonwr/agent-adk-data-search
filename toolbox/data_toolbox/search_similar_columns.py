import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from dateutil.tz import tzlocal

from ..utils.path_resolver import save_resource
from .utils.db_clients import get_chromadb_client, get_embedding, CHROMADB_COLLECTION_NAME


async def search_similar_columns(
    query_text: str,
    n_results: int = 10,
) -> Dict[str, Any]:
    """
    Search for similar column names using vector similarity.

    Args:
        query_text: Natural language query to search for similar columns
        n_results: Number of similar columns to return (default: 10)

    Returns:
        Dict with status and outputs (resource_link type with JSON file)
    """
    logging.debug(f"Searching for similar columns: {query_text}")

    # Get ChromaDB client
    try:
        chroma_client = get_chromadb_client()
        collection = chroma_client.get_collection(CHROMADB_COLLECTION_NAME)
    except Exception as e:
        logging.error(f"Error connecting to ChromaDB: {e}")
        return {
            "status": "error",
            "message": f"Error connecting to ChromaDB: {e}",
        }

    # Get embedding for query text
    try:
        embeddings = get_embedding([query_text])
    except Exception as e:
        logging.error(f"Error getting embeddings: {e}")
        return {
            "status": "error",
            "message": f"Error getting embeddings: {e}",
        }

    # Query collection
    try:
        query_res = collection.query(query_embeddings=embeddings, n_results=n_results)
        logging.debug(f"ChromaDB query result: {query_res}")
    except Exception as e:
        logging.error(f"Error querying ChromaDB: {e}")
        return {
            "status": "error",
            "message": f"Error querying ChromaDB: {e}",
        }

    # Format results
    documents = query_res.get("documents", [[]])[0]  # First query's documents
    distances = query_res.get("distances", [[]])[0]  # First query's distances
    metadatas = query_res.get("metadatas", [[]])[0]  # First query's metadatas
    ids = query_res.get("ids", [[]])[0]  # First query's ids

    results = []
    for i, doc in enumerate(documents):
        result_item = {
            "document": doc,
            "distance": distances[i] if i < len(distances) else None,
            "id": ids[i] if i < len(ids) else None,
        }
        if i < len(metadatas) and metadatas[i]:
            result_item["metadata"] = metadatas[i]
        results.append(result_item)

    # Prepare JSON data
    json_data = {
        "query": query_text,
        "n_results": n_results,
        "results": results,
        "timestamp": datetime.now(tzlocal()).isoformat(),
    }

    # Save as JSON resource
    job_id = uuid.uuid4().hex
    json_uri, json_filename, json_mime_type = save_resource(json_data, job_id, "json")

    # Generate description
    top_docs = [r["document"] for r in results[:3]]
    description = (
        f"유사 컬럼 검색 결과 | 쿼리: '{query_text}' | {len(results)}개 결과 | "
        f"상위 결과: {', '.join(top_docs)}"
    )

    # Return resource link
    return {
        "status": "success",
        "outputs": [
            {
                "type": "resource_link",
                "uri": json_uri,
                "filename": json_filename,
                "mime_type": json_mime_type,
                "description": description,
                "metadata": {
                    "query": query_text,
                    "results_count": len(results),
                }
            }
        ]
    }
