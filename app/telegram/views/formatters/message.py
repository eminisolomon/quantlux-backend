"""Message formatting utilities for Telegram bot."""

from app.core import messages
from app.core.enums import SignalAction


class MessageFormatter:
    """Format Telegram messages with rich styling."""

    @staticmethod
    def format_currency(amount: float, currency: str = "USD", decimals: int = 2) -> str:
        """Format currency with proper symbols."""
        symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}
        symbol = symbols.get(currency, currency)
        return f"{symbol}{amount:,.{decimals}f}"

    @staticmethod
    def format_percentage(
        value: float, decimals: int = 2, show_sign: bool = True
    ) -> str:
        """Format percentage with color indicator."""
        sign = "+" if value > 0 and show_sign else ""
        indicator = (
            messages.SYM_HEALTHY
            if value > 0
            else messages.SYM_DANGER if value < 0 else messages.SYM_NEUTRAL
        )
        return f"{sign}{value:.{decimals}f}% {indicator}"

    @staticmethod
    def format_pnl(pnl: float, currency: str = "USD") -> str:
        """Format P&L with color and sign."""
        indicator = messages.SYM_SUCCESS if pnl >= 0 else messages.SYM_ERROR
        sign = "+" if pnl > 0 else ""
        formatted = MessageFormatter.format_currency(abs(pnl), currency)
        return f"{sign}{formatted} {indicator}"

    @staticmethod
    def create_box(title: str, content: list[str], width: int = 24) -> str:
        """Create a box with title and content."""
        lines = []
        title_line = f" {title} "
        padding = (width - len(title_line)) // 2
        lines.append(f"┏{'━' * padding}{title_line}{'━' * padding}┓")

        for line in content:
            # Pad line to width
            padded = line.ljust(width - 2)
            lines.append(f"┃ {padded}┃")

        lines.append(f"┗{'━' * width}┛")
        return "\n".join(lines)

    @staticmethod
    def create_list_item(label: str, value: str, width: int = 20) -> str:
        """Create a formatted list item."""
        padding = width - len(label)
        return f"├─ {label}: {' ' * max(0, padding - 2)}{value}"

    @staticmethod
    def create_header(text: str, emoji: str = messages.SYM_CHART) -> str:
        """Create a formatted header."""
        return f"{emoji} *{text.upper()}*"

    @staticmethod
    def format_status_box(
        connected: bool,
        balance: float,
        equity: float,
        currency: str = "USD",
        auto_trading: bool = False,
    ) -> str:
        """Format account status as a styled box."""
        pnl = equity - balance
        pnl_pct = (pnl / balance * 100) if balance > 0 else 0

        content = [
            f"Balance  {MessageFormatter.format_currency(balance, currency)}",
            f"Equity   {MessageFormatter.format_currency(equity, currency)}",
            f"P&L      {MessageFormatter.format_pnl(pnl, currency)}",
            f"Return   {MessageFormatter.format_percentage(pnl_pct)}",
            "",
            f"Trading  {messages.SYM_SUCCESS + ' ' + messages.LABEL_AUTO if auto_trading else messages.SYM_WARNING + '  ' + messages.LABEL_MANUAL}",
            f"Status   {messages.SYM_HEALTHY + ' ' + messages.LABEL_ONLINE if connected else messages.SYM_DANGER + ' ' + messages.LABEL_OFFLINE}",
        ]

        return MessageFormatter.create_box("ACCOUNT", content)

    @staticmethod
    def format_position_details(
        symbol: str,
        pos_type: str,
        volume: float,
        entry: float,
        current: float,
        pnl: float,
        currency: str = "USD",
    ) -> str:
        """Format position details."""
        is_buy = "BUY" in pos_type.upper()
        type_emoji = messages.SYM_HEALTHY if is_buy else messages.SYM_DANGER
        pips = current - entry if is_buy else entry - current
        pips_str = f"+{pips:.1f}" if pips > 0 else f"{pips:.1f}"

        lines = [
            f"{type_emoji} *{symbol}* • {pos_type}",
            MessageFormatter.create_list_item("Volume", f"{volume} lots"),
            MessageFormatter.create_list_item("Entry", f"{entry:.5f}"),
            MessageFormatter.create_list_item(
                "Current", f"{current:.5f} ({pips_str} pips)"
            ),
            MessageFormatter.create_list_item(
                "P&L", MessageFormatter.format_pnl(pnl, currency)
            ),
        ]

        return "\n".join(lines)

    @staticmethod
    def format_positions_summary(
        positions: list[dict],
        currency: str = "USD",
    ) -> str:
        """Format positions list with rich details."""
        if not positions:
            return "📋 *POSITIONS*\n\nNo open positions."

        lines = [MessageFormatter.create_header("POSITIONS", "📋"), ""]

        total_pnl = 0.0
        for pos in positions:
            symbol = pos.get("symbol", "N/A")
            pos_type = pos.get("type", "UNKNOWN")
            is_buy = "BUY" in pos_type.upper()
            type_str = SignalAction.BUY.value if is_buy else SignalAction.SELL.value
            volume = pos.get("volume", 0)
            entry = pos.get("openPrice", 0)
            current = pos.get("currentPrice", 0)
            pnl = pos.get("profit", 0)
            total_pnl += pnl

            formatted = MessageFormatter.format_position_details(
                symbol, type_str, volume, entry, current, pnl, currency
            )
            lines.append(formatted)
            lines.append("")

        lines.append("─" * 30)
        lines.append(
            f"💰 *Total P&L*: {MessageFormatter.format_pnl(total_pnl, currency)}"
        )

        return "\n".join(lines)

    @staticmethod
    def format_error(message: str) -> str:
        """Format error message."""
        return f"{messages.SYM_ERROR} *ERROR*\\n\\n{message}"

    @staticmethod
    def format_success(message: str) -> str:
        """Format success message."""
        return f"{messages.SYM_SUCCESS} *SUCCESS*\\n\\n{message}"

    @staticmethod
    def format_warning(message: str) -> str:
        """Format warning message."""
        return f"{messages.SYM_WARNING} *WARNING*\\n\\n{message}"
