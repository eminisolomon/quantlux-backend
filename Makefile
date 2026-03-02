.PHONY: all start banner check-env validate run install test clean \
        docker-build docker-up docker-down docker-logs docker-shell

# Default target
all: start

# Main startup
start:
	@chmod +x scripts/start.sh
	@./scripts/start.sh

# Individual steps
banner:
	@./scripts/start.sh banner

check-env:
	@./scripts/start.sh check_env

validate:
	@./scripts/start.sh validate

run:
	@./scripts/start.sh run

# Utilities
install:
	uv pip install -r requirements.txt


# Calendar
news:
	uv run  -m app.integrations.forex_factory.calendar

# Testing
test:
	pytest tests/

backtest:
	uv run  -m scripts.backtest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# ── Docker Targets ────────────────────────────────────────────────────────────
docker-build:
	docker compose -f docker-compose.yml build

docker-up:
	docker compose -f docker-compose.yml up -d
	@echo "Run 'make docker-logs' to follow bot output."

docker-down:
	docker compose -f docker-compose.yml down

docker-logs:
	docker compose -f docker-compose.yml logs -f bot

docker-shell:
	docker compose -f docker-compose.yml exec bot /bin/bash
