from typing import Dict, Any, List, Literal, Tuple, Optional
from pydantic import BaseModel, Field
from abc import ABC

class BaseArtifact(BaseModel, ABC):
    """
    기본 상태 클래스 - 모든 artifact의 공통 속성 및 메서드 제공
    """
    type: str
    filename: str
    mime_type: str
    function_call_id: str
    user_query: str

    def to_json(self) -> Dict[str, Any]:
        return self.model_dump(mode='json', exclude_none=True)

    @classmethod
    def from_json(cls, data: Dict[str, Any]):
        return cls(**data)

class ImgArtifact(BaseArtifact):
    """
    이미지 artifact 상태 클래스
    """
    type: Literal["img"] = "img"
    img_size: Optional[Tuple[int, int]] = None

class TabularArtifact(BaseArtifact):
    """
    테이블 artifact 상태 클래스
    """
    type: Literal["table"] = "table"
    sql_query: Optional[str] = None
    data_length: Optional[int] = None

class AppState(BaseModel):
    """
    애플리케이션 상태 관리 클래스
    """
    artifacts: List[BaseArtifact] = Field(default_factory=list)

    def to_json(self) -> Dict[str, Any]:
        return {
            'artifacts': [artifacts.to_json() for artifact in self.artifacts]
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]):
        artifacts_data = data.get('artifacts', [])
        artifacts = []
        for artifact_data in artifacts_data:
            artifact_type = artifact_data.get('type')
            if artifact_type == 'img':
                artifacts.append(ImgArtifact.from_json(artifact_data))
            elif artifact_type == 'table':
                artifacts.append(TableArtifact.from_json(artifact_data))
            else:
                artifacts.append(BaseArtifact.from_json(artifact_data))
        return cls(artifacts=artifacts)

