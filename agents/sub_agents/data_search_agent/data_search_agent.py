import os
import logging

from google.adk.agents import LlmAgent, SequentialAgent, LoopAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest
from google.genai.types import Content, Part
from pydantic import BaseModel, Field

from agents.constants.constants import COLUMN_NAMES_STATES, COLUMN_NAMES_REF_DOCS_STATES
from agents.custom_types.tool_response import ToolResponse, ToolResponseData

# Import FastMCP server directly
from agents import mcp_server

from ...utils.file_utils import save_file_artifact_after_tool_callback
from ...utils.prompt_utils import get_prompt_yaml


# ============================================================================
# ADK Tool Adapters for FastMCP Tools
# These lightweight adapters connect Google ADK's ToolContext to FastMCP tools
# ============================================================================

def exit_column_extraction_loop(tool_context: ToolContext):
    """
    ADK adapter for mcp_server.exit_column_extraction_loop.
    Signals completion of column name extraction.
    """
    logging.debug(
        f"[Tool Call] exit_column_extraction_loop triggered by {tool_context.agent_name}"
    )

    # Get current column names from state
    curr_column_names = tool_context.state.get(COLUMN_NAMES_STATES, {"items": []})

    # Call FastMCP tool directly
    result = mcp_server.exit_column_extraction_loop(curr_column_names)

    # Handle escalation
    if result.get("escalate"):
        tool_context.actions.escalate = True

    # Return ADK ToolResponse
    return ToolResponse(
        status=result.get("status", "success"),
        message=result.get("message", "")
    ).to_json()


async def query_bga_database(generated_sql: str, tool_context: ToolContext):
    """
    ADK adapter for mcp_server.query_bga_database.
    Executes SQL queries on PostgreSQL database.
    """
    logging.debug(f"[Tool Call] query_bga_database triggered by {tool_context.agent_name}")

    # Call FastMCP tool directly
    result = await mcp_server.query_bga_database(generated_sql)

    # Handle escalation
    if result.get("escalate"):
        tool_context.actions.escalate = True

    # Extract data from result
    status = result.get("status", "success")
    message = result.get("message", "")
    data = result.get("data")

    # Return ADK ToolResponse
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
    ADK callback adapter for mcp_server.get_sql_query_references.
    Retrieves reference documents using RAG for SQL generation.
    """
    user_input = callback_context.user_content.parts[0].text

    # Call FastMCP tool directly
    result = mcp_server.get_sql_query_references(user_input, n_results=15)

    if result.get("status") == "success":
        docs_json = result.get("reference_docs", "[]")

        # Store in state for template usage
        callback_context.state[COLUMN_NAMES_REF_DOCS_STATES] = docs_json

        # Inject documents into LLM context
        context_contents = Content(
            parts=[
                Part(text=f"Retrieved docs relevant to user query: {docs_json}")
            ],
            role="user",
        )
        llm_request.contents.append(context_contents)
        logging.debug(f"RAG documents injected: {len(result.get('documents', []))} docs")
    else:
        logging.warning("Failed to retrieve RAG documents")

    logging.debug(f"{llm_request=}")
    return


# ============================================================================
# Agent Configuration
# ============================================================================

MODEL = LiteLlm(
        model=os.getenv("ROOT_AGENT_MODEL"),
        api_base=os.getenv("ROOT_AGENT_API_BASE"),
        extra_headers={
            "Content-Type": "application/json",
            "Authorization": os.getenv("PADO_API_KEY")
        },
        stream=False,
)


COLUMN_NAME_EXTRACTOR_DESCRIPTION = get_prompt_yaml(
    tag="column_name_extractor_description"
)
COLUMN_NAME_EXTRACTOR_INSTRUCTION = get_prompt_yaml(
    tag="column_name_extractor_instruction"
)
COLUMN_NAME_REVIEWER_DESCRIPTION = get_prompt_yaml(
    tag="column_name_reviewer_description"
)
COLUMN_NAME_REVIEWER_INSTRUCTION = get_prompt_yaml(
    tag="column_name_reviewer_instruction"
)
POSTGRESQL_DB_NAME = os.getenv("POSTGRESQL_DB_NAME", "")
POSTGRESQL_DB_TABLE = os.getenv("POSTGRESQL_DB_TABLE", "")

SQL_GENERATOR_DESCRIPTION = get_prompt_yaml(tag="sql_generator_description")
SQL_GENERATOR_INSTRUCTION = get_prompt_yaml(tag="sql_generator_instruction").replace(
    "__POSTGRESQL_DB_NAME__", POSTGRESQL_DB_NAME
).replace(
    "__POSTGRESQL_DB_TABLE__", POSTGRESQL_DB_TABLE
)
SQL_REVIEWER_DESCRIPTION = get_prompt_yaml(tag="sql_reviewer_description")
SQL_REVIEWER_INSTRUCTION = get_prompt_yaml(tag="sql_reviewer_instruction").replace(
    "__POSTGRESQL_DB_NAME__", POSTGRESQL_DB_NAME
).replace(
    "__POSTGRESQL_DB_TABLE__", POSTGRESQL_DB_TABLE
)

class ExtractedSingleColumnName(BaseModel):
    extracted_column_name: str = Field(
        description="The name of a single column name extracted from user natural language query."
    )

class ExtractedColumnNames(BaseModel):
    items: list[ExtractedSingleColumnName] = Field(
        description="The list of column names extracted from user query."
    )

_column_name_extractor = LlmAgent(
    name="column_name_extractor",
    description=COLUMN_NAME_EXTRACTOR_DESCRIPTION,
    model=MODEL,
    output_key=COLUMN_NAMES_STATES,
    output_schema=ExtractedColumnNames,
    instruction=COLUMN_NAME_EXTRACTOR_INSTRUCTION,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

_column_name_reviewer = LlmAgent(
    name="column_name_reviewer",
    description=COLUMN_NAME_REVIEWER_DESCRIPTION,
    model=MODEL,
    instruction=COLUMN_NAME_REVIEWER_INSTRUCTION,
    tools=[exit_column_extraction_loop]
)

column_name_extraction_loop_agent = LoopAgent(
    name="column_name_extraction_loop",
    sub_agents=[_column_name_extractor, _column_name_reviewer],
    max_iterations=3,
)

_sql_generator = LlmAgent(
    name="sql_generator",
    description=SQL_GENERATOR_DESCRIPTION,
    model = MODEL,
    instruction=(SQL_GENERATOR_INSTRUCTION),
    before_model_callback=get_sql_query_references_before_model_callback,
)

_sql_reviewer = LlmAgent(
    name="sql_reviewer",
    description=SQL_REVIEWER_DESCRIPTION,
    model=MODEL,
    instruction=(SQL_REVIEWER_INSTRUCTION),
    tools=[query_bga_database],
    after_tool_callback=[save_file_artifact_after_tool_callback],
)

sql_generation_loop_agent = LoopAgent(
    name="sql_generation_loop_agent",
    sub_agents=[_sql_generator, _sql_reviewer],
    max_iterations=3,
)

data_search_agent = SequentialAgent(
    name="data_search_agent",
    sub_agents=[
        column_name_extraction_loop_agent,
        sql_generation_loop_agent,
    ],
)
