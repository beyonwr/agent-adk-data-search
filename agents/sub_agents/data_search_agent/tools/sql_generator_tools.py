import json
import logging 

from google.adk.tools import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest
from google.genai.types import Content, Part 

from agents.constants.constants import COLUMN_NAMES_REF_DOCS_STATES
from agents.custom_types.tool_response import ToolResponse, ToolResponseData
from agents.sub_agents.data_search_agent.tools.bga_column_name_processor import (
    get_sim_search,
)
from agents.utils.database_utils import POOL

def _serialize_for_cell(data):
    """
    JSON, dict, list 등 어떤 구조든
    엑셀/CSV 한 셀 안에 안전하게 들어갈 수 있는 문자열로 변환.
    """
    # NBSP 제거 (LLM 출력 보호)
    s = data.replace("\u00A0", " ")
    return s

async def query_bga_database(generated_sql: str, tool_context: ToolContext):
    """
    Query data from BGA database using given SQL statement.
    Args:
        generated_sql: str. Complete SQL statement for PostgreSQL database.
    """

    generated_sql = _serialize_for_cell(generated_sql)
    res = []

    logging.debug(f"Generated SQL: {generated_sql}")
    async with POOL.connection() as conn:
        logging.debug(f"{conn}")
        async with conn.cursor() as cur:
            try:
                await cur.execute(query=generated_sql)
                raw_res = await cur.fetchall()
                columns = [item.name for item in cur.description]
                res = [{k: v for k, v in zip(columns, row)} for row in raw_res]

            except Exception as e:
                return ToolResponse(
                    status="error", message=f"Error while querying DB: {e}"
                ).to_json()


    logging.debug(f"[Tool] query_bga_database: {res=}"[:100])
    tool_context.actions.escalate = True
    return ToolResponse(
        status = "success",
        message = f"SQL executed.",
        data = ToolResponseData(
            type="csv_table", content={"sql": generated_sql, "records": res}
        ).to_json(),
    ).to_json()


def get_sql_query_references_before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
):
    user_input = callback_context.user_content.parts[0].text
    docs = get_sim_search([user_input], n_results=15)[0]
    docs_json = json.dumps(docs, ensure_ascii=False)

    # Store in state so {{column_names_reference_docs?}} template works for sql_reviewer too
    callback_context.state[COLUMN_NAMES_REF_DOCS_STATES] = docs_json

    context_contents = Content(
        parts = [
            Part(
                text=f"Retrieved docs relevant to user query: {docs_json}"
            )
        ],
        role="user",
    )
    llm_request.contents.append(context_contents)
    logging.debug(f"{llm_request=}")
    return



    