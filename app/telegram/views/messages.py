"""Telegram-specific view messages. Imports from core.messages where possible."""

from app.core import messages as msg


def get_welcome_message() -> str:
    """Get the welcome message for /start command."""
    return msg.WELCOME


def get_help_message() -> str:
    """Generate help message with available commands."""
    return msg.HELP


def get_error_message(error: str) -> str:
    """Get error message."""
    return f"❌ Error: {error}"
