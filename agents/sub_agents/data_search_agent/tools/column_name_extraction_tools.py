"""
Column Name Extraction Tools - ADK Wrapper for FastMCP Tools

This module provides Google ADK-compatible wrappers for the FastMCP tools
defined in agents.mcp_server. The actual tool logic is centralized in the
MCP server for consistency and maintainability.
"""
import logging

from google.adk.tools import ToolContext

from agents.constants.constants import COLUMN_NAMES_STATES
from agents.custom_types.tool_response import ToolResponse

# Import the FastMCP tool implementations
from agents import mcp_server


def exit_column_extraction_loop(tool_context: ToolContext):
    """
    Call this function ONLY when the column name extraction from user input has completed,
    signaling the iterative process should end.

    This is an ADK wrapper for the FastMCP tool implementation.
    """
    logging.debug(
        f"[Tool Call] exit_column_extraction_loop triggered by {tool_context.agent_name}"
    )

    # Get current column names from state
    curr_column_names = tool_context.state.get(COLUMN_NAMES_STATES, {"items": []})

    # Call the FastMCP tool implementation
    result = mcp_server.exit_column_extraction_loop(curr_column_names)

    # Handle escalation if indicated in result
    if result.get("escalate"):
        tool_context.actions.escalate = True

    # Convert to ADK ToolResponse format
    return ToolResponse(
        status=result.get("status", "success"),
        message=result.get("message", "")
    ).to_json()





