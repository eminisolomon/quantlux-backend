"""Interactive keyboard utilities for Telegram bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class KeyboardBuilder:
    """Build inline keyboards for Telegram."""

    @staticmethod
    def create_main_menu() -> InlineKeyboardMarkup:
        """Create main menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("💰 Balance", callback_data="balance"),
            ],
            [
                InlineKeyboardButton("📈 Positions", callback_data="positions"),
                InlineKeyboardButton("⏳ Orders", callback_data="orders"),
            ],
            [
                InlineKeyboardButton("📉 Performance", callback_data="performance"),
                InlineKeyboardButton("⚠️ Risk", callback_data="risk"),
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh"),
                InlineKeyboardButton("❌ Close", callback_data="close"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_refresh_button() -> InlineKeyboardMarkup:
        """Create simple refresh button."""
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_current")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_status_keyboard() -> InlineKeyboardMarkup:
        """Create keyboard for status view."""
        keyboard = [
            [
                InlineKeyboardButton("💰 Balance", callback_data="balance"),
                InlineKeyboardButton("📈 Positions", callback_data="positions"),
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="status"),
                InlineKeyboardButton("🏠 Menu", callback_data="menu"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_positions_keyboard() -> InlineKeyboardMarkup:
        """Create keyboard for positions view."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("💰 Balance", callback_data="balance"),
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="positions"),
                InlineKeyboardButton("🏠 Menu", callback_data="menu"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_performance_keyboard() -> InlineKeyboardMarkup:
        """Create keyboard for performance view."""
        keyboard = [
            [
                InlineKeyboardButton("Today", callback_data="perf_today"),
                InlineKeyboardButton("Week", callback_data="perf_week"),
                InlineKeyboardButton("Month", callback_data="perf_month"),
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="performance"),
                InlineKeyboardButton("🏠 Menu", callback_data="menu"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_risk_keyboard() -> InlineKeyboardMarkup:
        """Create keyboard for risk view."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("📈 Positions", callback_data="positions"),
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="risk"),
                InlineKeyboardButton("🏠 Menu", callback_data="menu"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_custom(
        buttons: list[tuple[str, str]], columns: int = 2
    ) -> InlineKeyboardMarkup:
        """Create custom keyboard layout."""
        keyboard = []
        row = []

        for i, (text, callback) in enumerate(buttons):
            row.append(InlineKeyboardButton(text, callback_data=callback))
            if (i + 1) % columns == 0:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        return InlineKeyboardMarkup(keyboard)
