# PREMONITION Makefile
# Works on Linux/macOS and Windows (with GNU Make installed).
# Windows alternative: use scripts/setup.ps1

.PHONY: help setup install install-dev test train explain api frontend frontend-dev frontend-test frontend-build clean docker-build docker-train docker-explain docker-api backup lint

PYTHON ?= python
PIP    ?= pip

help: ## Show available commands
	@echo "PREMONITION — available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup: install-dev env ## One-command project setup (install + create .env)
	@echo "Setup complete. Run: make train"

install: ## Install production dependencies
	$(PIP) install -r requirements.txt

install-dev: ## Install dev dependencies (includes production)
	$(PIP) install -r requirements-dev.txt

env: ## Create .env from template (skips if exists)
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env"; else echo ".env already exists"; fi

test: ## Run all tests
	$(PYTHON) -m pytest tests/ -v

test-cov: ## Run tests with coverage report
	$(PYTHON) -m pytest tests/ -v --cov=premonition --cov-report=term-missing

train: ## Train all models (tier t1)
	$(PYTHON) scripts/train.py --tier t1

train-t0: ## Train with demographics-only tier
	$(PYTHON) scripts/train.py --tier t0

train-t2: ## Train with labs tier
	$(PYTHON) scripts/train.py --tier t2

explain: ## Generate SHAP explanations
	$(PYTHON) scripts/explain.py --n-samples 5

api: ## Start FastAPI server
	$(PYTHON) scripts/run_api.py

frontend: ## Start React dev server (requires: cd frontend && npm install)
	cd frontend && npm run dev

frontend-dev: frontend ## Alias for frontend dev server

frontend-test: ## Run frontend tests
	cd frontend && npm test

frontend-build: ## Build frontend for production
	cd frontend && npm run build

lint: ## Run ruff linter
	ruff check src/ tests/ scripts/

clean: ## Remove caches and temp files
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

docker-build: ## Build Docker image
	docker compose build

docker-train: ## Train models inside Docker
	docker compose run --rm premonition-ml train

docker-explain: ## Generate explanations inside Docker
	docker compose run --rm premonition-ml explain

docker-test: ## Run tests inside Docker
	docker compose run --rm premonition-ml test

docker-api: ## Start API server in Docker
	docker compose up premonition-api

backup: ## Create backup of models, logs, and reports
	bash scripts/backup.sh
