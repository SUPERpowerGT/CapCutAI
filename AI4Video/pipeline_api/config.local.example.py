"""本地私有配置示例。

使用方式：
1. 复制本文件为 `config.local.py`
2. 将真实 token 填入副本
3. `config.local.py` 已被 gitignore 忽略，不会提交
"""

API_BASE_URL = "https://api.302.ai/v1/chat/completions"

API_KEYS = {
    "vl": "sk-your-vl-token",
    "omni": "sk-your-omni-token",
}

# 可选：按需覆盖默认模型或参数
# MODELS = {
#     "vl": "Qwen/Qwen3-VL-8B-Instruct",
#     "omni": "Qwen/Qwen3-Omni-30B-A3B-Instruct",
# }
