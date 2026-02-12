from __future__ import annotations

import os
import json
import pandas as pd 
from dotenv import load_dotenv
load_dotenv("toolbox/.env")

from pathlib import Path
from typing import Any, Dict, Tuple
from ..utils.resource_registry import add_resource

ADK_ARTIFACT_ROOT = os.environ.get("ADK_ARTIFACT_ROOT")
MCP_RESOURCE_ROOT = Path(os.environ.get("MCP_RESOURCE_ROOT"))

def get_artifact_path(
    user_id: str,
    session_id: str,
    artifact_name: str,
    versions: int,
)-> str:
    base_path = Path(ADK_ARTIFACT_ROOT)
    path = (
        base_path
        / user_id
        / "sessions"
        / session_id
        / "artifacts"
        / artifact_name
        / "versions"
        / str(version)
        / artifact_name
    )

    return path.as_posix()


# TODO artifact_locator 를 schema로 통합한 후에는 제거 예정입니다.
def resolve_artifact_path(
    artifact_locator: Dict[str,Any],
) -> str:
    """
    ADK artifact locator 를 실제 파일 경로로 반환한다.

    artifact_locator 예:
        {
            "user_id": "user123",
            "session_id": "ssssA",
            "artifact_name": "dataset.csv",
            "version": 3,
        }
    """

    required_keys = ["user_id", "session_id", "artifact_name", "version"]

    for key in required_keys:
        value = artifact_locator.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f" artifact_locator에 필수 항목 '{key}'이(가) 누락되었거나 비어있습니다.")

    user_id = artifact_locator["user_id"]
    session_id = artifact_locator["session_id"]
    artifact_name = artifact_locator["artifact_name"]
    version = str(artifact_locator["version"])

    path = (
        Path(ADK_ARTIFACT_ROOT)
        / user_id
        / "sessions"
        / session_id
        / "artifacts"
        / artifact_name
        / "versions"
        / version
        / artifact_name
    )

    return path.as_posix()

_MIME_BY_EXT = {
    "csv": "text/csv",
    "json": "application/json",
    "png": "image/png",
    "html": "text/html",
    "htm": "text/html",
    "txt": "text/plain",
}


def _get_mime_type(ext: str) -> str:
    """확장자에 대응하는 mime_type 변환. 미등록이면 application/octet-stream."""
    e = (ext or "").lstrip(".").lower()
    return _MIME_BY_EXT.get(e, "application/octet-stream")

def get_mcp_resource_path(job_id: str, ext: str) -> Tuple[Path, str, str]:
    """
    MCP릭소스 저장 경로(Path)와 URI, mime_type을 만든다.

    Parameters:
        job_id (str): 결과 식별자(파일명 prefix)
        ext (str): 'csv'|'json'|'png'|'html' 등 (점 제외 권장)

    Returns:
        (abs_path, uri, mime_type)
        - abs_path: 실제 저장할 절대 경로 (Path)
        - uri: mcp://resource/<job_id>.<ext>
        - mime_type: 확장자 기반 mime (미등록이면 application/octet-stream)

    Raises:
        ValueError: MCP_RESOURCE_ROOT 미설정
    """
    
    if not MCP_RESOURCE_ROOT:
        raise ValueError("MCP_RESOURCE_ROOT 환경변수가 설정되지 않았습니다.")

    root = Path(MCP_RESOURCE_ROOT).resolve()
    root.mkdir(parents=True, exist_ok=True)

    safe_ext = (ext or "").lstrip(".").lower()
    if not safe_ext:
        raise ValueError("ext 가 이어있습니다.")

    abs_path = (root / f"{job_id}.{safe_ext}").resolve()

    if root not in abs_path.parents and abs_path != root:
        raise ValueError("잘못된 MCP resource 경로입니다.")

    url = f"mcp://resources/{abs_path.name}"
    mime = _get_mime_type(safe_ext)
    return abs_path, uri, mime


def save_resource_bytes(data: bytes, job_id: str, ext: str) -> Tuple[str, str, str]:
    """
    bytes 를 MCP resource store에 저장 후 (uri, filename, mime_type) 변환.

    Parameters:
        data (bytes): 저장할 바이트 데이터
        job_id (str): 결과 식별자
        ext (str): 확장자 (json/png/html/csv 등)

    Returns:
        (uri, filename, mime_type)
    """
    abs_path, uri, mime_type = get_mcp_resource_path(job_id=job_id, ext=ext)
    abs_path, parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_bytes(data)

    add_resource(
        uri=uri,
        mime_type=mime_type,
        path=abs_path
    )
    
    return uri, abs_path.name, mime_type


def save_resource(
    obj: Any,
    job_id: str,
    ext: str,
) -> Tuple[str, str, str]:

    """
    (편의/호환) obj를 MCP resource store 에 저장 후 (uri, filename, mime_type) 변환.
    - csv: pandas.DataFrame만 지원
    - json: dict/list 등 JSON 직렬화 가능한 객체

    PNG/HTML 등은 save_resource_bytes()를 사용하세요.

    Parameters:
        obj: pd.DataFrame 또는 dict/list 등
        job_id (str): 결과 식별자
        ext (str): "csv"|"json"

    Returns:
        (uri, filename, mime_type)
    """
    safe_ext = (ext or "").lstrip(".").lower()
    abs_path, uri, mime_type = get_mcp_resource_path(job_id=job_id, ext=safe_ext)

    if safe_ext == "csv":
        if not isinstance(obj, pd.DataFrame):
            raise ValueError("csv 저장은 pandas.DataFrame만 지원합니다.")
        with abs_path.open("w", encoding="utf-8-sig", newline="") as f:
            obj.to_csv(f, index=False, lineterminator="\r\n", na_rep="null")
        return uri, abs_path.name, mime_type

    if safe_ext == "json":
        with abs_path.open("w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    add_resource(
        uri=uri,
        mime_type=mime_type,
        path=abs_path
    )

    return uri, abs_path.name, mime_type