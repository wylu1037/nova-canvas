# NovaCanvas — 技术设计与 UI 设计

> 项目名：**NovaCanvas**（包名 `nova_canvas`，展示名"NovaCanvas 图片工作台"）
> 基于 SenseNova U1.5 Lite / U1.5 Fast 云端 API，使用 PySide6 (Qt) 开发的桌面图片生成与编辑工具。

- 文档版本：v1.0
- 日期：2026-09-22
- 目标平台：macOS / Windows / Linux（Qt 跨平台）

---

## 1. 项目概述

一个本地桌面客户端，通过 SenseNova 云端 API 完成两类任务：

1. **文生图（Text-to-Image）**：输入提示词，生成 2K/4K 图片。
2. **图片编辑（Image Edit）**：上传 1~5 张图（第 1 张为主编辑图，其余为参考图），加编辑指令，输出修改后的图片。

应用本身不做本地推理，所有算力在云端；客户端只负责：组织请求、管理密钥、后台调用、预览与保存结果、维护历史记录。

### 1.1 模型与能力对照

| 模型名（`model` 字段） | 定位 | 适用场景 |
|---|---|---|
| `sensenova-u1.5-lite` | 轻量高质量版 | 追求成图质量、复杂版式、文字渲染 |
| `sensenova-u1.5-fast` | 加速版 | 追求出图速度、批量迭代、快速预览 |

两个模型的接口路径、请求字段、响应结构**完全一致**，UI 上仅作为一个下拉项切换 `model` 值。

---

## 2. API 规格（事实来源）

所有请求基于 Base URL：`https://token.sensenova.cn/v1`
鉴权：请求头 `Authorization: Bearer <SENSENOVA_API_KEY>`，`Content-Type: application/json`。

### 2.1 图片生成 `POST /images/generations`

| 字段 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `model` | string | 是 | — | `sensenova-u1.5-lite` / `sensenova-u1.5-fast` |
| `prompt` | string | 是 | — | 图像生成描述 |
| `n` | integer | 否 | 1 | 仅支持 `1` |
| `size` | string | 否 | `auto` | `{W}x{H}`，W/H 为 32 的倍数，范围 512~4096，最大比例 3:1 或 1:3 |
| `watermark` | boolean | 否 | true | true 加官方 Logo 水印；false 无水印（公测免费，后续收费） |
| `response_format` | string | 否 | `b64_json` | `b64_json` 返回 Base64；`url` 返回 24h 有效临时链接 |
| `output_format` | string | 否 | `png` | `png` / `jpg` / `jpeg` / `webp` |
| `prompt_extend` | boolean | 否 | true | 提示词自动润色；扩写失败自动回退原始 prompt |

**推荐分辨率预设**：

| 尺寸 | 比例 | 档位 |
|---|---|---|
| 2048x2048 | 1:1 | 2K |
| 2720x1536 | 16:9 | 2K |
| 1536x2720 | 9:16 | 2K |
| 2496x1664 | 3:2 | 2K |
| 1664x2496 | 2:3 | 2K |
| 4096x4096 | 1:1 | 4K |

### 2.2 图片编辑 `POST /images/edits`

在生成接口字段基础上，用 `images` 数组替代纯文本输入：

| 字段 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `model` | string | 是 | — | 同上 |
| `images` | array | 是 | — | 图片对象数组，第 1 张为主编辑图，至多 5 张参考图 |
| `images[].image_url` | string | 是 | — | 公网 URL 或 Base64 Data URL |
| `prompt` | string | 是 | — | 编辑指令；去除首尾空格后不可为空；尽量保留未指定修改的主体 |
| `n` / `size` / `response_format` / `output_format` / `watermark` / `prompt_extend` | — | 否 | 同生成接口 | `size=auto` 时自动适配主图 |

**图片输入两种方式**：
- 公网 URL：`http`/`https` 可公开访问地址。
- Base64 Data URL：**必须带完整前缀** `data:image/{format};base64,{data}`，不支持纯 Base64 字符串。

### 2.3 响应结构（生成 / 编辑通用）

```json
{
  "created": 1788851674,
  "data": [
    { "url": "https://cdn.sensenova.dev/gen/..." }
  ],
  "output_format": "png",
  "size": "2048x2048",
  "usage": {
    "input_tokens": 8785,
    "input_tokens_details": { "image_tokens": 8192, "text_tokens": 593 },
    "output_tokens": 4096,
    "total_tokens": 12881,
    "images_count": 1
  }
}
```

- `data[i]` 中 `url` 与 `b64_json` **不同时返回**，由 `response_format` 决定。
- `url` 有效期固定 **24 小时**，过期即失效。客户端应在拿到结果后立即下载落盘。

### 2.4 约束与边界

- 编辑接口**必须**至少 1 张输入图，不支持仅 prompt。
- `url` 链接 24h 过期 → 结果必须本地持久化。
- Base64 必须含 Data URL 前缀。
- 图片无法访问 / 非有效图片 / Base64 解码失败 → 请求被直接拒绝。
- `watermark=false` 目前免费公测，建议**显式传参**以防默认值变更。
- 限流：约 1500 请求 / 5 小时（Token Plan），需处理 429。

---

## 3. 技术选型与依赖

| 层 | 选型 | 说明 |
|---|---|---|
| GUI 框架 | **PySide6** (Qt 6) | 官方 LGPL 授权，控件成熟 |
| HTTP 客户端 | **httpx** 或 requests | 建议 httpx，支持超时细分与 HTTP/2 |
| 并发 | **QThreadPool + QRunnable** | 后台调用 API，避免阻塞 UI 事件循环 |
| 图像处理 | **Pillow** | 缩略图、格式转换、Base64 编解码 |
| 配置/密钥 | **QSettings** + 环境变量 | 跨平台持久化，密钥优先读环境变量 |
| 打包 | PyInstaller | 生成单文件可执行程序（可选） |

```
Python >= 3.10
PySide6
httpx
Pillow
```

---

## 4. 整体架构

分层设计，UI 与网络/业务解耦，便于测试与后续替换：

```
┌─────────────────────────────────────────────┐
│                   UI 层 (Qt Widgets)          │
│  MainWindow · GenerateTab · EditTab           │
│  ParamPanel · ImageCanvas · HistoryPanel      │
└───────────────┬─────────────────────────────┘
                │ Signal / Slot
┌───────────────▼─────────────────────────────┐
│               控制层 (Controller)             │
│  提交任务 · 参数校验 · 结果分发 · 状态管理     │
└───────────────┬─────────────────────────────┘
                │ 提交 QRunnable 到 QThreadPool
┌───────────────▼─────────────────────────────┐
│           服务层 (SenseNovaClient)            │
│  generate_image() · edit_image()              │
│  鉴权 · 重试 · 错误映射 · 结果下载             │
└───────────────┬─────────────────────────────┘
                │ httpx
┌───────────────▼─────────────────────────────┐
│          SenseNova Cloud API (/v1)            │
└─────────────────────────────────────────────┘

配套：
- ConfigStore（密钥 / 默认参数持久化）
- HistoryStore（历史记录 + 本地图片落盘）
- 工具模块：image_utils（Base64、缩略图、尺寸校验）
```

### 4.1 目录结构

```
nova_canvas/
├── main.py                     # 入口，启动 QApplication
├── requirements.txt
├── app/
│   ├── config.py               # ConfigStore：QSettings + 环境变量
│   ├── client.py               # SenseNovaClient：API 封装
│   ├── models.py               # 请求/响应数据类
│   ├── workers.py              # QRunnable 任务 + WorkerSignals
│   ├── history.py              # HistoryStore：历史与落盘
│   ├── image_utils.py          # Base64 / 缩略图 / size 校验
│   └── ui/
│       ├── main_window.py
│       ├── generate_tab.py
│       ├── edit_tab.py
│       ├── param_panel.py      # 生成/编辑共用参数面板
│       ├── image_canvas.py     # 结果预览 + 缩放
│       ├── image_dropzone.py   # 编辑页拖拽上传（含参考图列表）
│       ├── history_panel.py
│       └── settings_dialog.py  # API Key / 默认值设置
└── output/                     # 结果图片默认落盘目录
```

---

## 5. 核心模块设计

### 5.1 数据模型（`models.py`）

```python
from dataclasses import dataclass, field

@dataclass
class GenerateRequest:
    model: str                    # sensenova-u1.5-lite / -fast
    prompt: str
    size: str = "auto"            # "auto" 或 "2048x2048"
    watermark: bool = True
    response_format: str = "b64_json"
    output_format: str = "png"
    prompt_extend: bool = True
    n: int = 1

@dataclass
class EditRequest:
    model: str
    images: list[str]             # 每项为公网 URL 或 data URL
    prompt: str
    size: str = "auto"
    watermark: bool = True
    response_format: str = "b64_json"
    output_format: str = "png"
    prompt_extend: bool = True
    n: int = 1

@dataclass
class ImageResult:
    image_bytes: bytes            # 已下载/解码的最终图片字节
    size: str
    output_format: str
    usage: dict
    source_url: str = ""          # 若 response_format=url，保留原始链接（24h）
    saved_path: str = ""          # 落盘后路径
```

### 5.2 API 客户端（`client.py`）

关键点：统一鉴权、超时细分、可重试状态码、错误信息脱敏、结果统一解码为字节。

```python
import base64, httpx

RETRYABLE = {429, 500, 502, 503, 504}

class SenseNovaError(Exception):
    """对外统一的业务异常，携带用户可读信息。"""

class SenseNovaClient:
    def __init__(self, api_key: str,
                 base_url: str = "https://token.sensenova.cn/v1",
                 timeout: float = 120.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        # 生成/编辑耗时较长，read 超时放宽，connect 收紧
        self.timeout = httpx.Timeout(connect=10.0, read=timeout, write=30.0, pool=10.0)

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"}

    def generate(self, req) -> "ImageResult":
        payload = {
            "model": req.model, "prompt": req.prompt, "n": req.n,
            "size": req.size, "watermark": req.watermark,
            "response_format": req.response_format,
            "output_format": req.output_format,
            "prompt_extend": req.prompt_extend,
        }
        raw = self._post("/images/generations", payload)
        return self._to_result(raw)

    def edit(self, req) -> "ImageResult":
        payload = {
            "model": req.model,
            "images": [{"image_url": u} for u in req.images],
            "prompt": req.prompt, "n": req.n, "size": req.size,
            "watermark": req.watermark,
            "response_format": req.response_format,
            "output_format": req.output_format,
            "prompt_extend": req.prompt_extend,
        }
        raw = self._post("/images/edits", payload)
        return self._to_result(raw)

    def _post(self, path, payload):
        url = self.base_url + path
        last = None
        for attempt in range(3):
            try:
                with httpx.Client(timeout=self.timeout) as c:
                    r = c.post(url, headers=self._headers(), json=payload)
                if r.status_code in RETRYABLE and attempt < 2:
                    last = r
                    continue
                if not (200 <= r.status_code < 300):
                    raise SenseNovaError(self._fmt_error(r))
                return r.json()
            except httpx.HTTPError as e:
                last = e
                if attempt < 2:
                    continue
                raise SenseNovaError(f"网络请求失败：{type(e).__name__}")
        raise SenseNovaError("请求重试后仍失败")

    def _to_result(self, raw):
        item = raw["data"][0]
        if "b64_json" in item and item["b64_json"]:
            data = base64.b64decode(_strip_data_url(item["b64_json"]))
            src = ""
        else:                                # response_format=url
            src = item["url"]
            data = self._download(src)       # 24h 内立即下载落盘
        return ImageResult(image_bytes=data, size=raw.get("size", ""),
                           output_format=raw.get("output_format", "png"),
                           usage=raw.get("usage", {}), source_url=src)

    def _fmt_error(self, r):
        try:
            body = r.json()
            msg = body.get("error", {}).get("message") or body.get("message") or ""
        except Exception:
            msg = r.text[:300]
        msg = msg.replace(self.api_key, "[REDACTED]") if self.api_key else msg
        return f"API 错误 HTTP {r.status_code}: {msg}"
```

> 说明：Base64 结果需 `_strip_data_url` 去掉可能的 `data:image/...;base64,` 前缀再解码；`url` 结果需**立即下载**，因链接 24h 过期。

### 5.3 后台任务（`workers.py`）

网络调用绝不能跑在 UI 线程。用 `QRunnable` + `QThreadPool`，通过信号回传结果：

```python
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

class WorkerSignals(QObject):
    finished = Signal(object)   # ImageResult
    error = Signal(str)
    started = Signal()

class ApiTask(QRunnable):
    def __init__(self, fn, *args):
        super().__init__()
        self.fn, self.args = fn, args
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        self.signals.started.emit()
        try:
            self.signals.finished.emit(self.fn(*self.args))
        except Exception as e:
            self.signals.error.emit(str(e))
```

控制层提交：`QThreadPool.globalInstance().start(ApiTask(client.generate, req))`，并把 `finished/error` 连接到 UI 槽函数（更新预览、恢复按钮、弹错误）。

### 5.4 配置与密钥（`config.py`）

优先级：**环境变量 `SENSENOVA_API_KEY` > QSettings 存储**。

- 密钥不硬编码、不写日志、不进历史记录文件。
- 若用 QSettings 存储密钥，向用户提示明文风险；提供"仅本次会话记住"选项。
- 默认参数（model、size、watermark、output_format 等）持久化到 QSettings。

### 5.5 历史记录（`history.py`）

- 每次成功生成/编辑：图片字节落盘到 `output/{timestamp}_{model}.{ext}`。
- 元数据（prompt、参数、usage、时间、文件路径）写入本地 `history.json`。
- **不依赖 `url`**（24h 过期），预览一律读本地文件。

---

## 6. UI 设计

### 6.1 总体布局（主窗口）

顶部工具栏 + 中部双 Tab（生成 / 编辑）+ 右侧历史抽屉 + 底部状态栏。

```
┌──────────────────────────────────────────────────────────────┐
│  NovaCanvas 图片工作台       [模型: u1.5-lite ▾]   [⚙ 设置]     │  ← 工具栏
├───────────────┬──────────────────────────────┬───────────────┤
│  [文生图] [编辑] │                              │   历史记录     │
│  ┌───────────┐ │                              │  ┌─────────┐  │
│  │           │ │        结果预览画布            │  │ 缩略图1  │  │
│  │  参数面板  │ │      (缩放 / 适应窗口)         │  │ 缩略图2  │  │
│  │           │ │                              │  │ 缩略图3  │  │
│  │           │ │                              │  └─────────┘  │
│  └───────────┘ │                              │               │
│  [ 生成 ]      │   [下载] [复制] [作为编辑输入]  │               │
├───────────────┴──────────────────────────────┴───────────────┤
│  状态: 就绪   |   本次消耗 total_tokens: 5636   |   ● 在线      │  ← 状态栏
└──────────────────────────────────────────────────────────────┘
```

### 6.2 文生图 Tab

```
┌─ 参数面板 ────────────────┐
│ 提示词 (prompt)           │
│ ┌───────────────────────┐ │
│ │ 多行文本框             │ │
│ └───────────────────────┘ │
│ ☑ 自动润色 (prompt_extend) │
│                           │
│ 尺寸 (size)               │
│  [2048x2048 · 1:1 · 2K ▾] │  ← 预设下拉 + "自定义…"
│  自定义: [W____]x[H____]   │  ← 选自定义时展开，实时校验
│                           │
│ 输出格式 [png ▾]           │
│ 返回方式 [b64_json ▾]      │
│ ☐ 添加水印 (watermark)     │
│                           │
│        [  生成  ]          │  ← 生成时置灰 + 进度指示
└───────────────────────────┘
```

**交互要点**：
- `size` 下拉给出 §2.1 六个推荐预设 + `auto` + "自定义…"。
- 自定义尺寸实时校验：32 的倍数、512~4096、比例不超 3:1 / 1:3；不合法时输入框标红并禁用"生成"。
- 生成按钮点击后：置灰、显示旋转进度、状态栏更新为"生成中…"；完成后画布显示结果、状态栏显示 `usage`。

### 6.3 图片编辑 Tab

```
┌─ 输入图片 ────────────────┐   ┌─ 参数面板 ──────────────┐
│  主编辑图 (必填)           │   │ 编辑指令 (prompt)        │
│ ┌───────────────────────┐ │   │ ┌─────────────────────┐ │
│ │  拖拽 / 点击上传        │ │   │ │ 多行文本框           │ │
│ │  [缩略图]              │ │   │ └─────────────────────┘ │
│ └───────────────────────┘ │   │ ☑ 自动润色              │
│  参考图 (可选, 最多 4 张)   │   │ 尺寸 [auto (适配主图) ▾] │
│  [＋][img][img]           │   │ 输出格式 [png ▾]         │
│                           │   │ 返回方式 [b64_json ▾]    │
│  支持: 本地文件 / 公网 URL  │   │ ☐ 添加水印              │
│                           │   │        [  编辑  ]        │
└───────────────────────────┘   └─────────────────────────┘
```

**交互要点**：
- 主编辑图必填；未上传时"编辑"按钮禁用（呼应"编辑接口必须至少 1 张图"约束）。
- 参考图列表最多 4 张（加主图共 5 张，呼应"至多 5 张参考图"）。
- 本地图片上传时自动转 Base64 Data URL（带完整前缀）；也支持直接粘贴公网 URL。
- 上传前用 Pillow 生成缩略图预览，避免大图卡顿。
- 大图 Base64 会显著增加 `input_tokens`，UI 可提示预估体积。

### 6.4 结果画布（生成 / 编辑共用）

- 支持滚轮缩放、适应窗口、1:1 原始比例切换。
- 结果操作按钮：
  - **下载**：另存为（默认已落盘到 `output/`，此处为导出到用户指定位置）。
  - **复制**：复制图片到剪贴板。
  - **作为编辑输入**：一键把当前结果送到编辑 Tab 作主图，形成"生成→编辑"迭代闭环。

### 6.5 设置对话框

```
┌─ 设置 ────────────────────────────┐
│ API Key  [••••••••••••]  [显示]     │
│ Base URL [https://token.sensenova… ]│
│ 保存方式 (○ 仅本次会话  ○ 持久化)    │
│ ─────────────────────────────────  │
│ 默认模型  [sensenova-u1.5-lite ▾]   │
│ 默认尺寸  [2048x2048 ▾]             │
│ 默认输出  [png ▾]  默认返回 [url ▾] │
│ 落盘目录  [./output      ] [浏览]    │
│                       [取消] [保存]  │
└────────────────────────────────────┘
```

### 6.6 状态与反馈

| 状态 | UI 表现 |
|---|---|
| 就绪 | 状态栏"就绪"，按钮可用 |
| 请求中 | 按钮置灰 + 进度指示，状态栏"生成中…/编辑中…" |
| 成功 | 画布显示图，状态栏显示 `total_tokens` 与尺寸 |
| 失败 | 非阻塞提示条 + 状态栏红色错误摘要（脱敏后） |
| 限流 429 | 提示"请求过于频繁，稍后重试"，自动指数退避已在客户端处理 |

---

## 7. 关键交互时序（文生图）

```
用户            GenerateTab        Controller       ThreadPool/ApiTask     SenseNovaClient      Cloud API
 │  填写参数点生成 │                   │                    │                     │                 │
 │───────────────>│  校验 size/prompt  │                    │                     │                 │
 │                │──────────────────>│  构造 GenerateReq   │                     │                 │
 │                │  按钮置灰/进度      │───────提交 task────>│                     │                 │
 │                │                   │                    │──generate(req)─────>│                 │
 │                │                   │                    │                     │──POST /gen─────>│
 │                │                   │                    │                     │<──200 JSON──────│
 │                │                   │                    │  解码b64/下载url落盘  │                 │
 │                │<──finished(result)─────────────────────│                     │                 │
 │  预览+usage显示 │  画布渲染/恢复按钮  │  写入 HistoryStore  │                     │                 │
 │<───────────────│                   │                    │                     │                 │
```

失败路径：`ApiTask` 捕获异常 → `error(str)` 信号 → Controller 恢复按钮、弹出脱敏错误。

---

## 8. 错误处理与边界策略

| 场景 | 处理 |
|---|---|
| 缺少 API Key | 启动即引导进设置对话框，未配置时禁用生成/编辑 |
| 自定义尺寸非法 | 前端实时校验拦截，不发请求 |
| 编辑无输入图 | "编辑"按钮禁用 |
| `url` 24h 过期 | 结果拿到即下载落盘；预览与历史一律读本地文件 |
| Base64 无前缀 | 上传转换时统一补 `data:image/{fmt};base64,` |
| 429 限流 | 客户端指数退避重试；仍失败则提示稍后再试 |
| 5xx / 网络错误 | 重试 3 次；失败给出可读信息 |
| 密钥泄漏风险 | 错误信息、日志中脱敏；不写入历史文件 |
| watermark 默认变更风险 | 每次请求显式传 `watermark` |

---

## 9. 安全与合规

- **密钥管理**：优先读环境变量；持久化存储需显式告知明文风险。绝不硬编码、不打印、不入库。
- **不外传数据**：除调用 SenseNova 官方 API 外，不向任何第三方发送用户图片或提示词。
- **输出落盘**：结果保存在用户本地 `output/`，用户可自定义目录。
- **内容合规**：提示用户遵守 SenseNova 平台使用条款与内容政策。

---

## 10. 后续扩展（非首版）

- 批量队列：串行提交多条 prompt（`n` 仍限 1，靠客户端排队实现"批量"）。
- 提示词模板库 / 收藏。
- 局部编辑增强：结合参考图与区域指令做更精细的编辑指导（模型支持 bbox/mask 类控制时接入）。
- 生成参数与结果一键复现（从历史记录还原全部参数）。
- 国际站切换：Base URL 改 `https://token.sensenova.ai/v1`。

---

## 11. 首版开发里程碑建议

1. **M1 客户端内核**：`SenseNovaClient` + `models` + `image_utils`，命令行验证生成/编辑跑通。
2. **M2 骨架 UI**：主窗口 + 双 Tab + 设置对话框 + 后台任务串联，文生图闭环。
3. **M3 编辑闭环**：上传/参考图/Base64 转换 + 编辑接口 + "结果作为编辑输入"。
4. **M4 完善**：历史记录、错误处理、限流退避、落盘与导出、参数校验打磨。
5. **M5 打包**：PyInstaller 出包 + 基本冒烟测试。
