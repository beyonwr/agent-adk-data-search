import os
import io
from typing import Any, Dict, Optional

import pandas as pd 
import google.genai.types as types 
from google.adk.tools import ToolContext


DEFAULT_LOCAL_CSV_PATH = os.getenv("ADK_LOCAL_CSV_PATH", "../temp/cast_aladin_df.csv")
DEFAULT_ARTIFACT_FILENAME = os.getenv("ADK_ARTIFACT_CSV_NAME", "dataset.csv")
STATE_DATASET = "workspace:dataset"


async def get_data(
    tool_context: ToolContext,
    local_csv_path: Optional[str] = None,
    artifact_filename: Optional[str] = Npne,
) -> Dict[str, Any]:

    """
    로컬 csv를 읽어 adk artifact로 저장하고, 데이터 요약 메타정보를 session state에 저장한다.

    - artifact: 원본 파일 (bytes)
    - state: LLM이 다음 턴에서 활용 가능한 요약(컬럼/타입/결측/샘플 등)

    Returns:
        Dict[str, Any]: status, saved_filename, version, bytes, profile_summary 포함
    """

    local_csv_path = local_csv_path or DEFAULT_LOCAL_CSV_PATH
    artifact_filename = artifact_filename or DEFAULT_ARTIFACT_FILENAME

    if not os.path.isfile(local_csv_path):
        return {
            "status": "error",
            "message": f"로컬 csv를 찾을 수 없습니다.: {local_csv_path}",
        }
    
    with open(local_csv_path, "rb") as f:
        csv_bytes = f.read()

    part = types.Part.from_bytes(data=csv_bytes, mime_type="text/csv")
    version = await tool_context.saved_artifact(filename=artifact_filename, artifact=part)

    profile: Dict[str, Any] = {
        "filename": artifact_filename,
        "version": int(version) if version is not None else None,
        "mime_type": "text/csv",
        "bytes": len(csv_bytes),
        "source_path": local_csv_path,
    }

    try:
        sample_df = pd.read_csv(io.BytesIO(csv_bytes), nrows=2000)

        profile["shape_sampled"] = {"rows": int(sample_df.shape[0]), "cols": int(sample_df.shape[1])}
        profile["columns"] = list(sample_df.columns)
        profile["dtypes"] = {c: str(sample_df[c].dtype) for c in sample_df.columns}

        na_ratio = (sample_df.isna().mean()).sort_values(ascending=False)
        top_missing  = [
            {"column": str(col), "missing_ratio": float(r)}
            for col, r in na_ratio.head(10).items()
            if float(r) > 0.0
        ]

        profile["top_missing_columns"] = top_missing

        # 수치형 컬럼 기초 통계(상위 일부)
        num_cols = sample_df.select_dtypes(include="number").columns.tolist()
        if num_cols:
            desc = sample_df[num_cols].describe().to_dict()
            # desc는 {stat: {col:value}} 형태라 LLM이 읽기 어려움으로 컬럼 중심으로 재구성
            numeric_summary = {}
            for col in num_cols[:20]:
                numeric_summary[col] = {
                    "count": float(desc.get("count", {}).get(col, 0.0)),
                    "mean": float(desc.get("mean", {}).get(col, 0.0)),
                    "std": float(desc.get("std", {}).get(col, 0.0)),
                    "min": float(desc.get("min", {}).get(col, 0.0)),
                    "max": float(desc.get("max", {}).get(col, 0.0)),
                }
            profile["numeric_summary"] = numeric_summary

        profile["sample_rows"] = sample_df.head(10).to_dict(orient="records")

    except Exception as e:
        profile["profile_error"] = f"{type(e).__name__}: {e}"

    # prefix 없으면 session.state에 저장
    state_index = tool_context.state.get(STATE_DATASET, {})
    if not isinstance(state_index, dict):
        state_index = {}

    state_index[artifact_filename] = profile
    tool_context.state[STATE_DATASET] = state_index

    return {
        "status": "success",
        "saved_filename": artifact_filename,
        "version": version,
        "bytes": len(csv_bytes),
        "profile_summary": {
            "columns": profile.get("columns", []),
            "dtypes": profile.get("dtypes", {}),
            "top_missing_columns": profile.get("top_missing_columns", []),
            "sample_rows": profile.get("sample_rows", []),            
        },
        "state_key": STATE_DATASET,
    }
