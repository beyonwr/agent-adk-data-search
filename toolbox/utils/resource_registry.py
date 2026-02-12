from pathlib import Path
from typing import Callable, Optional
"""
의존성 주입을 위한 패키지 입니다.
시스템 시작과 함께 mcp_server.py 에서 선언 후
path_resolver 의 save_resource_bytes, save_resource 등
MCP_RESOURCE_ROOT 에 파일 데이터를 저장하는 함수에서 파일 저장 후
mcp.resource로 연결하기 위해 사용합니다.
"""

_ADD: Optional[Callable[..., None]] = None

def set_add_resource(fn):
    global_ADD; _ADD = fn

def add_resource(uri: str, mime_type:str, path: Path) -> None:
    if _ADD is None:
        raise RuntimeError("add_resouce() called before set_add_resource()")
    _ADD(uri, mime_type, path)

