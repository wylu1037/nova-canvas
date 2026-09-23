# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：NovaCanvas 桌面端。

用法：uv run pyinstaller nova-canvas.spec
产物：dist/NovaCanvas（onedir，macOS 额外生成 dist/NovaCanvas.app）
onedir 而非 onefile：PySide6 体积大，onefile 每次启动需解压，冷启动明显变慢。
"""
import sys

# 这些名字由 PyInstaller 在执行 spec 时注入；显式导入让 IDE 静态检查能识别
from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.osx import BUNDLE

APP_NAME = "NovaCanvas"
ENTRY = "src/nova_canvas/desktop/main.py"

# 仅收集实际用到的 Qt 模块，排除 WebEngine / 3D / Multimedia 等大模块
EXCLUDED_QT = [
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets", "PySide6.Qt3DCore",
    "PySide6.Qt3DRender", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets",
    "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtPdf", "PySide6.QtBluetooth",
    "PySide6.QtNetworkAuth", "PySide6.QtPositioning", "PySide6.QtLocation", "PySide6.QtSensors",
    "PySide6.QtSerialPort", "PySide6.QtRemoteObjects", "PySide6.QtScxml", "PySide6.QtTest",
    "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtSql", "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets", "PySide6.QtSvgWidgets", "PySide6.QtTextToSpeech",
    "PySide6.QtWebChannel", "PySide6.QtWebSockets", "PySide6.QtNfc", "PySide6.QtSpatialAudio",
]
# 桌面端不需要 Web 服务栈
EXCLUDED_OTHER = ["fastapi", "starlette", "uvicorn", "pytest", "respx", "ruff"]

a = Analysis(
    [ENTRY],
    pathex=["src"],
    binaries=[],
    datas=[],
    hiddenimports=[
        # pydantic v2 / pydantic-settings 的动态导入
        "pydantic.deprecated.decorator",
        "pydantic_settings",
        # Pillow 插件按需加载，显式收进常用格式
        "PIL.PngImagePlugin", "PIL.JpegImagePlugin", "PIL.WebPImagePlugin",
        "PIL.BmpImagePlugin", "PIL.GifImagePlugin",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=EXCLUDED_QT + EXCLUDED_OTHER,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    strip=False,
    upx=False,
    console=False,          # GUI 应用，不带终端窗口
    icon=None,              # 需要图标时放 assets/icon.icns / icon.ico 并在此引用
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=False, name=APP_NAME,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier="cn.novacanvas.desktop",
        info_plist={
            "CFBundleDisplayName": "NovaCanvas 图片工作台",
            "CFBundleShortVersionString": "0.1.0",
            "NSHighResolutionCapable": True,
            # API 走 HTTPS，无需配置 NSAppTransportSecurity 例外
        },
    )
