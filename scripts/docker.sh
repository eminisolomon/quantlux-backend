#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# QuantLux Docker Entrypoint
# 1. Launch the trading bot
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

YELLOW='\033[1;33m'
NC='\033[0m'

# ── 1. Start the Bot ──────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/1] Launching QuantLux Trading Bot...${NC}"
echo "────────────────────────────────────────────"

exec python -m app.main
