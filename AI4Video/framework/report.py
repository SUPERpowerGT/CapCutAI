"""Markdown 报告生成器: 把多模型 × 多任务的推理结果整理成对比文档。

报告结构:
    # 标题
    ## 实验设置
    ## 任务 1
        ### 模型 A 输出 + 截图表
        ### 模型 B 输出 + 截图表
        ...
    ## 整体观察
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ModelTaskRun:
    """单个 (模型, 任务) 的完整结果, 含原文与每条时间戳的截图路径。"""

    model_name: str
    task_name: str
    prompt: str
    answer: str
    latency_sec: float
    extra: dict[str, Any]
    # 每条 timestamp 的展开: (描述行, 时间戳秒, 截图相对路径)
    timestamp_rows: list[tuple[str, float, str]]


def _frame_table(rows: list[tuple[str, float, str]], cols: int = 3) -> str:
    """把多条截图组织成 N 列 markdown 表格。"""
    if not rows:
        return "_(模型未输出可解析的时间戳)_"

    parts: list[str] = []
    # 表头
    parts.append("| " + " | ".join([f"截图 {i+1}" for i in range(cols)]) + " |")
    parts.append("|" + "|".join([" --- "] * cols) + "|")

    # 图像行
    for r0 in range(0, len(rows), cols):
        chunk = rows[r0 : r0 + cols]
        cells = []
        for _, t, rel in chunk:
            cells.append(f"![{t:.2f}s]({rel})<br>**{t:.2f}s**")
        while len(cells) < cols:
            cells.append("")
        parts.append("| " + " | ".join(cells) + " |")

    # 说明行
    parts.append("")
    parts.append("**对应描述:**")
    for _, t, _rel in rows:
        pass  # 单独列表展示更清晰
    for desc, t, _rel in rows:
        parts.append(f"- `{t:.2f}s`: {desc}")
    return "\n".join(parts)


def build_report(
    title: str,
    video_path: str | Path,
    video_duration_sec: float | None,
    task_titles: dict[str, str],  # task_name -> 中文展示标题
    runs: list[ModelTaskRun],
    output_md_path: str | Path,
    extra_notes: str | None = None,
) -> Path:
    """生成 markdown 文档并落盘。"""
    output_md_path = Path(output_md_path)
    md_dir = output_md_path.parent
    md_dir.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## 实验设置")
    lines.append(f"- 视频文件: `{video_path}`")
    if video_duration_sec is not None:
        lines.append(f"- 视频时长: {video_duration_sec:.2f}s")
    lines.append("")

    # 模型清单
    models = sorted({r.model_name for r in runs}, key=lambda x: x)
    lines.append("- 参与模型: " + ", ".join(f"`{m}`" for m in models))
    lines.append("")
    if extra_notes:
        lines.append(extra_notes)
        lines.append("")

    # 按任务分组
    by_task: dict[str, list[ModelTaskRun]] = {}
    for r in runs:
        by_task.setdefault(r.task_name, []).append(r)

    for task_name, task_runs in by_task.items():
        display = task_titles.get(task_name, task_name)
        lines.append(f"## 任务: {display}  (`{task_name}`)")
        lines.append("")
        if task_runs:
            lines.append(f"**Prompt:**\n\n> {task_runs[0].prompt.strip()}")
            lines.append("")

        for run in task_runs:
            lines.append(f"### 模型: `{run.model_name}`")
            lines.append(f"- 推理耗时: {run.latency_sec:.2f}s")
            if run.extra:
                meta = ", ".join(f"{k}={v}" for k, v in run.extra.items() if v is not None)
                if meta:
                    lines.append(f"- 元数据: {meta}")
            lines.append("")
            lines.append("**模型输出:**")
            lines.append("")
            lines.append("```")
            lines.append(run.answer.strip())
            lines.append("```")
            lines.append("")
            lines.append("**时间戳截图:**")
            lines.append("")
            lines.append(_frame_table(run.timestamp_rows))
            lines.append("")
            lines.append("---")
            lines.append("")

    output_md_path.write_text("\n".join(lines), encoding="utf-8")
    return output_md_path.resolve()
