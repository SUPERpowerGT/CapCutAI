# Scripts

这里放的是 **仓库级辅助脚本**。

它们的定位不是某个单独服务内部代码，而是：

- 本地联调辅助
- 脚手架验证
- 仓库级 smoke test
- 启动后快速自检

所以 `scripts/` 放在仓库根目录，而不是放进 `backend/`、`frontend/` 或 `ai-service/` 里面。

## 当前脚本

### `smoke_test_im_agent.py`

文件：

- [`smoke_test_im_agent.py`](./smoke_test_im_agent.py)

用途：

- 检查 backend health
- 创建一条 conversation
- 发送一条 message
- 触发 agent reply
- 读取 message 列表

也就是说，它验证的是当前这条最小主链：

```txt
backend -> ai-service -> postgres
```

### `render_editor_sample.sh`

文件：

- [`render_editor_sample.sh`](./render_editor_sample.sh)

用途：

- 从 `data/test_case` 读取 mock analyzer 数据
- 生成 `editing-package.json`
- 调用本机 ffmpeg native render
- 输出一版可直接检查的 MP4

也就是说，它验证的是当前剪辑工具链的最小闭环：

```txt
data/test_case -> editing-package -> native render -> mp4
```

默认输出：

```txt
ai-service/output/plans/editor-sample.editing-package.json
ai-service/output/renders/editor-sample.native.final.mp4
```

默认 profile 是：

```txt
smoke
```

常用方式：

```bash
scripts/render_editor_sample.sh
PROFILE=smoke scripts/render_editor_sample.sh
PROFILE=1080p scripts/render_editor_sample.sh
```

如果要额外生成 HyperFrames bundle：

```bash
BUILD_HYPERFRAMES=1 scripts/render_editor_sample.sh
```

如果要继续尝试 HyperFrames render：

```bash
RENDER_HYPERFRAMES=1 PROFILE=1080p scripts/render_editor_sample.sh
```

说明：

- 默认不依赖 Docker
- 默认走本机 ffmpeg
- HyperFrames render 需要 Node.js 22+ 和 Google Chrome
- Docker 仍用于 `make up` 的本地服务链

## 如何使用

推荐在项目根目录执行：

```bash
make smoke
```

等价于：

```bash
python3 scripts/smoke_test_im_agent.py
```

剪辑工具链 smoke：

```bash
scripts/render_editor_sample.sh
```

## 规则

后续如果继续往这里加脚本，遵循这几个原则：

- 只放仓库级脚本
- 不放某个服务内部私有逻辑
- 不把业务实现写进这里
- 优先做“验证、诊断、辅助”用途

如果某个脚本只服务于一个具体模块，应优先放回对应模块内部，而不是继续堆在 `scripts/`。
