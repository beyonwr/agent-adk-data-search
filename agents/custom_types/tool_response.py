import json
from typing import Literal

from google.genai.types import Content
from mcp.types import CallToolResult, TextContent
from pydantic import BaseModel


class ToolResponseData(BaseModel):
    type: Literal["image", "markdown_table", "csv_table", "excel_table"]
    content: str | list[str] | list[dict] | dict

    def to_json(self) -> list[dict] | dict:
        return self.model_dump(mode="python", exclude_none=True)

class ToolResponse(BaseModel):
    """
    Project 내에서 사용할 Tool의 return class를 정의합니다.
    message 항목은 tool 실행의 결과물 또는 data 결과물에 대한 간단한 설명을 작성합니다.
    data에는 record 형태 (dict로 이루어진 list) 또는 dict 또는 None만을 허용합니다.
    """

    status: Literal["success", "error"]
    message: str
    data: list[dict] | dict | ToolResponseData = None

    def to_json(self) -> list[dict] | dict:
        return self.model_dump(mode="python", exclude_none=True)

    def to_mcp_result(self) -> CallToolResult:
        contents = Content(parts=[TextContent(type="text", text=self.message)])
        contents.parts.append(TextContent(type="text", text=json.dumps(self.data, ensure_ascii=False)))
        return CallToolResult(
            content=contents,
            isError=True if self.status == "error" else False,
            structured_content=self.data,
        )

