# NovaCanvas 常用命令。运行 `make` 或 `make help` 查看列表。
.DEFAULT_GOAL := help
SHELL := /bin/bash

UV      ?= uv
PORT    ?= 8000
HOST    ?= 127.0.0.1
export VIRTUAL_ENV :=   # 避免 pyenv 等外部 VIRTUAL_ENV 干扰 uv

.PHONY: help install sync dev desktop serve test test-desktop lint fmt check \
        build build-clean clean clean-all env

help: ## 显示所有命令
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ---- 依赖 ----------------------------------------------------------------------

install: ## 安装全部依赖（含 dev 组）
	$(UV) sync --all-groups

sync: install ## install 的别名

env: ## 生成 .env（若不存在）
	@test -f .env || cp .env.example .env
	@echo "请编辑 .env 填入 SENSENOVA_API_KEY"

# ---- 运行 ----------------------------------------------------------------------

desktop: ## 启动桌面端（PySide6）
	$(UV) run nova-canvas-desktop

dev: ## 启动后端（热重载）
	$(UV) run uvicorn nova_canvas.main:app --reload --host $(HOST) --port $(PORT)

serve: ## 启动后端（生产模式）
	$(UV) run nova-canvas

# ---- 质量 ----------------------------------------------------------------------

test: ## 运行全部测试
	QT_QPA_PLATFORM=offscreen $(UV) run pytest -q

test-desktop: ## 仅运行桌面端测试
	QT_QPA_PLATFORM=offscreen $(UV) run pytest -q tests/test_desktop.py

lint: ## ruff 静态检查
	$(UV) run ruff check src tests

fmt: ## ruff 自动修复 + 格式化
	$(UV) run ruff check --fix src tests
	$(UV) run ruff format src tests

check: lint test ## lint + test

# ---- 打包 ----------------------------------------------------------------------

build: ## PyInstaller 打包桌面端到 dist/
	$(UV) run pyinstaller --noconfirm nova-canvas.spec
	@echo "产物: dist/NovaCanvas$(shell [ "$$(uname)" = Darwin ] && echo ' 与 dist/NovaCanvas.app')"

build-clean: build-artifacts-clean build ## 清理后重新打包

build-artifacts-clean:
	rm -rf build dist

# ---- 清理 ----------------------------------------------------------------------

clean: build-artifacts-clean ## 清理构建产物与缓存
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache \) -prune -exec rm -rf {} +

clean-all: clean ## 额外删除 .venv 与 output/
	rm -rf .venv output
