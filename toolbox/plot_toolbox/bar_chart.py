import uuid
import pandas as pd 
import numpy as np
import plotly.io as pio 
import plotly.graph_objects as go 
from typing import Dict, Any, List

from ..utils.path_resolver import resolve_artifact_path, save_resource_bytes, save_resource

def _generate_bar_plot_description(fig: go.Figure) -> str:

    if not fig.data or fig.data[0].type != "bar":
        return "이 그래프는 바 차트가 아니거나 데이터가 비어 있습니다."

    trace = fig.data[0]

    labels = list(trace.x)
    values = np.array(trace.y, dtype=float)

    title = fig.layout.title.text or "제목 없음"
    x_title = fig.layout.xaxis.title.text or "카테고리"
    y_title = fig.layout.yaxis.title.text or "값"

    # 통계 요약
    max_idx = int(values.argmax())
    min_idx = int(values.argmin())

    max_label = labels[max_idx]
    max_value = values[max_idx]

    min_label = labels[min_idx]
    min_value = values[min_idx]

    description = (
        f"**{title}** 바 차트 | x:{x_title}({len(labels)}), Y:{y_title} | "
        f"max {max_label} {max_value: .2f}, min {min_label} {min_value: .2f}, "
        f"range {values.min(): .2f}"
    )

    return description

def bar_chart(
    labels: List[str],
    values: List[float],
    title: str = "bar chart",
    label_name: str = "Category",
    value_name: str = "Value",
    top_k: int = 30
) -> Dict[str, Any]:
    """
    바 차트를 생성하고 Base64로 인코딩된 HTML을 반환합니다.

    Args:
        labels: X축에 표시할 항목명 리스트 (예: ['Feature A', 'Feature B']),
        values: Y축에 표시할 수치 데이터 리스트 (예: [0.05, 0.42]), labels 와 깊이가 같아야합니다.
        title: 그래프의 제목 및 반환될 파일명에 사용됩니다.
        label_name: X축 하단에 표시할 라벨명
        value_name: Y축 좌측에 표시할 라벨명
        top_k: 수치가 높은 상위 K개의 항목만 추출하여 표시
    """
    if not labels or not values or len(labels) != len(values):
        return {
            "status": "error",
            "outputs": [
                {
                    "type": "INVALID_INPUT",
                    "message": "labels 와 values 의 개수가 일치해야 하며 비어있을 수 없습니다."
                }
            ]
        }

    df = pd.DataFrame({
        "label": labels,
        "value": values
    })
    view_df = df.sort_values("value", ascending=False).head(int(top_k))
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=view_df["label"],
        y=view_df["value"],
        name=value_name
    ))
    fig.update_layout(
        title=title,
        xaxis_title=label_name,
        yaxis_title=value_name,
        template="plotly_white"
    )
    fig.update_xaxes(tickangle=45)

    job_id = uuid.uuid4().hex
    graph_json = pio.to_json(fig)
    json_url, json_filename, json_mime_type = save_resource(graph_json, job_id, "json")
    png_bytes = fig.to_image(format="png", width=800, height=400, scale=1)
    png_url, png_filename, png_mime_type = save_resource_bytes(png_bytes, job_id, "png")
    description = _generate_bar_plot_description(fig)

    return {
        "status": "success",
        "outputs": [
            {
                "type": "resource_link",
                "uri": json_url,
                "filename": json_filename,
                "mime_type": json_mime_type,
                "description": description,
            },
            {
                "type": "resource_link",
                "uri": png_url,
                "filename": png_filename,
                "mime_type": png_mime_type,
                "description": f"PNG 프리뷰"
            }
        ]
    }

