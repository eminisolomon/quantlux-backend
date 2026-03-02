#!/bin/bash
# QuantLux Trading Bot Startup Script

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

banner() {
    echo -e "${BLUE}"
    echo "   ____                   __  __               "
    echo "  / __ \__  ______ _____ / /_/ /   __  ___  __"
    echo " / / / / / / / __ \`/ __ \/ __/ /   / / / / |/_/"
    echo "/ /_/ / /_/ / /_/ / / / / /_/ /___/ /_/ />  <  "
    echo "\___\_\__,_/\__,_/_/ /_/\__/_____/\__,_/_/|_|  "
    echo -e "${NC}"
    echo -e "${BLUE}Starting QuantLux Trading Environment...${NC}"
    echo "----------------------------------------"
}

check_env() {
    echo -e "${YELLOW}[1/2] Checking Environment...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    fi
    PYTHON_VER=$(python --version 2>&1)
    echo "Using: $PYTHON_VER"
}

validate() {
    echo -e "${YELLOW}[2/2] Validating Configuration...${NC}"
    python -c "from app.core.settings import settings; print(f'✓ Loaded settings for env: {settings.TRADING_ENV}')" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Configuration valid${NC}"
    else
        echo -e "${RED}✗ Configuration error${NC}"
        exit 1
    fi
}

run() {
    echo -e "${YELLOW}🚀 Launching Trading Bot...${NC}"
    echo "----------------------------------------"
    echo -e "${GREEN}Logs will appear below:${NC}"
    echo ""
    python main.py
}

news() {
    echo -e "${YELLOW}[News] Fetching Economic Calendar...${NC}"
    python -m news.calendar
}

# Run specific function if provided as argument
if [ $# -eq 1 ]; then
    if declare -f "$1" > /dev/null; then
        "$1"
        exit $?
    else
        echo -e "${RED}Error: Function '$1' not found.${NC}"
        echo "Available functions: banner, check_env, validate, run, news"
        exit 1
    fi
fi

# Default: Run full sequence
banner
check_env
validate
run
