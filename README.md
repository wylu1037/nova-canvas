# NovaCanvas

基于 SenseNova U1.5 Lite / Fast 的图片生成与编辑工具，提供 **PySide6 桌面端** 与 **FastAPI 后端** 两种入口，共用同一套服务层。

## 架构

```
桌面端 (PySide6)                          后端 (FastAPI)
desktop/ui/*  →  desktop/controller.py    handlers/*  →  core/dependencies.py
     (Signal/Slot)   ↓ QThreadPool/ApiTask                   ↓ Depends
                 services/ (ImageService · HistoryService)
                          ↓
      repositories/ (历史 JSON · 本地图片落盘)   clients/sensenova.py (鉴权、退避重试、脱敏)
```

- `core/`：配置（pydantic-settings）、日志、异常与全局异常处理、依赖注入
- `middleware/`：Request-ID、访问日志
- `schemas/`：pydantic 请求/响应模型与参数校验（尺寸、Data URL 等）
- `handlers/`：HTTP 路由，仅做协议转换
- `services/`：业务逻辑
- `repositories/`：抽象仓储接口 + JSON 文件实现
- `clients/`：SenseNova HTTP 客户端
- `desktop/`：桌面端 — `config.py`（QSettings + 环境变量）、`workers.py`（QRunnable）、`controller.py`、`ui/`（主窗口、双 Tab、参数面板、画布、拖拽上传、历史、设置）

## 运行

```bash
uv sync --all-groups
```

**桌面端**（推荐）：

```bash
uv run nova-canvas-desktop
```

首次启动会引导打开设置对话框填写 API Key；也可预先 `export SENSENOVA_API_KEY=sk-...`（环境变量优先级最高）。密钥可选"仅本次会话"或"持久化"（明文写入 QSettings，界面会提示风险）。

**后端服务**：

```bash
cp .env.example .env   # 填入 SENSENOVA_API_KEY
uv run nova-canvas     # http://127.0.0.1:8000/docs
```

## 测试

```bash
uv run pytest
```
