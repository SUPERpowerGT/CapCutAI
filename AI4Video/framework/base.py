"""测试框架基类。

所有具体的 Tester (VLM / ASR / Audio-LLM) 都继承 BaseTester,
对外暴露统一的 load / run_task / run_tasks 接口, 便于后续扩展新模型时
只需实现 _load_model 与 _infer 即可。
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TaskResult:
    """单次推理结果。"""

    task_name: str
    prompt: str
    answer: str
    latency_sec: float
    extra: dict[str, Any] = field(default_factory=dict)


class BaseTester(ABC):
    """所有模型 Tester 的抽象基类。

    子类需实现:
        _load_model(): 加载权重并准备好 self._ready 状态。
        _infer(media, prompt, **kwargs) -> (answer, extra): 单次推理。
    """

    def __init__(self, model_path: str, name: str | None = None):
        self.model_path = model_path
        self.name = name or Path(model_path).name
        self._loaded = False

    # ------- 子类必须实现 -------
    @abstractmethod
    def _load_model(self) -> None: ...

    @abstractmethod
    def _infer(self, media: str, prompt: str, **kwargs: Any) -> tuple[str, dict[str, Any]]: ...

    # ------- 通用流程 -------
    def load(self) -> None:
        if self._loaded:
            return
        print(f"[{self.name}] loading from {self.model_path} ...")
        t0 = time.time()
        self._load_model()
        self._loaded = True
        print(f"[{self.name}] loaded in {time.time() - t0:.1f}s")

    def run_task(self, media: str, task_name: str, prompt: str, **kwargs: Any) -> TaskResult:
        self.load()
        print(f"\n---------- [{self.name}] {task_name} ----------")
        print(f"[Prompt] {prompt}")
        t0 = time.time()
        answer, extra = self._infer(media, prompt, **kwargs)
        latency = time.time() - t0
        print(f"[Latency] {latency:.1f}s")
        print(f"[Answer]\n{answer}")
        return TaskResult(task_name=task_name, prompt=prompt, answer=answer,
                          latency_sec=latency, extra=extra)

    def run_tasks(self, media: str, tasks: dict[str, str], **kwargs: Any) -> list[TaskResult]:
        return [self.run_task(media, name, prompt, **kwargs) for name, prompt in tasks.items()]

    # ------- 结果持久化 -------
    @staticmethod
    def save_results(results: list[TaskResult], output_path: str | Path) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(r) for r in results]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[Saved] {len(results)} results -> {path}")
