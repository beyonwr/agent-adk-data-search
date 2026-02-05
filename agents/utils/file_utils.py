from base64 import b64decode
import io
import json
import logging
import os
from copy import deepcopy
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List
from dateutil.tz import tzlocal
from dotenv import load_dotenv

load_dotenv()

import google.genai.types as types
import pandas as pd
from google.adk.agents.callback_context import CallbackContext 
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools.base_tool import BaseTool 
from google.adk.tools.tool_context import ToolContext 
from mcp import types as mcp_types
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import CallToolResult

from agents.custom_types.tool_response import ToolResponse, ToolResponseData
from ..constants import NUM_OF_DISPLAYED_DATA
from .state_manager_utils import add_artifact_to_state, get_all_states
from ..constants import ARTIFACT_STATES, NUM_OF_DISPLAYED_DATA


class BeforeModelCallbackState(Enum):
    START_QUERY_IMG_SIMILARITY = 0
    RETRY_QUERY_IMG_SIMILARITY = 1
    FUNC_RESPONSE = 2

mime_lookup_for_tool = {
    "anlyze_basic_statistics": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "generate_chart_from_data": "image/png",
}

def make_subset_data(
    total_count: int, data_df: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    """
    function to extract only a few pieces of data from the dataframe

    Args:
        total_count: number of original data frame
        data_df: original data frame

    Returns:
        pd.DataFrame: Dataframe created by deleting that the value of the column of the dataframe is NaN
        dict: dict, which is a subsest created by extracting only a few from the dataframe
    """

    num_of_partial_data = (
        NUM_OF_DISPLAYED_DATA if total_count > NUM_OF_DISPLAYED_DATA else total_count
    )

    dropped_data_df = data_df.dropna(axis=1, how="all")
    partial_data_df = dropped_data_df.iloc[
        :num_of_partial_data, 0 : min(7, len(dropped_data_df.columns))
    ]
    partial_data = partial_data_df.to_dict()
    return dropped_data_df, partial_data

def make_artifact_structure_for_xlsx(tool_response: dict) -> types.Part:
    """
    function to make artifact structure for xlsx

    Args:
        tool_response; number of original dataframe

    Returns:
        types.Part : structure of artifact to be saved
    """

    if tool_response.get("report_xlsx") is not None:
        data = tool_response["report_xlsx"]
    else:
        return None

    data.seek(0)
    statics_report_xlsx = data.getvalue()
    
    artifact_to_save = types.Part(
        inline_data=types.Blob(
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            data=statics_report_xlsx,
        )
    )

    return artifact_to_save

async def get_content_from_rag_server(
    url:str,
) -> tuple[mcp_types.BlobResourceContents, dict]:
    """
    function to get contents from rag server

    Args:
        url: URI information of data to be read from the RAG server
    
    Returns:
        mcp_types.BlobResourceContents: Data read from RAG server
        dict: return dict
    """

    part0 = None
    ret_dict = None
    try:
        async with sse_client(url=os.getenv("SQL_GENERATION_TOOL")) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                rr: mcp_types.ReadResourceResult - await session.read_resource(url)
                if not rr.contents:
                    ret_dict = {
                        "status": "error",
                        "reason": f"No content for resource: {url}",
                    }
                else:
                    part0 = rr.contents[0]
    except Exception as e:
        ret_dict = {"status": "error", "reason": f"resources.read 실패: {e}"}
    return part0, ret_dict

async def save_file_artifact_after_tool_callback(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_response: CallToolResult,
    tool_context: ToolContext,
) -> Dict:
    """
    after_tool_callback to save a file through artifact to use later

    Args: 
        tool: tool that calls the corresponding callback function
        args: key and value used for query
        tool_response: response of the tool that calls the corresponding callback function

    Returns:
        dict: a dictionary containing the API response, typically with a "status", "total_count" and "data" key.
    """

    logging.info(
        f"==> Called After Callback: {__name__}.{save_file_artifact_after_tool_callback.__name__}"
    )

    agent_name = tool_context.agent_name
    tool_name = tool.name 

    logging.info(
        f"[Callback] After tool call for tool '{tool_name}' in agent '{agent_name}'"
    )

    l = [(f"{a=}", type(a)) for a in args]
    logging.info(f"[Callback] Args used: {args=} {l=}")
    logging.info(f"[Callback] Original tool_response: {type(tool_response)} {str(tool_response)[:500]}")

    file_mime_type = mime_lookup_for_tool.get(tool_name)

    logging.debug(f"file_mime_type: {file_mime_type}")

    if tool_response.get("data", None) is not None:
        tool_response_data = tool_response.get("data")
        if tool_response_data.get("type", None) is None:
            raise ValueError(f"Tool response data must have 'type' property: {tool_response_data}")
        tool_response_data_type = tool_response_data.get("type")
        if tool_response_data_type == "csv_table":
            table_content = tool_response_data.get("content", None).get("records", [])
            if table_content is None:
                raise ValueError(f"Tool response data empty: {table_content=}")
            
            data_df = pd.DataFrame.from_records(table_content)
            text_data = data_df.to_csv(index=False, encoding="utf-8-sig")
            csv_bytes = text_data.encode(encoding="utf-8-sig")

            csv_artifact = types.Part(inline_data=types.Blob(mime_type="text/csv", data=csv_bytes))
            now = datetime.now(tzlocal())
            file_name = f'output_data_{now.strftime("%Y%m%d_%H%M%S")}.csv'
            version = await tool_context.save_artifact(filename=file_name, artifact=csv_artifact)
            total_count = len(data_df)

            artifact = add_artifact_to_state(
                artifact_type="table",
                context=tool_context,
                filename=file_name,
                mime_type="text/csv",
                data_length = total_count,
                sql_query = args.get("sql_queery")
            )

            states = tool_context.state.get(ARTIFACT_STATES, {})
            logging.info(f"[STATE] DATA_SEARCH_AGENT - 개수: {len(states)}, 키: {list(states.keys())}, 상태: {get_all_states(tool_context)}")

            return ToolResponse(status="success", message=f"Query successfully executed. Resulting {total_count} records stored in states. Notice user to check the attachment files.").to_json()

    if tool_name == "generate_chart_from_data":
        if tool_response["status"] == "success":
            img_data = tool_response["data"]["img_data"]

            artifact_to_save = types.Part(
                inline_data=types.Blob(mime_type=file_mime_type, data=img_data)
            )

            temp_file_name = args["filename"]
            file_name = f"{temp_file_name.split('.'[0])}.png"
            ret_dict = {"status": "success"}

        else:
            ret_dict = {"status": "error"}
    elif tool_name == "anlyze_basic_statistics":
        artifact_to_save = make_artifact_structure_for_xlsx(tool_response)
        if artifact_to_save == None:
            return {
                "status": "error",
                "reason": "tool_respone 안에 report_xlsx가 없습니다.",
            }

        if tool_response.get("file_name") is not None:
            file_name = tool_response["file_name"]
        else:
            return {
                "status": "error",
                "reason": "tool_response 안에 file_name가 없습니다.",
            }
        ret_dict = {"status": "success"}

    else:
        logging.info("No files to process")
        return None

    try:
        version = await tool_context.save_artifact(
            filename=file_name, artifact=artifact_to_save
        )
        if file_mime_type == "image/png":
            artifact = add_artifact_to_state(
                artifact_type="img",
                context=tool_context,
                filename=file_name,
                mime_type="image/png",
            )

            states = tool_context.state.get(ARTIFACT_STATES, {})

            logging.info(
                f"[STATE] DATA_SEARCH_AGNENT - 개수: {len(states)}, 키: {list(states.keys())}, 상태: {get_all_states(tool_context)}"
            )

        else:
            artifact = None

        if artifact == None:
            raise Exception(f"Failed to save artifact: {file_name} from {tool_name}")

    except ValueError as e:
        logging.info(f"Error saving Python artifact: {e}")
    except Exception as e:
        logging.info(f"An unexpected error occurred during Python artifact save: {e}")

    return ret_dict









async def save_imgfile_artifact_before_agent_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    before_agent_callback to save a file through artifact to use later.
    
    Args:
    
    Returns:
        Optional[types.Content]: A content containing the list of parts(single message) and role(producer of the content).
    """

    logging.info(
        f"==> Called Before Callback: {__name__}.{save_imgfile_artifact_before_agent_callback.__name__}"
    )
    logging.debug(f"==> callback_context.user_content: {callback_context.user_content}")

    try:
        for part in callback_context.user_content.parts:
            if hasattr(part, "inline data") and part.inline_data:
                logging.debug(f"User input file: {part.inline_data}")
                figure_artifact = types.Part(
                    inline_data=types.Blob(
                        mime_type = part.inline_data.mime_type, data=part.inline_data.data
                    )
                )
                file_naem = "user_input_" + part.inline_data.display_name
                mime_type = part.inline_data.mime_type
                
                version = await callback_context.save_artifact(
                    filename = file_name, artifact=figure_artifact
                )
                
                artifact = add_artifact_to_state(
                    artifact_type="img",
                    context = callback_context,
                    filename = file_name,
                    mime_type = mime_type,
                )
                if not artifact:
                    error_message = f"Error while saving nartifact state"
                    logging.debug(error_message)
                    return types.Content(parts=[types.Part(text=error_message)])

                logging.debug(f"Input file saved to artifacts {artifact}")
        return None

    except Exception as e:
        error_message = f"Error saving user input image as artifact {e}"
        logging.debug(error_message)
        return types.Content(parts=[types.Part(text.error_message)])


def remove_non_text_part_from_llmrequest_before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:

    """
    before_model_callback to reduce size of the llm_request.contents and remove inline_data in content.part.

    Args:
        llm_request: provides an interface that users use to request natural language processing tasks.
                    part.inline_data of the contents is deleted in this function.

    Returns:
        Optional[LlmResponse]: A content containing the list of parts(single message) and role(producer of the content).
    """

    logging.info(
        f"==> Called Before Callback: {__name__}.{remove_non_text_part_from_llmrequest_before_model_callback.__name__}"
    )
    logging.debug(
        f"Entering Agent: {callback_context.agent_name} (Inv: {callback_context.invocation_id})"
    )
    logging.debug(f"Contents of the Original LLM Request: {llm_request.contents}")

    new_contents: list[types.Content] = []
    for content in llm_request.contents:
        new_content = deepcopy(content)

        parts_without_inline_data = list(
            filter(
                lambda part: getattr(part, "inline_data", None) == None, content.parts
            )
        )

        logging.debug(f"{parts_without_inline_data}")
        new_content.parts = parts_without_inline_data
        new_contents.append(new_content)

    llm_request.contents = new_contents

    logging.debug(f"Modified llm_request.contents : '{llm_request.contents}'")

    return None