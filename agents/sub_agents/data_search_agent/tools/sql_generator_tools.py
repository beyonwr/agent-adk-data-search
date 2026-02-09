import json
import logging 
import re

from google.adk.tools import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest
from google.genai.types import Content, Part 

from agents.constants.constants import BGA_COLUMN_NAMES_REF_DOCS_STATES, BGA_COLUMN_NAMES_STATES
from agents.custom_types.tool_response import ToolResponse, ToolResponseData
from agents.sub_agents.data_search_agent.tools.bga_column_name_processor import (
    get_sim_search,
)
from agents.utils.database_utils import POOL

MAX_RESULT_ROWS = 300
MAX_RESULT_COLUMNS = 20


def _limit_select_clause(sql: str, max_columns: int = MAX_RESULT_COLUMNS) -> str:
    """Limit the number of columns in SELECT list (no-op for SELECT *)."""
    m = re.match(r"(?is)^\s*select\s+(.*?)\s+from\s+", sql)
    if not m:
        return sql

    select_expr = m.group(1).strip()
    if select_expr == "*":
        return sql

    columns = [col.strip() for col in select_expr.split(",") if col.strip()]
    if len(columns) <= max_columns:
        return sql

    limited_select_expr = ", ".join(columns[:max_columns])
    return sql[:m.start(1)] + limited_select_expr + sql[m.end(1):]


def _ensure_limit_clause(sql: str, max_rows: int = MAX_RESULT_ROWS) -> str:
    """Ensure SQL has LIMIT and clamp to max_rows if needed."""
    limit_match = re.search(r"(?is)\blimit\s+(\d+)", sql)
    if limit_match:
        current_limit = int(limit_match.group(1))
        if current_limit > max_rows:
            return re.sub(r"(?is)\blimit\s+\d+", f"LIMIT {max_rows}", sql, count=1)
        return sql

    return sql.rstrip().rstrip(";") + f" LIMIT {max_rows};"

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
    generated_sql = _limit_select_clause(generated_sql, max_columns=MAX_RESULT_COLUMNS)
    generated_sql = _ensure_limit_clause(generated_sql, max_rows=MAX_RESULT_ROWS)
    res = []

    logging.debug(f"Generated SQL: {generated_sql}")
    async with POOL.connection() as conn:
        logging.debug(f"{conn}")
        async with conn.cursor() as cur:
            try:
                await cur.execute(query=generated_sql)
                raw_res = await cur.fetchmany(MAX_RESULT_ROWS)
                columns = [item.name for item in cur.description][:MAX_RESULT_COLUMNS]
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
    extracted_column_names = callback_context.state.get(BGA_COLUMN_NAMES_STATES, {}).get("items", [])
    extracted_column_queries = [item.get("extracted_column_name") for item in extracted_column_names if item.get("extracted_column_name")]

    search_queries = [user_input, *extracted_column_queries]
    docs_per_query = get_sim_search(search_queries, n_results=20)

    deduped_docs = []
    seen_docs = set()
    for docs in docs_per_query:
        for doc in docs:
            if doc in seen_docs:
                continue
            seen_docs.add(doc)
            deduped_docs.append(doc)

    docs = deduped_docs[:20]
    docs_json = json.dumps(docs, ensure_ascii=False)

    # Store in state so {{bga_column_names_reference_docs?}} template works for sql_reviewer too
    callback_context.state[BGA_COLUMN_NAMES_REF_DOCS_STATES] = docs_json

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



    
