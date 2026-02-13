import logging
from typing import Any, Dict

from .utils.db_clients import (
    POSTGRES_DB_NAME,
    POSTGRES_DB_HOST,
    POSTGRES_DB_PORT,
    POSTGRES_DB_TABLE,
    CHROMADB_HOST,
    CHROMADB_PORT,
    CHROMADB_COLLECTION_NAME,
    TEXT_EMBEDDING_MODEL_NAME,
)


async def get_database_context() -> Dict[str, Any]:
    """
    Get current database and environment context information.

    Returns database connection details, ChromaDB configuration, and other
    environment settings that are useful for data analysis agents.

    This tool helps agents understand:
    - Which PostgreSQL database and table they're working with
    - Available ChromaDB collections for similarity search
    - Embedding model being used

    Returns:
        Dict with status and context information including:
        - postgresql: DB name, host, port, default table
        - chromadb: Host, port, collection name
        - embedding: Model name
    """
    logging.debug("Retrieving database context information")

    # Prepare context information
    context = {
        "postgresql": {
            "database": POSTGRES_DB_NAME or "Not configured",
            "host": POSTGRES_DB_HOST or "Not configured",
            "port": POSTGRES_DB_PORT or "Not configured",
            "default_table": POSTGRES_DB_TABLE or "Not configured",
            "note": "Use query_data() tool to execute SQL queries on this database"
        },
        "chromadb": {
            "host": CHROMADB_HOST or "Not configured",
            "port": str(CHROMADB_PORT),
            "collection": CHROMADB_COLLECTION_NAME or "Not configured",
            "note": "Use search_similar_columns() tool to find relevant column names"
        },
        "embedding": {
            "model": TEXT_EMBEDDING_MODEL_NAME or "Not configured",
            "note": "Model used for vector similarity search in ChromaDB"
        }
    }

    # Check for missing critical configuration
    missing_configs = []
    if not POSTGRES_DB_NAME:
        missing_configs.append("POSTGRESQL_DB_NAME")
    if not CHROMADB_COLLECTION_NAME:
        missing_configs.append("CHROMADB_COLLECTION_NAME")

    if missing_configs:
        logging.warning(f"Missing environment variables: {', '.join(missing_configs)}")
        context["warnings"] = [
            f"Missing environment variables: {', '.join(missing_configs)}",
            "Some tools may not work properly without these configurations"
        ]

    return {
        "status": "success",
        "context": context,
        "message": "Database context retrieved successfully"
    }
