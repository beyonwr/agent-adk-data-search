"""
SQL Generator Tools - ADK Wrapper for FastMCP Tools

This module provides Google ADK-compatible wrappers for the FastMCP tools
defined in agents.mcp_server. The actual tool logic is centralized in the
MCP server for consistency and maintainability.
"""
import json
import logging

from google.adk.tools import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest
from google.genai.types import Content, Part

from agents.constants.constants import COLUMN_NAMES_REF_DOCS_STATES
from agents.custom_types.tool_response import ToolResponse, ToolResponseData

# Import the FastMCP tool implementations
from agents import mcp_server


async def query_bga_database(generated_sql: str, tool_context: ToolContext):
    """
    Query data from BGA database using given SQL statement.

    This is an ADK wrapper for the FastMCP tool implementation.

    Args:
        generated_sql: Complete SQL statement for PostgreSQL database.
        tool_context: ADK tool context
    """
    logging.debug(f"[Tool Call] query_bga_database triggered by {tool_context.agent_name}")

    # Call the FastMCP tool implementation
    result = await mcp_server.query_bga_database(generated_sql)

    # Handle escalation if indicated in result
    if result.get("escalate"):
        tool_context.actions.escalate = True

    # Extract data from result
    status = result.get("status", "success")
    message = result.get("message", "")
    data = result.get("data")

    # Convert to ADK ToolResponse format
    if status == "error":
        return ToolResponse(status=status, message=message).to_json()

    return ToolResponse(
        status=status,
        message=message,
        data=ToolResponseData(
            type=data["type"],
            content=data["content"]
        ).to_json() if data else None
    ).to_json()


def get_sql_query_references_before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest
):
    """
    Before-model callback to retrieve SQL query reference documents using RAG.

    This function uses the FastMCP tool to get relevant documents from ChromaDB
    and injects them into the LLM context.

    Args:
        callback_context: ADK callback context
        llm_request: LLM request to modify
    """
    user_input = callback_context.user_content.parts[0].text

    # Call the FastMCP tool implementation for RAG
    result = mcp_server.get_sql_query_references(user_input, n_results=15)

    if result.get("status") == "success":
        docs_json = result.get("reference_docs", "[]")

        # Store in state so {{column_names_reference_docs?}} template works for sql_reviewer too
        callback_context.state[COLUMN_NAMES_REF_DOCS_STATES] = docs_json

        # Inject retrieved documents into LLM context
        context_contents = Content(
            parts=[
                Part(text=f"Retrieved docs relevant to user query: {docs_json}")
            ],
            role="user",
        )
        llm_request.contents.append(context_contents)
        logging.debug(f"RAG documents injected into LLM context: {len(result.get('documents', []))} docs")
    else:
        logging.warning("Failed to retrieve RAG documents")

    logging.debug(f"{llm_request=}")
    return

    