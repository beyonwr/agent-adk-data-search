"""
Data Search Agent Tools - ADK Tool Exports

This module exports Google ADK-compatible tool wrappers.
All tool implementations are centralized in agents.mcp_server using FastMCP.

Tool Architecture:
- Core implementations: agents.mcp_server (FastMCP decorators)
- ADK wrappers: This package (Google ADK compatible interfaces)
- The wrappers handle ToolContext/CallbackContext and call mcp_server functions

Available Tools:
- exit_column_extraction_loop: Signal completion of column extraction
- query_bga_database: Execute PostgreSQL queries
- get_sql_query_references_before_model_callback: RAG callback for SQL generation
- get_sim_search: DEPRECATED - Use agents.mcp_server.get_sim_search directly

For new code, consider importing directly from agents.mcp_server for consistency.
"""

# ADK Tool wrappers - these handle ToolContext and call mcp_server
from .column_name_extraction_tools import exit_column_extraction_loop
from .sql_generator_tools import (
    query_bga_database,
    get_sql_query_references_before_model_callback,
)

# Deprecated backward compatibility wrapper
# New code should use: from agents import mcp_server
from .bga_column_name_processor import get_sim_search

__all__ = [
    "exit_column_extraction_loop",
    "query_bga_database",
    "get_sql_query_references_before_model_callback",
    "get_sim_search",  # Deprecated
]
