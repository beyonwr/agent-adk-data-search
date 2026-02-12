import io
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import google.genai.types as types
import pandas as pd
from dateutil.tz import tzlocal
from google.adk.tools import ToolContext

from .utils.db_clients import POOL

STATE_QUERY_RESULTS = "workspace:query_results"


def _serialize_for_cell(data: str) -> str:
    """
    JSON, dict, list 등 어떤 구조든
    엑셀/CSV 한 셀 안에 안전하게 들어갈 수 있는 문자열로 변환.
    """
    # NBSP 제거 (LLM 출력 보호)
    s = data.replace("\u00A0", " ")
    return s


async def query_data(
    tool_context: ToolContext,
    sql_query: str,
    artifact_filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute SQL query on PostgreSQL and save results as ADK artifact.

    Args:
        tool_context: ADK ToolContext (auto-injected by calling agent)
        sql_query: Complete SQL statement for PostgreSQL database
        artifact_filename: Optional custom filename (default: query_result_YYYYMMDD_HHMMSS.csv)

    Returns:
        Dict with status, filename, version, row_count, columns, sample_rows
    """
    # Generate default filename with timestamp
    if artifact_filename is None:
        now = datetime.now(tzlocal())
        artifact_filename = f'query_result_{now.strftime("%Y%m%d_%H%M%S")}.csv'

    # Sanitize SQL query
    sql_query = _serialize_for_cell(sql_query)

    logging.debug(f"Executing SQL query: {sql_query}")

    # Execute query
    try:
        async with POOL.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query=sql_query)
                raw_res = await cur.fetchall()
                columns = [item.name for item in cur.description]
                records = [{k: v for k, v in zip(columns, row)} for row in raw_res]
    except Exception as e:
        logging.error(f"Error executing SQL query: {e}")
        return {
            "status": "error",
            "message": f"Error executing SQL: {e}",
        }

    # Convert to DataFrame
    if not records:
        # Empty result set
        return {
            "status": "success",
            "message": "Query executed successfully but returned no results",
            "row_count": 0,
            "columns": columns,
        }

    data_df = pd.DataFrame.from_records(records)
    row_count = len(data_df)

    # Generate CSV bytes
    csv_text = data_df.to_csv(index=False, encoding="utf-8-sig")
    csv_bytes = csv_text.encode(encoding="utf-8-sig")

    # Create artifact
    csv_artifact = types.Part.from_bytes(data=csv_bytes, mime_type="text/csv")

    # Save artifact
    try:
        version = await tool_context.save_artifact(
            filename=artifact_filename,
            artifact=csv_artifact
        )
    except Exception as e:
        logging.error(f"Error saving artifact: {e}")
        return {
            "status": "error",
            "message": f"Error saving artifact: {e}",
        }

    # Generate metadata profile
    profile = {
        "filename": artifact_filename,
        "version": int(version) if version is not None else None,
        "mime_type": "text/csv",
        "bytes": len(csv_bytes),
        "timestamp": datetime.now(tzlocal()).isoformat(),
        "row_count": row_count,
        "columns": columns,
    }

    # Try to generate additional metadata
    try:
        profile["dtypes"] = {c: str(data_df[c].dtype) for c in data_df.columns}

        # Sample rows (first 10)
        sample_rows = data_df.head(10).to_dict(orient="records")
        profile["sample_rows"] = sample_rows
    except Exception as e:
        logging.warning(f"Error generating additional metadata: {e}")
        profile["metadata_error"] = str(e)

    # Store in state
    state_index = tool_context.state.get(STATE_QUERY_RESULTS, {})
    if not isinstance(state_index, dict):
        state_index = {}

    state_index[artifact_filename] = profile
    tool_context.state[STATE_QUERY_RESULTS] = state_index

    # Return summary
    return {
        "status": "success",
        "message": f"Query executed successfully. {row_count} rows saved to artifact.",
        "filename": artifact_filename,
        "version": version,
        "row_count": row_count,
        "columns": columns,
        "sample_rows": profile.get("sample_rows", []),
    }
