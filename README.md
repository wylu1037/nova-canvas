<div align="center">

# 🎨 NovaCanvas

**基于 SenseNova U1.5 的图片生成与编辑工作台**

桌面端 (PySide6) 与 REST 服务 (FastAPI) 双入口，共用一套服务层

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-Qt%206-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![uv](https://img.shields.io/badge/uv-managed-DE5FE9?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)
[![Tests](https://img.shields.io/badge/tests-26%20passed-brightgreen)](#-测试)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[功能特性](#-功能特性) · [快速开始](#-快速开始) · [技术栈](#-技术栈) · [架构](#-架构) · [API](#-rest-api) · [打包](#-打包) · [开发](#-开发)

</div>

---

## ✨ 功能特性

| | 功能 | 说明 |
|---|---|---|
| 🖼️ | **文生图** | 输入提示词生成 2K / 4K 图片，6 种推荐分辨率预设 + 自定义尺寸实时校验 |
| ✏️ | **图片编辑** | 1 张主图 + 最多 4 张参考图，拖拽 / 本地文件 / 公网 URL 均可 |
| 🔁 | **生成 → 编辑闭环** | 一键把结果送入编辑页作主图，持续迭代 |
| 🗂️ | **历史记录** | 卡片式浏览，结果**立即落盘**，不依赖上游 24h 临时链接 |
| ⚡ | **模型切换** | `u1.5-lite`（画质优先）/ `u1.5-fast`（速度优先）一键切换 |
| 🛡️ | **稳健的云端调用** | 429 / 5xx 指数退避重试、错误信息脱敏、显式传参防上游默认值漂移 |
| 🔐 | **密钥安全** | 环境变量 > 会话内存 > 持久化三级优先级，持久化前明确提示明文风险 |
| 🌐 | **REST 服务** | 同一套能力以 HTTP API 暴露，自带 Swagger 文档 |

## 🚀 快速开始

### 环境要求

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/)（`brew install uv` / `pip install uv`）
- 一个 [SenseNova](https://www.sensenova.cn/) API Key

### 安装

```bash
git clone <repo-url> nova-canvas
cd nova-canvas
make install          # 等价于 uv sync --all-groups
```

### 🖥️ 启动桌面端

```bash
make desktop
```

首次启动会自动弹出设置对话框，填入 API Key 即可。也可以预先通过环境变量注入（优先级最高，界面中不可修改）：

```bash
export SENSENOVA_API_KEY=sk-xxxx
make desktop
```

### 🌐 启动 REST 服务

```bash
make env              # 生成 .env，填入 SENSENOVA_API_KEY
make dev              # 热重载，默认 http://127.0.0.1:8000
```

打开 <http://127.0.0.1:8000/docs> 即可在 Swagger UI 中直接调用。

## 🧰 技术栈

| 领域 | 选型 | 用途 |
|---|---|---|
| 语言 | **Python 3.11+** | 类型注解、`StrEnum`、`match` 等现代特性 |
| 包管理 | **uv** | 依赖解析、虚拟环境、脚本入口 |
| 桌面 GUI | **PySide6 (Qt 6)** | 跨平台原生控件，`QThreadPool` 后台任务 |
| Web 框架 | **FastAPI** + **Uvicorn** | 异步路由、依赖注入、OpenAPI 文档 |
| HTTP 客户端 | **httpx** | 异步请求，细粒度超时（connect / read / write / pool） |
| 数据校验 | **pydantic v2** + **pydantic-settings** | 请求 / 响应模型、参数校验、配置加载 |
| 图像处理 | **Pillow** | Data URL 编解码、格式探测、缩略图 |
| 测试 | **pytest** + **pytest-asyncio** + **respx** | 上游 API 模拟、离屏 Qt 测试 |
| 代码质量 | **Ruff** | Lint + import 排序 + 格式化 |
| 打包 | **PyInstaller** | onedir 桌面应用，macOS 生成 `.app` |

## 🏗️ 架构

严格三层：**handler / UI → service → repository**，UI 与网络、业务解耦，两种入口复用同一服务层。

```
┌─────────────────────────────┐      ┌─────────────────────────────┐
│      桌面端 (PySide6)         │      │       REST 服务 (FastAPI)     │
│  desktop/ui/*  Signal/Slot   │      │  handlers/*  ← middleware/*  │
│        ↓                     │      │        ↓  Depends            │
│  desktop/controller.py       │      │  core/dependencies.py        │
│        ↓  QThreadPool/ApiTask│      │                              │
└──────────┬──────────────────┘      └──────────────┬──────────────┘
           │                                        │
           └──────────────┬─────────────────────────┘
                          ▼
            services/  ImageService · HistoryService
                          │
        ┌─────────────────┼──────────────────────┐
        ▼                 ▼                      ▼
  repositories/      repositories/         clients/sensenova.py
  HistoryRepository  ImageStorage          鉴权 · 指数退避 · 脱敏 · 结果下载
  (JSON 文件)         (本地落盘)                     │
                                                    ▼
                                        SenseNova Cloud API /v1
```

### 目录结构

```
src/nova_canvas/
├── main.py                 # FastAPI 应用工厂与入口
├── core/                   # 配置、日志、业务异常、依赖注入、FastAPI 异常处理器
├── middleware/             # Request-ID、访问日志
├── schemas/                # pydantic 模型：尺寸 / Data URL / 张数校验
├── handlers/               # HTTP 路由（仅协议转换）
├── services/               # 业务编排：调用 → 落盘 → 写历史
├── repositories/           # 抽象仓储 + JSON 文件 / 本地文件实现
├── clients/                # SenseNova 异步客户端
├── utils/                  # 尺寸校验、Data URL 编解码、缩略图
└── desktop/                # 桌面端
    ├── main.py             #   QApplication 入口
    ├── config.py           #   ConfigStore：QSettings + 环境变量
    ├── workers.py          #   QRunnable + WorkerSignals
    ├── controller.py       #   任务提交 / 结果分发 / 状态管理
    └── ui/                 #   主窗口、参数面板、画布、拖拽上传、历史、设置…
```

### 设计要点

- 🧩 **Repository 模式** — 抽象接口 + 文件实现，可平滑替换为数据库
- 💉 **依赖注入** — 后端用 FastAPI `Depends`，桌面端由 Controller 按任务组装
- 🧵 **UI 线程零阻塞** — 网络调用全部在 `QThreadPool`，信号回传结果
- 🚫 **服务层不依赖 Web 框架** — 桌面打包时可完整排除 FastAPI / Uvicorn
- ⏱️ **24h 链接过期对策** — 结果拿到即下载落盘，预览与历史一律读本地文件

## 📡 REST API

Base path：`/api/v1`

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/images/generations` | 文生图 |
| `POST` | `/images/edits` | 图片编辑（JSON，images 为 URL / Data URL） |
| `POST` | `/images/edits/upload` | 图片编辑（multipart 文件上传） |
| `GET` | `/images/presets` | 推荐尺寸预设 |
| `GET` | `/history` | 历史列表（分页，新的在前） |
| `GET` | `/history/{id}` | 历史详情 |
| `GET` | `/history/{id}/image` | 下载结果图片（读本地文件） |
| `DELETE` | `/history/{id}` | 删除记录，可选同时删文件 |
| `GET` | `/health` | 健康检查 |

<details>
<summary>示例：文生图</summary>

```bash
curl -X POST http://127.0.0.1:8000/api/v1/images/generations \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "sensenova-u1.5-lite",
    "prompt": "一只在雪山之巅眺望日出的雪豹，电影感光影",
    "size": "2048x2048",
    "watermark": false
  }'
```

```json
{
  "id": "3f9c…",
  "created": 1788851674,
  "model": "sensenova-u1.5-lite",
  "size": "2048x2048",
  "output_format": "png",
  "usage": { "input_tokens": 593, "output_tokens": 4096, "total_tokens": 4689 },
  "file_path": "output/20260922_214019_123456_sensenova-u1.5-lite.png",
  "download_url": "/api/v1/history/3f9c…/image"
}
```

</details>

<details>
<summary>错误响应格式</summary>

```json
{
  "error": {
    "code": "rate_limited",
    "message": "请求过于频繁，请稍后重试",
    "request_id": "1a3d5846db53"
  }
}
```

| HTTP | code | 场景 |
|---|---|---|
| 400 | `upstream_rejected` | 上游拒绝（图片无法访问、参数非法） |
| 401 | `upstream_unauthorized` | API Key 无效 |
| 422 | `validation_error` | 请求参数校验失败（含 `details`） |
| 429 | `rate_limited` | 限流，重试耗尽 |
| 502 | `upstream_error` | 上游 5xx / 网络错误 |
| 503 | `not_configured` | 未配置 API Key |

</details>

## ⚙️ 配置

| 环境变量 | 默认 | 说明 |
|---|---|---|
| `SENSENOVA_API_KEY` | — | **必填**。API 密钥 |
| `NOVA_BASE_URL` | `https://token.sensenova.cn/v1` | 国际站改为 `https://token.sensenova.ai/v1` |
| `NOVA_OUTPUT_DIR` | `./output` | 结果落盘目录 |
| `NOVA_HISTORY_FILE` | `./output/history.json` | 历史记录文件 |
| `NOVA_REQUEST_TIMEOUT` | `120` | 读超时（秒），生成 4K 图耗时较长 |
| `NOVA_MAX_RETRIES` | `3` | 429 / 5xx 重试次数 |
| `NOVA_LOG_LEVEL` | `INFO` | 日志级别 |

桌面端的默认参数（模型、尺寸、格式、水印、落盘目录）保存在 QSettings，可在设置对话框修改。

## 📦 打包与跨平台分发

### 本地打包

```bash
make build            # 产物：dist/NovaCanvas/，macOS 额外生成 dist/NovaCanvas.app
```

- onedir 模式，冷启动快；已排除 WebEngine、Qml、Multimedia 等未使用的 Qt 模块及 Web 服务栈，体积约 120 MB
- macOS 产物未签名，其他机器首次打开需右键“打开”；正式分发请自行 `codesign` + `notarytool`

### 跨平台 CI/CD 构建 (GitHub Actions)

项目配置了完整的自动化构建流 [`.github/workflows/build.yml`](.github/workflows/build.yml)，支持：

- **代码质量门禁**：在 Ubuntu 上快速执行 Ruff 语法检查与 Pytest 自动化测试
- **多平台矩阵构建**：
  | 平台 / 架构 | 运行环境 | 打包产物 | 说明 |
  |---|---|---|---|
  | **macOS (Apple Silicon)** | `macos-latest` (arm64) | `NovaCanvas-macos-arm64.dmg`<br>`NovaCanvas-macos-arm64.zip` | 挂载即用的 DMG 镜像与压缩包 |
  | **macOS (Intel)** | `macos-13` (x86_64) | `NovaCanvas-macos-x86_64.dmg`<br>`NovaCanvas-macos-x86_64.zip` | 兼容旧款 Intel Mac 芯片 |
  | **Windows** | `windows-latest` (x64) | `NovaCanvas-windows-x64.zip` | 解压双击 `NovaCanvas.exe` 即可使用 |
  | **Linux** | `ubuntu-22.04` (x86_64) | `NovaCanvas-linux-x86_64.tar.gz` | 保留可执行权限，解压即运行 |
- **构建物获取与发布**：
  - **日常 PR / 分支推送 / 手动触发 (workflow_dispatch)**：构建产物自动保存于 Actions Artifacts 中（保留 14 天）。
  - **版本发布 (Git Tag)**：推送版本标签（如 `git tag v0.1.0 && git push origin v0.1.0`）时，工作流自动聚合所有平台的二进制产物，创建 GitHub Release 并上传资产。

## 🧑‍💻 开发

```bash
make help             # 查看全部命令
make check            # lint + test
make fmt              # ruff 自动修复 + 格式化
make test-desktop     # 仅运行离屏 Qt 测试
```

### 测试

```bash
make test
```

- 后端：`respx` 模拟 SenseNova 上游，覆盖 b64 / url 两种返回、重试与限流、密钥脱敏、参数校验、历史 CRUD、文件上传
- 桌面：`QT_QPA_PLATFORM=offscreen` 无头运行，覆盖参数校验流转、编辑页主图约束、后台任务信号

## 🗺️ Roadmap

- [ ] 批量队列：串行提交多条 prompt
- [ ] 提示词模板库 / 收藏
- [ ] 从历史记录一键复现全部参数
- [ ] 国际站 Base URL 快捷切换
- [ ] macOS 代码签名与公证

## 📄 License

[MIT](LICENSE) © 2026 wylu1037
