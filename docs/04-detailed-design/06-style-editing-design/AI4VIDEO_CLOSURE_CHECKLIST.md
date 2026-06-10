# AI4Video Closure Checklist

这份清单记录当前 `AI4Video -> 新视频成片` 闭环的完成项和下一步。

## 当前闭环状态

当前最小链路已经跑通：

```txt
参考视频
  -> AI4Video 分析
  -> elastic_template.json

source 素材
  -> AI4Video 分析
  -> sourceMaterials

elastic_template.json + sourceMaterials
  -> planner
  -> editing-package.json
  -> native render
  -> final.mp4
```

## 已完成

### 1. 参考视频经验提取

- [x] 支持 API 版 AI4Video。
- [x] 支持 VL token 和 Omni token 的本地私有配置。
- [x] 产出 `step1_audio.json`、`step2_transcript.json`、`step3_visual.json`。
- [x] 产出核心经验文件 `elastic_template.json`。
- [x] 参考分析固定落盘到 workspace：

```txt
assets/intermediate/
assets/template/elastic_template.json
```

### 2. source 素材分析

- [x] 支持最多 10 个 source 视频。
- [x] 每个 source 可通过 AI4Video 生成音频、转写、视觉和模板文件。
- [x] source 分析缓存落到：

```txt
ai-service/output/im-runs/<workspaceId>/<conversationId_timestamp>/analysis/
```

### 3. Planner

- [x] 支持 configured LLM planner。
- [x] 当前可使用 `ai4video_vl` provider。
- [x] LLM planner 失败时可 fallback 到 rule-based planner。
- [x] 输出 `timeline_plan.json`。

### 4. Package builder

- [x] 支持 `AI4Video outputs + source videos + experience` 构建 `editing-package.json`。
- [x] 支持外部 `timeline_plan.json`。
- [x] 修复 Docker 环境下 `ffprobe` 路径硬编码问题。

### 5. Renderer

- [x] native ffmpeg render 可输出 MP4。
- [x] 支持 source audio 或 reference audio override。
- [x] 支持 burn subtitles。
- [x] 最终成片固定落盘到 workspace：

```txt
artifacts/renders/*.native.final.mp4
artifacts/renders/*.native.final.render-result.json
```

### 6. IM 编排

- [x] 支持“分析爆款/参考视频”意图。
- [x] 支持“剪辑/制作/生成 demo”意图。
- [x] 重任务执行前先确认。
- [x] 已有 `elastic_template.json` 时，默认复用经验剪 source，不重复分析参考视频。
- [x] 明确说“重新分析 / 重跑分析 / 再分析一次”时才重跑参考分析。
- [x] 运行时锁定 reference/source 上传和删除操作。
- [x] 错误回复做摘要，不把底层 traceback 原样打进 IM。

## 当前还需要增强

### A. Planner 质量

当前重点不是“能不能出片”，而是“出片是否足够像参考风格”。

建议增强：

- [ ] 使用 `storyline_structure` 做 phase-aware 片段分配。
- [ ] 使用参考视频 pacing/drops 控制 source 片段长度。
- [ ] 使用 `editing_utility` 选择 hook / highlight / transition 片段。
- [ ] 让字幕文案更像参考风格，而不是只复用 source 转写。
- [ ] 给 planner 输出加自检，避免过长、过短或过度平铺。

### B. 进度系统

当前前端有动态状态，但还可以细化：

- [ ] source 分析进度：第几个 source / 哪个步骤。
- [ ] planner 进度：LLM planner 或 fallback。
- [ ] package 进度。
- [ ] render 进度。

### C. Workspace 资产登记

当前最终 MP4 已落 workspace，但还需要产品化：

- [ ] 把 final MP4 登记成 workspace asset。
- [ ] 支持成片历史列表。
- [ ] 支持打开文件、复制路径、替换 preview。
- [ ] 支持重新渲染同一个 package。

### D. Render 质量

- [ ] 更好处理横竖屏混剪。
- [ ] 提供目标比例参数。
- [ ] 更细致的字幕样式映射。
- [ ] 后续评估 HyperFrames 用于复杂 overlay / 动效。

## 环境检查

服务健康：

```bash
docker compose exec ai-service /bin/sh -lc 'python - <<PY
from urllib.request import urlopen
print(urlopen("http://127.0.0.1:8000/internal/health", timeout=5).read().decode())
PY'
```

AI4Video token：

```txt
AI4Video/pipeline_api/config.local.py
```

必须包含：

```python
API_KEYS = {
    "vl": "...",
    "omni": "...",
}
```

渲染工具：

```bash
docker compose exec ai-service /bin/sh -lc 'ffmpeg -version && ffprobe -version'
```

## 推荐验收用例

1. 上传一个参考视频到 reference。
2. 上传 1 到 10 个 source 视频。
3. IM 输入“帮我分析这个爆款视频”。
4. 确认后等待 `assets/template/elastic_template.json` 生成。
5. IM 输入“帮我剪辑视频吧”。
6. 确认后等待 `artifacts/renders/*.native.final.mp4` 生成。

验收标准：

- 不重复分析已有参考经验。
- 最终 MP4 不落在 `ai-service/output/im-runs` 作为交付路径。
- IM 回复不伪造完成状态，必须以真实文件产物为准。
