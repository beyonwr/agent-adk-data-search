import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import google.genai.types as types
from dateutil.tz import tzlocal
from google.adk.tools import ToolContext

from .utils.db_clients import get_chromadb_client, get_embedding, CHROMADB_COLLECTION_NAME

STATE_SIMILAR_COLUMNS = "workspace:similar_columns"


async def search_similar_columns(
    tool_context: ToolContext,
    query_text: str,
    n_results: int = 10,
    artifact_filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search for similar column names using vector similarity.

    Args:
        tool_context: ADK ToolContext (auto-injected by calling agent)
        query_text: Natural language query to search for similar columns
        n_results: Number of similar columns to return (default: 10)
        artifact_filename: Optional custom filename (default: similar_columns_YYYYMMDD_HHMMSS.json)

    Returns:
        Dict with status, filename, version, results (list of similar columns)
    """
    # Generate default filename with timestamp
    if artifact_filename is None:
        now = datetime.now(tzlocal())
        artifact_filename = f'similar_columns_{now.strftime("%Y%m%d_%H%M%S")}.json'

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

    # Convert to JSON bytes
    json_text = json.dumps(
        {
            "query": query_text,
            "n_results": n_results,
            "results": results,
        },
        ensure_ascii=False,
        indent=2
    )
    json_bytes = json_text.encode("utf-8")

    # Create artifact
    json_artifact = types.Part.from_bytes(data=json_bytes, mime_type="application/json")

    # Save artifact
    try:
        version = await tool_context.save_artifact(
            filename=artifact_filename,
            artifact=json_artifact
        )
    except Exception as e:
        logging.error(f"Error saving artifact: {e}")
        return {
            "status": "error",
            "message": f"Error saving artifact: {e}",
        }

    # Generate metadata profile
    profile = {
        "filename": artifact_filename,
        "version": int(version) if version is not None else None,
        "mime_type": "application/json",
        "bytes": len(json_bytes),
        "timestamp": datetime.now(tzlocal()).isoformat(),
        "query": query_text,
        "n_results": len(results),
    }

    # Store in state
    state_index = tool_context.state.get(STATE_SIMILAR_COLUMNS, {})
    if not isinstance(state_index, dict):
        state_index = {}

    state_index[artifact_filename] = profile
    tool_context.state[STATE_SIMILAR_COLUMNS] = state_index

    # Return summary
    return {
        "status": "success",
        "message": f"Found {len(results)} similar columns.",
        "filename": artifact_filename,
        "version": version,
        "query": query_text,
        "results_count": len(results),
        "top_results": results[:3],  # Return top 3 for preview
    }
