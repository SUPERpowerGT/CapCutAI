# HyperFrames Draft Builder

这份文档说明当前仓库里已经可用的一个最小工具：

```txt
Editor Export Package
  -> HyperFrames Composition Draft
```

它的目标不是直接渲染最终 mp4，而是把前端导出的 package 转成一个稳定的 composition 起点，供 Codex / Cursor / agent 继续往真实 HyperFrames 渲染推进。

## 入口

命令：

```bash
cd ai-service
python -m app.tools.build_hyperframes_draft \
  --package ../path/to/example.editing-package.json
```

可选：

```bash
--output-dir ./output/plans/custom.hyperframes
```

如果不传 `--output-dir`，默认使用 package 里的：

```txt
editingJob.compositionPath
```

## 输入

输入文件是前端 Editor 的导出 package：

```txt
*.editing-package.json
```

它至少需要：

- `sourceAssets`
- `sourceMaterials`
- `editingExperience`
- `timelinePlan`
- `editingJob`
- `renderResult`

## 输出

生成目录里当前包含：

- `composition.draft.json`
- `timeline-plan.json`
- `editing-job.json`
- `render-result.json`
- `index.html`
- `composition-data.js`
- `composition.js`
- `README.md`

## 现在做到了什么

当前 draft builder 会：

1. 读取导出 package
2. 从 `timelinePlan` 里找出 `video / subtitle / overlay / audio` 四类 track
3. 以 video clip 为主，把字幕、overlay、audio cue 合并到 scene 级别
4. 生成 `composition.draft.json`
5. 生成一个可以本地打开查看结构的 `index.html`

## 现在还没做到什么

当前还没有：

- 真正调用 HyperFrames render
- 真正输出最终 mp4
- 真正读取稳定的本地视频文件路径

这是因为前端导出的 `sourceAssets.objectUrl` 目前通常还是浏览器 `blob:` URL，它适合前端预览，但不适合离线渲染。

## 下一步怎么接

下一步建议：

1. 让 workspace 或 asset manager 给出稳定本地文件路径
2. 让 Codex / agent 基于 `composition.draft.json` 生成真实 HyperFrames composition
3. 再接 HyperFrames CLI 或 producer 去导出 mp4

## 相关文件

- [`../../ai-service/app/tools/build_hyperframes_draft.py`](../../ai-service/app/tools/build_hyperframes_draft.py)
- [`../../ai-service/app/services/hyperframes_service.py`](../../ai-service/app/services/hyperframes_service.py)
- [`../../shared/schemas/hyperframes-composition-draft.schema.json`](../../shared/schemas/hyperframes-composition-draft.schema.json)
- [`../agent-editing-tools/README.md`](../agent-editing-tools/README.md)
