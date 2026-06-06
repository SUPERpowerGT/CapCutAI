"""Qwen 视频/音频理解能力测试框架。"""

from framework.base import BaseTester, TaskResult
from framework.tasks import VLM_TASKS, VLM_EDITING_TASKS, ASR_TASKS

__all__ = ["BaseTester", "TaskResult", "VLM_TASKS", "VLM_EDITING_TASKS", "ASR_TASKS"]
