.PHONY: all start banner check-env validate run install test clean \
        docker-build docker-up docker-down docker-logs docker-shell

# Default target
all: start

# Main startup
start:
	@chmod +x backend/scripts/start.sh
	@cd backend && ./scripts/start.sh

# Individual steps
banner:
	@cd backend && ./scripts/start.sh banner

check-env:
	@cd backend && ./scripts/start.sh check_env

validate:
	@cd backend && ./scripts/start.sh validate

run:
	@cd backend && ./scripts/start.sh run

# Utilities
install:
	uv pip install -r backend/requirements.txt


# Calendar
news:
	uv run -C backend -m app.integrations.forex_factory.calendar

# Testing
test:
	pytest backend/tests/

backtest:
	uv run -C backend -m scripts.backtest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# ── Docker Targets ────────────────────────────────────────────────────────────
docker-build:
	docker compose -f backend/docker-compose.yml build

docker-up:
	docker compose -f backend/docker-compose.yml up -d
	@echo "Run 'make docker-logs' to follow bot output."

docker-down:
	docker compose -f backend/docker-compose.yml down

docker-logs:
	docker compose -f backend/docker-compose.yml logs -f bot

docker-shell:
	docker compose -f backend/docker-compose.yml exec bot /bin/bash
