"""Drawdown protection: daily/total limits, auto-halt on breach."""

from datetime import datetime

from app.utils.logger import logger


class DrawdownManager:
    def __init__(
        self,
        max_daily_dd_pct: float = 5.0,
        max_total_dd_pct: float = 15.0,
        warning_threshold_pct: float = 75.0,  # % of limit before warning
    ):
        self.max_daily_dd = max_daily_dd_pct
        self.max_total_dd = max_total_dd_pct
        self.warning_threshold = warning_threshold_pct / 100.0

        self.daily_start_equity: float = 0.0
        self.peak_equity: float = 0.0
        self.is_halted: bool = False
        self.halt_reason: str = ""

        self.last_reset_date: datetime = datetime.now().date()

        logger.info(
            f"DrawdownManager initialized: Daily={max_daily_dd_pct}%, Total={max_total_dd_pct}%"
        )

    def initialize(self, starting_equity: float):
        self.daily_start_equity = starting_equity
        self.peak_equity = starting_equity
        logger.info(f"Drawdown manager initialized with equity: ${starting_equity:.2f}")

    def reset_daily(self, current_equity: float):
        self.daily_start_equity = current_equity
        self.last_reset_date = datetime.now().date()
        logger.debug(f"Daily drawdown reset. Starting equity: ${current_equity:.2f}")

    def update_peak(self, current_equity: float):
        if current_equity > self.peak_equity:
            old_peak = self.peak_equity
            self.peak_equity = current_equity
            logger.info(f"🎉 New equity peak! ${old_peak:.2f} → ${current_equity:.2f}")

    def check_drawdown_limits(self, current_equity: float) -> dict:
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.reset_daily(current_equity)

        self.update_peak(current_equity)

        if self.daily_start_equity > 0:
            daily_dd = (
                (self.daily_start_equity - current_equity) / self.daily_start_equity
            ) * 100
        else:
            daily_dd = 0.0

        if self.peak_equity > 0:
            total_dd = ((self.peak_equity - current_equity) / self.peak_equity) * 100
        else:
            total_dd = 0.0

        status = {
            "daily_dd": daily_dd,
            "total_dd": total_dd,
            "halt_trading": False,
            "reduce_position_size": False,
            "warning": "",
        }

        if daily_dd >= self.max_daily_dd:
            self.is_halted = True
            self.halt_reason = f"Daily drawdown limit breached: {daily_dd:.2f}%"
            status["halt_trading"] = True
            logger.critical(f"🛑 TRADING HALTED: {self.halt_reason}")

        elif total_dd >= self.max_total_dd:
            self.is_halted = True
            self.halt_reason = f"Total drawdown limit breached: {total_dd:.2f}%"
            status["halt_trading"] = True
            logger.critical(f"🛑 TRADING HALTED: {self.halt_reason}")

        elif daily_dd >= (self.max_daily_dd * self.warning_threshold):
            status["reduce_position_size"] = True
            pct_of_limit = (daily_dd / self.max_daily_dd) * 100
            status["warning"] = (
                f"⚠️ Daily DD at {pct_of_limit:.0f}% of limit ({daily_dd:.2f}%)"
            )
            logger.warning(status["warning"])

        elif total_dd >= (self.max_total_dd * self.warning_threshold):
            status["reduce_position_size"] = True
            pct_of_limit = (total_dd / self.max_total_dd) * 100
            status["warning"] = (
                f"⚠️ Total DD at {pct_of_limit:.0f}% of limit ({total_dd:.2f}%)"
            )
            logger.warning(status["warning"])

        return status

    def is_trading_allowed(self) -> bool:
        return not self.is_halted

    def reset_halt(self):
        logger.warning("⚠️ Manually resetting drawdown halt")
        self.is_halted = False
        self.halt_reason = ""

    def get_status_summary(self, current_equity: float) -> str:
        status = self.check_drawdown_limits(current_equity)

        summary = f"""
📊 Drawdown Status

Daily DD: {status["daily_dd"]:.2f}% (Limit: {self.max_daily_dd}%)
Total DD: {status["total_dd"]:.2f}% (Limit: {self.max_total_dd}%)

Peak Equity: ${self.peak_equity:.2f}
Current: ${current_equity:.2f}
Daily Start: ${self.daily_start_equity:.2f}

Trading: {"🛑 HALTED" if status["halt_trading"] else "✅ ALLOWED"}
        """.strip()

        if status["warning"]:
            summary += f"\n\n{status['warning']}"

        return summary
