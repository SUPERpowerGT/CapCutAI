# MVP Video Pipeline

这份文档定义 CapCutAI 当前视频能力的主线。

核心目标不是聊天，而是：

```txt
参考视频分析
+ 用户视频自动套风格
+ IM 对话式修订
```

## 三条主链

### 1. 参考视频分析链

输入：

- 参考视频

输出：

- `materials.json`
- `style_profile.json`
- `editing_rules.json`

作用：

- 把爆款视频经验沉淀成结构化风格资产

### 2. 用户视频自动套风格链

输入：

- 用户视频
- `style_profile`
- 用户指令

输出：

- `timeline_plan.json`
- `editing_job.json`
- `final.mp4`

作用：

- 把结构化风格规则应用到用户视频

### 3. IM 对话式修订链

输入：

- 当前 conversation
- 当前 timeline / output
- 用户修订指令

输出：

- 新版 timeline
- 新版 `editing_job`
- 新版 `final.mp4`

作用：

- 让右侧 `Agent Panel` 变成视频修订控制台

## 当前最重要的判断

现在不能只做其中一边。

更合理的是：

```txt
参考视频分析链
和
用户视频剪辑链
同步推进
```

原因：

- 只分析爆款，不知道输出结构够不够后面剪
- 只做剪辑，不知道前面到底该沉淀什么风格资产

所以当前真正要同步收敛的是：

- `Style Analysis Output Schema`
- `User Editing Input Schema`

## MVP 第一阶段

第一版只支持：

```txt
One Last Kiss
```

最小闭环：

1. 用户上传视频
2. 用户输入：
   - `帮我做成 One Last Kiss 风格`
3. Material Analyzer
4. Style Retriever
5. Director Planner
6. Editing Skills
7. 输出 `final.mp4`

## 当前目录落点

- 参考视频：
  - `ai-service/input/stylizationvideo/`
- 用户视频：
  - `ai-service/input/uservideo/`
- 分析产物：
  - `ai-service/output/materials/`
- 规划产物：
  - `ai-service/output/plans/`
- 最终视频：
  - `ai-service/output/renders/`

## 下一步看哪里

- 风格分析：[`../style-analysis-design/README.md`](../style-analysis-design/README.md)
- 风格套用：[`../style-editing-design/README.md`](../style-editing-design/README.md)
- ai-service 架构：[`../ai-service-video-architecture/README.md`](../ai-service-video-architecture/README.md)
