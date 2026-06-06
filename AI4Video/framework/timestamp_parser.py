"""从模型输出文本中解析时间戳, 转化为可用于截帧的秒数。

支持的格式 (按行解析, 每行一个事件):
    [0.0-2.5] | 描述
    [0.0-2.5秒] 描述
    0.0 - 2.5  描述
    [1.25s] 描述
    [1.25] 描述

返回 dataclass 列表, 每条带:
    line: 原始行
    start_sec / end_sec: 起止秒 (若是单点, 二者相等)
    midpoint_sec: 区间中点 (用于截帧的代表帧位置)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# 时间戳数字可带或不带小数; 也兼容 s / 秒 后缀
_NUM = r"(\d+(?:\.\d+)?)"
# MM:SS 或 HH:MM:SS (整数分秒)
_HMS = r"(?:(\d{1,2}):)?(\d{1,2}):(\d{2})"

# 匹配区间: 形如 [0.0-2.5], (0.0-2.5), 0.0-2.5, 0.0–2.5, 0.0~2.5
_RANGE_PATTERNS = [
    re.compile(rf"\[\s*{_NUM}\s*[-–~]\s*{_NUM}\s*(?:s|秒)?\s*\]"),
    re.compile(rf"(?<![.\d]){_NUM}\s*[-–~]\s*{_NUM}\s*(?:s|秒)"),
    # 行首出现 a-b 即视为时间戳 (Qwen2.5-VL 常见格式: "0.0 - 2.8 描述")
    re.compile(rf"^\s*\[?\s*{_NUM}\s*[-–~]\s*{_NUM}\s*\]?\b"),
]

# 单点时间戳: [1.25], [1.25s], [1.25秒], 以及 MM:SS / HH:MM:SS
_POINT_PATTERNS = [
    re.compile(rf"\[\s*{_NUM}\s*(?:s|秒)?\s*\]"),
    re.compile(rf"^\s*\[?\s*{_NUM}\s*(?:s|秒)\s*\]?\s*[|,，:、]"),
]
# MM:SS 单独成行 (Omni 偶尔输出 "00:42 | 硬切 | ...")
_HMS_PATTERN = re.compile(rf"^\s*\[?\s*{_HMS}\s*\]?\s*[|,，、]")


@dataclass
class Timestamp:
    line: str
    start_sec: float
    end_sec: float

    @property
    def midpoint_sec(self) -> float:
        return (self.start_sec + self.end_sec) / 2.0

    @property
    def is_point(self) -> bool:
        return self.start_sec == self.end_sec


def _try_range(line: str) -> tuple[float, float] | None:
    for pat in _RANGE_PATTERNS:
        m = pat.search(line)
        if m:
            return float(m.group(1)), float(m.group(2))
    return None


def _try_point(line: str) -> float | None:
    m = _HMS_PATTERN.match(line)
    if m:
        h = int(m.group(1)) if m.group(1) else 0
        return h * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    for pat in _POINT_PATTERNS:
        m = pat.search(line)
        if m:
            return float(m.group(1))
    return None


def parse_timestamps(text: str) -> list[Timestamp]:
    """从一段多行文本中按行抽取时间戳。

    每行至多产出 1 条 (优先匹配区间, 区间失败再试单点)。
    无时间戳的行被跳过。
    """
    results: list[Timestamp] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        rng = _try_range(line)
        if rng is not None:
            start, end = rng
            if end < start:
                start, end = end, start
            results.append(Timestamp(line=line, start_sec=start, end_sec=end))
            continue
        pt = _try_point(line)
        if pt is not None:
            results.append(Timestamp(line=line, start_sec=pt, end_sec=pt))
    return results
