"""
BGA Column Name Processor - Wrapper for FastMCP Tools

This module provides backward-compatible wrappers for existing code that
imports these functions. The actual implementations are now centralized
in agents.mcp_server for consistency and maintainability.

DEPRECATED: This module is maintained for backward compatibility.
New code should import directly from agents.mcp_server.
"""
import logging
from typing import List

# Import the FastMCP tool implementations
from agents import mcp_server


def get_sim_search(query_list: List[str], n_results: int = 3) -> List[List[str]]:
    """
    Perform similarity search using ChromaDB to find relevant documents.

    DEPRECATED: Use agents.mcp_server.get_sim_search instead.

    Args:
        query_list: List of query strings to search for
        n_results: Number of results to return (default: 3)

    Returns:
        List of document lists (ChromaDB format)
    """
    logging.debug(f"[DEPRECATED] get_sim_search called with {len(query_list)} queries")

    # Call the FastMCP implementation
    result = mcp_server.get_sim_search(query_list, n_results)

    if result.get("status") == "success":
        # Return in the old format for backward compatibility
        return result.get("documents", [[]])
    else:
        logging.error("Failed to perform similarity search")
        return [[]]


def _get_embedding(text_list: List[str]) -> List[List[float]]:
    """
    Get embeddings from the BGE-M3-KO model.

    DEPRECATED: Use agents.mcp_server._get_embedding instead.

    Args:
        text_list: List of texts to embed

    Returns:
        List of embedding vectors
    """
    logging.debug(f"[DEPRECATED] _get_embedding called with {len(text_list)} texts")

    # Call the FastMCP implementation
    return mcp_server._get_embedding(text_list)