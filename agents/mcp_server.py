"""
FastMCP Server for Data Search Agent Tools
All tools from the data search agent are exposed through this MCP server.

This module centralizes all tool implementations using FastMCP decorators.
The tools can be:
1. Run as a standalone MCP server (python -m agents.mcp_server)
2. Imported directly by ADK tools as regular Python functions
"""
import os
import json
import logging
from typing import Any

from fastmcp import FastMCP
import chromadb
import chromadb.config
import requests

# Import constants and utilities
# These imports work when the module is imported as part of the agents package
try:
    from .constants.constants import COLUMN_NAMES_STATES, COLUMN_NAMES_REF_DOCS_STATES
    from .utils.database_utils import POOL
except ImportError:
    # Fallback for when run as __main__
    from constants.constants import COLUMN_NAMES_STATES, COLUMN_NAMES_REF_DOCS_STATES
    from utils.database_utils import POOL

# Initialize FastMCP server
mcp = FastMCP("Data Search Agent Tools")

# Environment variables for external services
CHROMADB_HOST = os.getenv("CHROMADB_HOST")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))
CHROMADB_COLLECTION_NAME = os.getenv("CHROMADB_COLLECTION_NAME")
TEXT_EMBEDDING_MODEL_URL = os.getenv("TEXT_EMBEDDING_MODEL_URL")
TEXT_EMBEDDING_MODEL_NAME = os.getenv("TEXT_EMBEDDING_MODEL_NAME")


def _serialize_for_cell(data: str) -> str:
    """
    Remove NBSP and other special characters for safe CSV/Excel cell storage.

    Args:
        data: String data to serialize

    Returns:
        Cleaned string
    """
    return data.replace("\u00A0", " ")


def _get_embedding(text_list: list[str]) -> list[list[float]]:
    """
    Get embeddings from the BGE-M3-KO model.

    Args:
        text_list: List of texts to embed

    Returns:
        List of embedding vectors
    """
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


@mcp.tool()
def exit_column_extraction_loop(column_names: dict[str, Any]) -> dict[str, Any]:
    """
    Call this function ONLY when the column name extraction from user input has completed,
    signaling the iterative process should end.

    Args:
        column_names: The extracted column names dictionary with structure:
                     {"items": [{"extracted_column_name": str}, ...]}

    Returns:
        Dictionary with status and message
    """
    logging.debug("[Tool Call] exit_column_extraction_loop triggered")

    if not column_names or len(column_names.get("items", [])) == 0:
        return {
            "status": "error",
            "message": "Column name extraction required."
        }

    return {
        "status": "success",
        "message": "Column name extraction completed.",
        "escalate": True
    }


@mcp.tool()
async def query_bga_database(generated_sql: str) -> dict[str, Any]:
    """
    Query data from BGA database using given SQL statement.

    Args:
        generated_sql: Complete SQL statement for PostgreSQL database.

    Returns:
        Dictionary with status, message, and query results
    """
    generated_sql = _serialize_for_cell(generated_sql)
    res = []

    logging.debug(f"Generated SQL: {generated_sql}")

    try:
        async with POOL.connection() as conn:
            logging.debug(f"Connection: {conn}")
            async with conn.cursor() as cur:
                await cur.execute(query=generated_sql)
                raw_res = await cur.fetchall()
                columns = [item.name for item in cur.description]
                res = [{k: v for k, v in zip(columns, row)} for row in raw_res]
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error while querying DB: {e}"
        }

    logging.debug(f"[Tool] query_bga_database: {res=}"[:100])

    return {
        "status": "success",
        "message": "SQL executed.",
        "data": {
            "type": "csv_table",
            "content": {
                "sql": generated_sql,
                "records": res
            }
        },
        "escalate": True
    }


@mcp.tool()
def get_sim_search(query_list: list[str], n_results: int = 3) -> dict[str, Any]:
    """
    Perform similarity search using ChromaDB to find relevant documents.

    Args:
        query_list: List of query strings to search for
        n_results: Number of results to return (default: 3)

    Returns:
        Dictionary with search results
    """
    chroma_client = chromadb.HttpClient(
        host=CHROMADB_HOST,
        port=CHROMADB_PORT,
        settings=chromadb.config.Settings(allow_reset=True, anonymized_telemetry=False)
    )

    collection = chroma_client.get_collection(CHROMADB_COLLECTION_NAME)
    embeddings = _get_embedding(query_list)
    query_res = collection.query(query_embeddings=embeddings, n_results=n_results)

    logging.debug(f"ChromaDB query results: {query_res}")

    return {
        "status": "success",
        "documents": query_res["documents"]
    }


@mcp.tool()
def get_sql_query_references(user_input: str, n_results: int = 15) -> dict[str, Any]:
    """
    Get SQL query reference documents based on user input using similarity search.
    This tool performs RAG (Retrieval-Augmented Generation) to find relevant
    column metadata and documentation.

    Args:
        user_input: User's natural language query
        n_results: Number of reference documents to retrieve (default: 15)

    Returns:
        Dictionary with retrieved reference documents
    """
    # Get similarity search results
    search_result = get_sim_search([user_input], n_results=n_results)

    if search_result.get("status") == "success":
        docs = search_result.get("documents", [[]])[0]
        docs_json = json.dumps(docs, ensure_ascii=False)

        return {
            "status": "success",
            "message": f"Retrieved {len(docs)} reference documents",
            "reference_docs": docs_json,
            "documents": docs
        }
    else:
        return {
            "status": "error",
            "message": "Failed to retrieve reference documents"
        }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
