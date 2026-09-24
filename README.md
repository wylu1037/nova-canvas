<div align="center">

# 🎨 NovaCanvas

**基于商汤 SenseNova U1.5 的跨平台图片生成与多图编辑工作台**

提供 Qt 桌面客户端 (PySide6) 与 REST API 服务 (FastAPI) 双入口，共享高内聚服务层架构。

[![CI Build](https://github.com/wylu1037/nova-canvas/actions/workflows/build.yml/badge.svg)](https://github.com/wylu1037/nova-canvas/actions/workflows/build.yml)
[![Release](https://img.shields.io/github/v/release/wylu1037/nova-canvas?color=blue&logo=github)](https://github.com/wylu1037/nova-canvas/releases)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey?logo=apple&logoColor=white)](https://github.com/wylu1037/nova-canvas/releases)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-Qt%206-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![uv](https://img.shields.io/badge/uv-managed-DE5FE9?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)
[![Tests](https://img.shields.io/badge/tests-26%20passed-brightgreen)](#-开发与测试)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[功能特性](#-功能特性) · [获取 API Key](#-获取-sensenova-api-key) · [快速开始](#-快速开始) · [使用指南](#-桌面端使用指南) · [技术栈](#-技术栈) · [架构设计](#-架构设计) · [REST API](#-rest-api) · [打包与分发](#-打包与跨平台分发) · [参与贡献](#-参与贡献)

</div>

---

## ✨ 功能特性

| 模块 | 功能 | 说明 |
|---|---|---|
| �️ | **文生图 (Text-to-Image)** | 输入文本提示词生成 2K / 4K 超高清图像，内置 6 种主流宽高比预设，支持任意分辨率动态像素约束校验 |
| ✏️ | **图片编辑 (Image-to-Image)** | 支持 1 张主图 + 最多 4 张风格/参考图融合，支持文件拖拽、本地选择与公网图片 URL |
| 🔁 | **生成 → 编辑创作闭环** | 一键将文生图结果送入图片编辑作为主图，无需手动保存导入，支持快速多轮局部迭代与风格转换 |
| 🗂️ | **即时落盘历史画廊** | 生成结果**立即保存到本地磁盘**，彻底告别云端临时链接 24 小时过期失效困扰，支持随时回看与参数复现 |
| ⚡ | **双模型自由切换** | 支持 `sensenova-u1.5-lite`（画质精细写实）与 `sensenova-u1.5-fast`（极速响应）一键切换 |
| 🛡️ | **企业级容错与健壮性** | 内置 429 限流 / 5xx 上游故障指数退避重试机制、敏感密钥脱敏日志打印、显式参数防漂移 |
| 🔐 | **多层级安全凭证管理** | 环境变量 > 会话内存 > 本地加密持久化三级优先级，保障密钥安全 |
| 🌐 | **双端同源架构** | 同一套业务能力既支持原生 Qt 桌面客户端交互，也支持通过 FastAPI 开放标准化 REST API 与 Swagger 文档 |

---

## 🔑 获取 SenseNova API Key

NovaCanvas 底层依托商汤 **SenseNova U1.5** 大模型提供视觉生成能力。在开始使用前，您需要准备一个 API Key：

1. **注册账号**：
   访问商汤日日新开放平台官方网站 👉 **[https://www.sensenova.cn](https://www.sensenova.cn)**，完成注册并登录。
2. **登录控制台与获取体验额度**：
   进入 **[控制台 (Console)](https://www.sensenova.cn)**，新注册用户通常可在控制台直接领取免费体验 Token 额度，可直接用于文生图与图生图。
3. **创建 API Key**：
   在控制台左侧导航栏进入 **API Keys**，点击 **创建 API Key**，复制生成的密钥。
4. **填入配置**：
   - **桌面客户端**：首次启动时软件会自动弹出设置对话框，将 API Key 粘贴保存即可。
   - **REST 服务端**：将 API Key 填入项目根目录 `.env` 文件中的 `SENSENOVA_API_KEY` 变量。
   - *(可选)* 海外或国际站用户可在配置中将 Base URL 切换为 `https://token.sensenova.ai/v1`。

---

## 🚀 快速开始

### 方式一：下载桌面安装包（推荐普通用户，免配环境）

无需配置 Python 开发环境，直接前往 **[GitHub Releases 最新版本发布页](https://github.com/wylu1037/nova-canvas/releases)** 下载对应系统的安装包：

| 操作系统 | 下载文件 | 安装与使用说明 |
|---|---|---|
| **macOS (Apple Silicon)** | `NovaCanvas-macos-arm64.dmg`<br>`NovaCanvas-macos-arm64.zip` | 适用于 M1/M2/M3/M4 系列 Mac。双击打开 DMG 镜像，将 `NovaCanvas.app` 拖入 `Applications` 即可。 |
| **macOS (Intel)** | `NovaCanvas-macos-x86_64.dmg`<br>`NovaCanvas-macos-x86_64.zip` | 适用于 Intel 芯片的老款 Mac 设备。 |
| **Windows** | `NovaCanvas-windows-x64.zip` | 适用于 64 位 Windows 10/11。解压后进入目录，双击 `NovaCanvas.exe` 启动。 |
| **Linux** | `NovaCanvas-linux-x86_64.tar.gz` | 适用于 Ubuntu / Debian / Fedora 等主流 Linux 发行版。解压后运行 `./NovaCanvas/NovaCanvas`。 |

> [!TIP]
> **macOS 首次打开提示未签名？**  
> 因为开源安装包未附加商业证书签名，若系统提示“无法打开，因为无法验证开发者”，请在 macOS 的 **「系统设置」->「隐私与安全性」** 底部点击 **「仍要打开」** 即可正常使用。

---

### 方式二：从源码运行与二次开发（推荐开发者）

#### 环境要求

- **Python** ≥ 3.11
- **包管理器**：推荐使用 [uv](https://docs.astral.sh/uv/)（安装极其快速：`curl -LsSf https://astral.sh/uv/install.sh | sh` 或 `brew install uv`）
- **API 凭证**：前往 [https://www.sensenova.cn](https://www.sensenova.cn) 注册并获取的 API Key

#### 1. 克隆代码与依赖同步

```bash
git clone https://github.com/wylu1037/nova-canvas.git
cd nova-canvas

# 安装全量依赖（包含 PySide6、FastAPI 及开发工具包）
make install          # 等价于 uv sync --all-groups
```

#### 2. 启动桌面端 (PySide6)

```bash
make desktop
```

*首次启动会自动弹出设置对话框，输入 API Key 即可。也可通过环境变量临时注入：*

```bash
export SENSENOVA_API_KEY=sk-your-key-here
make desktop
```

#### 3. 启动 REST API 后端服务 (FastAPI)

```bash
make env              # 自动根据 .env.example 生成 .env 配置文件
# 编辑 .env 填入 SENSENOVA_API_KEY=sk-...

make dev              # 开发模式（热重载），监听 http://127.0.0.1:8000
```

服务启动后，在浏览器访问 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** 即可打开交互式 Swagger UI 文档直接调试接口。

---

## 💡 桌面端使用指南

- 🖼️ **文生图 (Text to Image)**：
  1. 在左侧参数面板选择模型：`u1.5-lite`（细腻写实）或 `u1.5-fast`（极速生成）。
  2. 输入创意提示词（Prompt），支持中文与英文自然语言描述。
  3. 点击推荐尺寸快速设定（如 1:1 正方形 2048x2048、16:9 横屏 2560x1440、9:16 竖屏 1440x2560 等），支持自定义宽高。
  4. 点击 **「生成图片」**，UI 界面零阻塞（后台线程池异步调用），结果生成后实时高清预览。
- ✏️ **图片编辑与风格迁移 (Image Edit)**：
  1. 切换至 **「图片编辑」** 标签页。
  2. 拖拽或点击选择上传 1 张主体图片，同时支持上传最多 4 张参考图（垫图）。
  3. 输入修改要求（例如：*“将背景切换为黄昏的雪山，保持主体猫咪不变”*）。
  4. 点击 **「开始编辑」** 查看生成效果。
- 🔁 **生成 → 编辑迭代闭环**：
  - 在生成结果下方点击 **「送入编辑」**，即可将刚刚生成的图片无缝设置为编辑主图，继续补充提示词进行微调。
- 🗂️ **本地画廊与历史记录**：
  - 点击右上角「历史」面板展开抽屉。
  - 所有图片均在本地 `./output` 目录落盘，支持点击卡片随时重新载入、查看参数或在文件管理器中打开。

---

## 🧰 技术栈

| 领域 | 选型 | 说明 |
|---|---|---|
| **核心语言** | **Python 3.11+** | 强类型注解、`StrEnum`、模式匹配等现代化语法 |
| **包管理工具** | **uv** | 极速依赖解析、虚拟环境隔离与工作流脚本统一管理 |
| **桌面客户端** | **PySide6 (Qt 6)** | 原生跨平台 UI 控件、`QThreadPool` 与信号槽异步机制 |
| **Web API 框架** | **FastAPI + Uvicorn** | 高性能异步路由、依赖注入、自动 OpenAPI / Swagger 文档 |
| **异步网络请求** | **httpx** | 细粒度网络超时控制、连接池管理与指数退避重试 |
| **数据校验** | **Pydantic v2 + Settings** | 声明式数据模型校验、严格类型检查、多源配置读取 |
| **图像底层处理** | **Pillow (PIL)** | 本地图片读写、Data URL 编解码、尺寸自适应与缩略图生成 |
| **自动化测试** | **Pytest + Respx** | 离屏 Qt 交互测试 (`offscreen`) 与完整 Mock 上游云端接口 |
| **代码规范与质量** | **Ruff** | 极速静态代码分析、规范格式化与 Import 排序 |
| **打包分发** | **PyInstaller** | onedir 跨平台构建，macOS 生成标准 `.app` / `.dmg` |

---

## 🏗️ 架构设计

严格遵循三层分层设计：**handler / UI → service → repository**。界面交互与云端网络调用完全解耦，桌面端与 REST 接口复用同一套服务层逻辑。

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
├── main.py                 # FastAPI 应用入口与路由挂载
├── core/                   # 全局配置、日志、业务异常模型、FastAPI 依赖注入
├── middleware/             # 全局 Request-ID、结构化访问日志中间件
├── schemas/                # Pydantic 校验模型：尺寸规则、Data URL、请求响应结构
├── handlers/               # HTTP 路由处理器（协议解析与转换）
├── services/               # 核心业务层：编排任务调用、图片本地落盘、历史写入
├── repositories/           # 仓储抽象与本地实现（JSON 历史数据库、图片存储）
├── clients/                # SenseNova 异步 HTTP 客户端封装（带重试与脱敏）
├── utils/                  # 尺寸算子校验、Data URL 编解码工具
└── desktop/                # 桌面端完整实现
    ├── main.py             #   QApplication 启动入口
    ├── config.py           #   ConfigStore：QSettings 与环境变量持久化管理
    ├── workers.py          #   QRunnable 异步任务封装与 WorkerSignals 信号分发
    ├── controller.py       #   任务调度、状态机管理与结果分发
    └── ui/                 #   主窗口、参数面板、画布、拖拽组件、历史画廊、设置弹窗
```

---

## 📡 REST API

基础路径：`/api/v1`

| 请求方法 | 路由路径 | 功能说明 |
|---|---|---|
| `POST` | `/images/generations` | 文本生成图片（文生图） |
| `POST` | `/images/edits` | 图片编辑 / 垫图（JSON 格式，支持 Base64 / URL） |
| `POST` | `/images/edits/upload` | 图片编辑（Multipart/form-data 文件直传） |
| `GET` | `/images/presets` | 获取官方推荐分辨率及长宽比预设 |
| `GET` | `/history` | 查询本地历史生成记录（支持分页，按时间倒序） |
| `GET` | `/history/{id}` | 查询单条历史详情 |
| `GET` | `/history/{id}/image` | 下载或查看历史图片二进制流 |
| `DELETE` | `/history/{id}` | 删除指定历史记录（支持连带删除本地原图） |
| `GET` | `/health` | 服务健康检查 |

<details>
<summary><b>查看 API 调用示例 (cURL)</b></summary>

```bash
curl -X POST http://127.0.0.1:8000/api/v1/images/generations \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "sensenova-u1.5-lite",
    "prompt": "一只在雪山之巅眺望日出的雪豹，电影感光影，8k超高清",
    "size": "2048x2048",
    "watermark": false
  }'
```

**成功返回示例：**

```json
{
  "id": "3f9c8d2a1b",
  "created": 1788851674,
  "model": "sensenova-u1.5-lite",
  "size": "2048x2048",
  "output_format": "png",
  "usage": { "input_tokens": 593, "output_tokens": 4096, "total_tokens": 4689 },
  "file_path": "output/20260922_214019_123456_sensenova-u1.5-lite.png",
  "download_url": "/api/v1/history/3f9c8d2a1b/image"
}
```

</details>

---

## ⚙️ 环境变量与配置

支持通过环境变量或根目录 `.env` 文件进行配置：

| 配置项 | 默认值 | 必填 | 说明 |
|---|---|:---:|---|
| `SENSENOVA_API_KEY` | — | **是** | 商汤 SenseNova API 密钥（获取自 [https://www.sensenova.cn](https://www.sensenova.cn)） |
| `NOVA_BASE_URL` | `https://token.sensenova.cn/v1` | 否 | API 基础地址（国际站请填写 `https://token.sensenova.ai/v1`） |
| `NOVA_OUTPUT_DIR` | `./output` | 否 | 生成图片本地保存目录 |
| `NOVA_HISTORY_FILE` | `./output/history.json` | 否 | 本地历史生成记录存储文件路径 |
| `NOVA_REQUEST_TIMEOUT` | `120` | 否 | HTTP 请求超时时间（秒，高分辨率生图耗时稍长） |
| `NOVA_MAX_RETRIES` | `3` | 否 | 触发 429 限流或 5xx 异常时的最大退避重试次数 |
| `NOVA_LOG_LEVEL` | `INFO` | 否 | 日志输出级别（`DEBUG` / `INFO` / `WARNING` / `ERROR`） |

---

## 📦 打包与跨平台分发

### 本地编译打包

```bash
make build            # 产物输出至 dist/NovaCanvas，macOS 环境自动生成 dist/NovaCanvas.app
```

- 采用 onedir 模式，冷启动极快；已剔除 WebEngine、QML、3D 等冗余 Qt 模块，构建包体积控制在约 120 MB。

### 自动化跨平台 CI/CD (GitHub Actions)

项目内置了自动化构建流水线 [`.github/workflows/build.yml`](.github/workflows/build.yml)：

- **自动化质量把控**：Ubuntu Runner 上严格执行 Ruff 代码规范检查与 Pytest 单元测试。
- **全平台构建矩阵**：
  - 🍏 **macOS (Apple Silicon)**：编译生成 `NovaCanvas-macos-arm64.dmg` 与 `.zip`。
  - 🍏 **macOS (Intel)**：编译生成 `NovaCanvas-macos-x86_64.dmg` 与 `.zip`。
  - 🪟 **Windows (x64)**：编译生成 `NovaCanvas-windows-x64.zip`。
  - 🐧 **Linux (x86_64)**：基于 Ubuntu 22.04 编译生成 `NovaCanvas-linux-x86_64.tar.gz`。
- **Release 发布机制**：推送版本标签（例如 `git tag v0.1.0 && git push origin v0.1.0`）时，工作流自动聚合全平台产物并发布到 GitHub Releases。

---

## 🧑‍💻 开发与测试

```bash
make help             # 查看所有 Makefile 可用指令
make check            # 执行代码风格校验与测试（lint + test）
make fmt              # 使用 Ruff 进行代码自动修复与格式化
make test-desktop     # 仅运行 Qt 桌面端离屏测试
```

### 自动化测试

```bash
make test
```

- **后端测试**：使用 `respx` 完整模拟 SenseNova 上游接口行为，覆盖 Base64 / URL 返回、指数退避重试、限流容错、参数校验及历史记录增删改查。
- **桌面测试**：利用 `QT_QPA_PLATFORM=offscreen` 在无头模式下自动化测试信号流转、参数约束联动与任务取消逻辑。

---

## 🤝 参与贡献

我们非常欢迎并感谢社区的任何贡献！如果您希望参与改进 NovaCanvas：

1. **提交反馈**：在 [Issues](https://github.com/wylu1037/nova-canvas/issues) 提出使用疑问、Bug 报告或功能建议。
2. **贡献代码**：
   - Fork 本仓库并创建特性分支：`git checkout -b feature/amazing-feature`
   - 编写代码并确保测试通过：`make check`
   - 提交代码并提交 Pull Request，GitHub Actions 将会自动验证多平台构建。

如果这个项目对您有所启发或帮助，欢迎为本项目点亮一颗 ⭐️ **Star**！

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 协议开源。
