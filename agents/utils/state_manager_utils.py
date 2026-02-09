"""
통합된 State 관리 유틸리티
AppState 객체를 사용하여 table 과 img artifacts를 하나의 state에서 관리합니다.
"""

from typing import Dict, List, Literal, Tuple, Optional
import logging
from copy import deepcopy

from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext
import pandas as pd

from ..custom_types import AppState, ImgArtifact, TableArtifact
from ..constants import ARTIFACT_STATES

def _initialize_state(context: ToolContext | CallbackContext, invocation_id: str) -> Dict:
    """
    새로운 State 객체를 초기화하고 tool context에 저장합니다.
    기존 상태가 있으면 덮어쓰지 않고 유지합니다.

    Args:
        context: 상태 정보를 포함하는 context
        invocation_id: invocation의 고유 식별자
    """

    states = context.state.get(ARTIFACT_STATES, {})

    if invocation_id not in states:
        state = AppState()
        states[invocation_id] = state.to_json()

    logging.info(f"[STATE] 초기화, invocation_id: {invocation_id}")
    return states

def add_artifact_to_state(
    artifact_type: str,
    context: ToolContext | CallbackContext,
    filename: str,
    mime_type: str,
    img_size: Optional[Tuple[int, int]] = None,
    data_length: Optional[int] = None,
    sql_query: Optional[str] = None,
) -> ImgArtifact | TableArtifact | None:
    """
    State의 artifacts 리스트에 새로운 artifact를 추가합니다.

    Args:
        Required:
        artifact_type: artifact 타입 ("table" 또는 "img")
        invocation_id: invocation의 고유 식별자
        filename: artifact 파일명
        mime_type: artifact의 MIME 타입

        Optional:
        img_size: 이미지 사이즈 tuple (width, height)
        data_length: 데이터 크기
        columns: 데이터 컬럼명 list
        sql_query: 모델이 생성한 SQL 문

    Returns:
        성공적으로 추가되면 True, 실패하면 False
        
    """

    invocation_id = context.invocation_id
    artifact_states = _initialize_state(context, invocation_id)
    current_artifact_states = AppState.from_json(artifact_states[invocation_id])
    new_artifact_states = deepcopy(artifact_states)

    # 받아온 Context 활용하여 필수값 채우기
    user_query = context.user_content.parts[0].text
    function_call_id = context.function_call_id if hasattr(context, "function_call_id") else None

    # artifact_type에 따라 적절한 Artifact States 객체 생성
    artifact = None
    if artifact_type == "img":
        artifact = ImgArtifact(
            type=artifact_type,
            filename=filename,
            mime_type=mime_type,
            function_call_id=function_call_id if function_call_id else f"user_input_from_invocation_{invocation_id}",
            user_query=user_query,
        )
    elif artifact_type == "table":
        artifact = TableArtifact(
            filename=filename,
            mime_type=mime_type,
            function_call_id=function_call_id,
            user_query=user_query,
            sql_query=sql_query,
            data_length=data_length,
        )
    else:
        error_message = f"[STATE] 지원하지 않는 artifact_type: {artifact_type}"
        logging.error(error_message)
        raise ValueError(error_message)
    
    current_artifact_states.artifacts.append(artifact)
    new_artifact_states[invocation_id] = current_artifact_states.to_json()
    context.state[ARTIFACT_STATES] = new_artifact_states
    logging.info(
        f"[STATE] artifact 추가, invocation_id: {invocation_id}, artifact: {artifact}"
    )
    return artifact

def get_state(tool_context: ToolContext, invocation_id: str) -> Optional[AppState]:
    """
    invocatoin id로 state 객체를 조회합니다.

    Args:
        tool_context: 상태 정보를 포함하는 tool context
        invocation_id: invocation의 고유 식별자

    Returns:
        찾으면 AppState 객체, 없으면 None
    """

    if (
        ARTIFACT_STATES not in tool_context.State
        or invocation_id not in tool_context.state[ARTIFACT_STATES]
    ):
        return None

    return AppState.from_json(tool_context.state[ARTIFACT_STATES][invocation_id])


def delete_state(tool_context: ToolContext, invocation_id: str) -> bool:
    """
    State 객체를 tool context에서 삭제합니다.

    Args:
        tool_context: 상태 정보를 포함하는 tool context
        invoation_id: invocation의 고유 식별자

    Returns:
        성공적으로 삭제되면 True, 찾을 수 없으면 False
    """
    if (
        ARTIFACT_STATES not in tool_context.state
        or invocation_id not in tool_context.state[ARTIFACT_STATES]
    ):
        return False

    del tool_context.state[ARTIFACT_STATES][invocation_id]
    return True

def get_all_states(tool_context: ToolContext) -> Dict[str, AppState]:
    """
    tool context에서 모든 state 객체를 조회합니다.

    Args:   
        tool_context: 상태정보를 포함하는 tool context
    
    Returns:
        invocation_id를 AppState 객체에 매핑하는 딕너리
    """
    if ARTIFACT_STATES not in tool_context.state:
        return {}

    return {
        invocation_id: AppState.from_json(state_json)
        for invocation_id, state_json in tool_context.state[ARTIFACT_STATES].items()
    }

def clear_all_states(tool_context: ToolContext) -> None:
    """
    tool context 에서 모든 state 객체를 삭제합니다.
    """
    tool_context.state[ARTIFACT_STATES] = {}
