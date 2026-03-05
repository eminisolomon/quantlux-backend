"""Drawdown protection: daily/total limits, auto-halt on breach."""

import json
from datetime import datetime

from app.utils.logger import logger
from app.core.redis_client import redis_client


class DrawdownManager:
    def __init__(
        self,
        max_daily_dd_pct: float = 5.0,
        max_total_dd_pct: float = 15.0,
        warning_threshold_pct: float = 75.0,  # % of limit before warning
        account_id: str = "default",
    ):
        self.max_daily_dd = max_daily_dd_pct
        self.max_total_dd = max_total_dd_pct
        self.warning_threshold = warning_threshold_pct / 100.0
        self.account_id = account_id

        self.key_ns = f"quantlux:drawdown:{account_id}"

        logger.info(
            f"DrawdownManager initialized: Daily={max_daily_dd_pct}%, Total={max_total_dd_pct}%"
        )

    async def _get_state(self) -> dict:
        redis = redis_client.redis
        state_str = await redis.get(f"{self.key_ns}:state")
        if state_str:
            return json.loads(state_str)
        return {
            "daily_start_equity": 0.0,
            "peak_equity": 0.0,
            "is_halted": False,
            "halt_reason": "",
            "last_reset_date": datetime.now().date().isoformat(),
        }

    async def _save_state(self, state: dict):
        redis = redis_client.redis
        await redis.set(f"{self.key_ns}:state", json.dumps(state))

    async def initialize(self, starting_equity: float):
        state = await self._get_state()
        if state["peak_equity"] == 0.0:
            state["daily_start_equity"] = starting_equity
            state["peak_equity"] = starting_equity
            await self._save_state(state)
            logger.info(
                f"Drawdown manager initialized with equity: ${starting_equity:.2f}"
            )
        else:
            logger.info(
                f"Drawdown manager state loaded from Redis. Peak: ${state['peak_equity']:.2f}"
            )

    async def reset_daily(self, current_equity: float):
        state = await self._get_state()
        state["daily_start_equity"] = current_equity
        state["last_reset_date"] = datetime.now().date().isoformat()
        await self._save_state(state)
        logger.debug(f"Daily drawdown reset. Starting equity: ${current_equity:.2f}")

    async def update_peak(self, current_equity: float):
        state = await self._get_state()
        if current_equity > state["peak_equity"]:
            old_peak = state["peak_equity"]
            state["peak_equity"] = current_equity
            await self._save_state(state)
            logger.info(f"🎉 New equity peak! ${old_peak:.2f} → ${current_equity:.2f}")

    async def check_drawdown_limits(self, current_equity: float) -> dict:
        state = await self._get_state()
        current_date = datetime.now().date()
        last_reset_date = datetime.fromisoformat(state["last_reset_date"]).date()

        if current_date > last_reset_date:
            state["daily_start_equity"] = current_equity
            state["last_reset_date"] = current_date.isoformat()
            await self._save_state(state)
            logger.debug(
                f"Daily drawdown reset. Starting equity: ${current_equity:.2f}"
            )

        # update peak in current flow
        if current_equity > state["peak_equity"]:
            old_peak = state["peak_equity"]
            state["peak_equity"] = current_equity
            await self._save_state(state)
            logger.info(f"🎉 New equity peak! ${old_peak:.2f} → ${current_equity:.2f}")

        daily_start_equity = state["daily_start_equity"]
        peak_equity = state["peak_equity"]

        if daily_start_equity > 0:
            daily_dd = (
                (daily_start_equity - current_equity) / daily_start_equity
            ) * 100
        else:
            daily_dd = 0.0

        if peak_equity > 0:
            total_dd = ((peak_equity - current_equity) / peak_equity) * 100
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
            state["is_halted"] = True
            state["halt_reason"] = f"Daily drawdown limit breached: {daily_dd:.2f}%"
            await self._save_state(state)
            status["halt_trading"] = True
            logger.critical(f"🛑 TRADING HALTED: {state['halt_reason']}")

        elif total_dd >= self.max_total_dd:
            state["is_halted"] = True
            state["halt_reason"] = f"Total drawdown limit breached: {total_dd:.2f}%"
            await self._save_state(state)
            status["halt_trading"] = True
            logger.critical(f"🛑 TRADING HALTED: {state['halt_reason']}")

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

    async def is_trading_allowed(self) -> tuple[bool, str]:
        state = await self._get_state()
        return not state["is_halted"], state["halt_reason"]

    async def reset_halt(self):
        logger.warning("⚠️ Manually resetting drawdown halt")
        state = await self._get_state()
        state["is_halted"] = False
        state["halt_reason"] = ""
        await self._save_state(state)

    async def get_status_summary(self, current_equity: float) -> str:
        status = await self.check_drawdown_limits(current_equity)
        state = await self._get_state()

        summary = f"""
📊 Drawdown Status

Daily DD: {status["daily_dd"]:.2f}% (Limit: {self.max_daily_dd}%)
Total DD: {status["total_dd"]:.2f}% (Limit: {self.max_total_dd}%)

Peak Equity: ${state.get('peak_equity', 0):.2f}
Current: ${current_equity:.2f}
Daily Start: ${state.get('daily_start_equity', 0):.2f}

Trading: {"🛑 HALTED" if status["halt_trading"] else "✅ ALLOWED"}
        """.strip()

        if status["warning"]:
            summary += f"\n\n{status['warning']}"

        return summary
