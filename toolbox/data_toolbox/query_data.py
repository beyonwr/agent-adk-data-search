import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
from dateutil.tz import tzlocal

from ..utils.path_resolver import save_resource
from .utils.db_clients import get_pool


def _serialize_for_cell(data: str) -> str:
    """
    JSON, dict, list 등 어떤 구조든
    엑셀/CSV 한 셀 안에 안전하게 들어갈 수 있는 문자열로 변환.
    """
    # NBSP 제거 (LLM 출력 보호)
    s = data.replace("\u00A0", " ")
    return s


async def query_data(
    sql_query: str,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Execute SQL query on PostgreSQL and return results as CSV resource.

    Args:
        sql_query: Complete SQL statement for PostgreSQL database
        limit: Optional limit for number of rows to return (default: no limit)

    Returns:
        Dict with status and outputs (resource_link type with CSV file)
    """
    # Sanitize SQL query
    sql_query = _serialize_for_cell(sql_query)

    logging.debug(f"Executing SQL query: {sql_query}")

    # Execute query
    try:
        pool = get_pool()
        async with pool.connection() as conn:
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
            "status": "error",
            "outputs": [
                {
                    "type": "EMPTY_RESULT",
                    "message": "Query executed successfully but returned no results"
                }
            ]
        }

    data_df = pd.DataFrame.from_records(records)
    row_count = len(data_df)

    # Apply limit if specified
    if limit is not None and limit > 0:
        data_df = data_df.head(limit)

    # Save as CSV resource
    job_id = uuid.uuid4().hex
    csv_uri, csv_filename, csv_mime_type = save_resource(data_df, job_id, "csv")

    # Generate description
    description = (
        f"SQL 쿼리 결과 | {row_count}행 × {len(columns)}열 | "
        f"컬럼: {', '.join(columns[:5])}"
        f"{'...' if len(columns) > 5 else ''}"
    )

    # Return resource link
    return {
        "status": "success",
        "outputs": [
            {
                "type": "resource_link",
                "uri": csv_uri,
                "filename": csv_filename,
                "mime_type": csv_mime_type,
                "description": description,
                "metadata": {
                    "row_count": row_count,
                    "columns": columns,
                    "timestamp": datetime.now(tzlocal()).isoformat(),
                }
            }
        ]
    }
