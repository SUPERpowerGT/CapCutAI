# MVP Video Pipeline

这份文档只回答一件事：

```txt
CapCutAI 的视频 MVP 当前到底要闭环哪些执行链，按什么顺序推进，当前明确不做什么？
```

它不是 use case 文档。

也就是说：

- 用户目标、输入输出价值优先看 use case 层
- 这里更关心当前版本的执行范围、阶段顺序和落地闭环

如果你要先看上层 why，先看：

- [`../../02-use-cases/01-workspace-agent-use-cases/README.md`](../../02-use-cases/01-workspace-agent-use-cases/README.md)

当前 MVP 的主线不是聊天，而是：

```txt
参考视频分析
+ 用户视频自动套风格
+ IM 对话式修订
```

而且这三条主链默认都应建立在：

```txt
Local-first Agent Runtime
+ Local Tool Runtime
+ Local Workspace Artifacts
```

---

## 1. MVP Chains

当前 MVP 只围绕 3 条执行链组织：

### 1. 参考视频分析链

目的：

- 生成可复用的参考风格资产

当前闭环产物：

- `materials.json`
- `style_profile.json`
- `editing_rules.json`

### 2. 用户视频自动套风格链

目的：

- 把参考风格资产应用到用户本地素材

当前闭环产物：

- `timeline_plan.json`
- `editing_job.json`
- `final.mp4`

### 3. IM 对话式修订链

目的：

- 在已有结果之上继续 patch plan 和 rerender

当前闭环产物：

- 新版 `timeline_plan.json`
- 新版 `editing_job.json`
- 新版 `final.mp4`

---

## 2. Execution Order

当前最重要的执行判断不是“先分析还是先剪”，而是：

```txt
参考视频分析链
和
用户视频剪辑链
需要同步收敛
```

原因仍然成立：

- 只分析爆款，不知道输出结构够不够后面剪
- 只做剪辑，不知道前面到底该沉淀什么风格资产

所以当前真正要同步收敛的是两类 contract：

- `Style Analysis Output Schema`
- `User Editing Input Schema`

而 revision 链当前依赖前两条链先产生稳定 artifacts，所以顺序上是：

```txt
P0
  reference analysis
  + source editing

P1
  revision on existing output
```

---

## 3. MVP Phase 1

当前第一阶段只支持：

```txt
One Last Kiss
```

这是刻意收窄，不是长期限制。

最小闭环：

1. 用户导入视频到当前 workspace
2. 系统完成 reference analysis
3. 系统拿到 `style_profile`
4. 系统分析 source videos
5. 系统生成 `timeline_plan.json`
6. 系统生成 `editing_job.json`
7. 本地 render 输出 `final.mp4`

如果第一阶段跑不通，就说明当前 MVP 还没有真正闭环。

---

## 4. Current Directory Landing

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

---

## 5. Data Boundary For MVP

P0 推荐默认策略：

- 原始视频不出本地 workspace
- 本地先做抽帧、镜头切分、音频特征提取、可选 ASR
- 模型优先消费结构化摘要、metadata、少量抽样帧
- 最终 `final.mp4` 生成并保存在本地

---

## 6. In Scope / Out Of Scope

### In Scope

- 单一固定风格闭环
- reference analysis artifacts
- source editing artifacts
- 本地 render 成片
- 基于已有 artifacts 的 revision 起点

### Out Of Scope For Now

- 多风格自由切换
- 通用风格 marketplace
- 云端主渲染链
- 复杂协同编辑
- 高级偏好学习和长期 personalization

---

## 7. Related Docs

- 上层 use cases：[`../../02-use-cases/01-workspace-agent-use-cases/README.md`](../../02-use-cases/01-workspace-agent-use-cases/README.md)
- 总体架构：[`../../03-architecture/03-system-architecture/README.md`](../../03-architecture/03-system-architecture/README.md)
- 风格分析：[`../05-style-analysis-design/README.md`](../05-style-analysis-design/README.md)
- 风格套用：[`../06-style-editing-design/README.md`](../06-style-editing-design/README.md)
- ai-service 架构：[`../01-ai-service-video-architecture/README.md`](../01-ai-service-video-architecture/README.md)
