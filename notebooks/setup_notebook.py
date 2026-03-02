import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(os.getcwd()).parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))


def init_env():
    """Initialize app environment for notebooks."""
    from dotenv import load_dotenv

    load_dotenv(project_root / ".env")

    from app.core.settings import settings
    from app.utils.logger import logger

    print("✅ QuantLux Environment Initialized")
    print(f"📍 Project Root: {project_root}")
    print(f"🤖 Trading Env: {settings.TRADING_ENV}")
    return settings, logger
