import logging

from google.adk.tools import ToolContext

from agents.constants.constants import COLUMN_NAMES_STATES
from agents.custom_types.tool_response import ToolResponse

def exit_column_extraction_loop(tool_context: ToolContext):
    """Call this function ONLY when the column name extraction from user input has completed, signaling the iterative process should end."""
    logging.debug(
        f"[Tool Call] exit_column_extraction_loop triggered by {tool_context.agent_name}"
    )
    curr_column_names = tool_context.state.get(COLUMN_NAMES_STATES, {"items": []})

    if len(curr_column_names["items"]) == 0:
        return ToolResponse(status="error", message="Column name extraction required.").to_json()

    tool_context.actions.escalate = True
    return ToolResponse(status="success", message="Column name extraction completed.").to_json()





