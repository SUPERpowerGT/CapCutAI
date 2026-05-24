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

## 如何使用

推荐在项目根目录执行：

```bash
make smoke
```

等价于：

```bash
python3 scripts/smoke_test_im_agent.py
```

## 规则

后续如果继续往这里加脚本，遵循这几个原则：

- 只放仓库级脚本
- 不放某个服务内部私有逻辑
- 不把业务实现写进这里
- 优先做“验证、诊断、辅助”用途

如果某个脚本只服务于一个具体模块，应优先放回对应模块内部，而不是继续堆在 `scripts/`。
