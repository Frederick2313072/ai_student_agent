# 费曼学习系统 Makefile - 开发和部署命令
# 支持uv和pip两种包管理方式，提供配置管理和监控功能

.PHONY: help install run test lint clean dev-setup config-check celery-worker celery-flower celery-status

help: ## 显示帮助信息
	@echo "🎓 费曼学习系统 - 可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# === 依赖管理 ===

install: ## 安装依赖 (推荐使用uv)
	uv sync

install-pip: ## 安装依赖 (使用pip)
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# === 应用运行 ===

run: ## 启动应用
	uv run python run_app.py

run-pip: ## 启动应用 (使用pip)
	python run_app.py

run-ui: ## 启动Streamlit界面
	uv run streamlit run src/feynman/interfaces/web/streamlit_ui.py

dev-start: ## 启动开发环境（含配置检查）
	uv run python scripts/dev_helper.py check
	uv run python run_app.py

# === Celery 任务队列 ===

celery-worker: ## 启动Celery Worker
	./scripts/celery_worker.sh

celery-worker-dev: ## 启动Celery Worker (调试模式)
	uv run python scripts/start_celery_worker.py --loglevel debug --workers 1

celery-flower: ## 启动Flower监控面板
	uv run python scripts/start_flower.py

celery-status: ## 查看Celery状态
	uv run celery -A feynman.tasks.celery_app.celery_app status

celery-purge: ## 清空所有队列
	uv run celery -A feynman.tasks.celery_app.celery_app purge

celery-inspect: ## 检查活跃任务
	uv run celery -A feynman.tasks.celery_app.celery_app inspect active

# === 配置管理 ===

config-check: ## 验证当前配置
	uv run python scripts/config_validator.py

config-setup: ## 交互式配置设置
	uv run python scripts/setup_env.py --interactive

config-minimal: ## 创建最小配置模板
	uv run python scripts/setup_env.py --type minimal --output environments/minimal.env

config-dev: ## 创建开发环境配置
	uv run python scripts/setup_env.py --type development --output environments/development.env

config-prod: ## 创建生产环境配置
	uv run python scripts/setup_env.py --type production --output environments/production.env

# === 测试和质量 ===

test: ## 运行测试
	uv run pytest tests/ -v

test-unit: ## 运行单元测试
	uv run pytest tests/unit/ -v

test-integration: ## 运行集成测试
	uv run pytest tests/integration/ -v

lint: ## 代码检查
	uv run python scripts/dev_helper.py lint

format: ## 代码格式化
	uv run black src/ tests/
	uv run isort src/ tests/

# === 开发辅助 ===

dev-setup: ## 完整开发环境设置
	@echo "🎓 设置费曼学习系统开发环境..."
	uv sync
	uv run python scripts/config_validator.py
	@echo "🎉 开发环境设置完成！运行 'make run' 启动应用"

dev-check: ## 开发环境全面检查
	uv run python scripts/dev_helper.py all

clean: ## 清理缓存文件
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/

# === 监控和部署 ===

monitoring-up: ## 启动监控栈
	docker-compose -f config/docker-compose.monitoring.yml up -d
	@echo "📊 监控面板访问:"
	@echo "  Grafana: http://localhost:3000 (admin/admin)"
	@echo "  Prometheus: http://localhost:9090"

monitoring-down: ## 停止监控栈
	docker-compose -f config/docker-compose.monitoring.yml down

docker-build: ## 构建Docker镜像
	docker build -f deployment/docker/Dockerfile -t feynman-learning-system:latest .

docker-run: ## 运行Docker容器
	docker run -p 8000:8000 --env-file environments/production.env feynman-learning-system:latest

# === 快速开始 ===

quickstart: ## 快速开始（新用户推荐）
	@echo "🚀 费曼学习系统快速开始..."
	uv sync
	@echo "📝 创建开发配置..."
	uv run python scripts/setup_env.py --type development --output environments/local.env
	@echo "✅ 配置已创建！请编辑 environments/local.env 填写API密钥"
	@echo "然后运行: make run