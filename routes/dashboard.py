from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List, Optional
from app.core import settings

router = APIRouter(tags=["dashboard"])


class SystemStatus(BaseModel):
    is_online: bool
    active_strategies: int
    data_feeds_ok: bool


class PerformanceMetrics(BaseModel):
    total_equity: float
    win_rate: float
    profit_factor: float
    active_trades_count: int
    daily_return_pct: float


@router.get("/status", response_model=SystemStatus)
async def get_system_status(request: Request):
    trading_bot = getattr(request.app.state, "trading_bot", None)
    health_monitor = getattr(request.app.state, "health_monitor", None)

    is_online = health_monitor.is_running if health_monitor else False
    active_strategies = (
        len(trading_bot.strategies.strategies)
        if trading_bot and trading_bot.strategies
        else 0
    )
    data_feeds_ok = health_monitor.is_running if health_monitor else False

    return SystemStatus(
        is_online=is_online,
        active_strategies=active_strategies,
        data_feeds_ok=data_feeds_ok,
    )


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(request: Request):
    tracker = getattr(request.app.state, "tracker", None)
    trading_bot = getattr(request.app.state, "trading_bot", None)

    report = tracker.generate_performance_report() if tracker else None

    active_trades_count = 0
    if trading_bot and trading_bot.trade_executor:
        try:
            positions = await trading_bot.trade_executor.get_positions()
            for pos in positions:
                magic = getattr(pos, "magic", None) or (
                    isinstance(pos, dict) and pos.get("magic")
                )
                if magic == settings.MAGIC_NUMBER:
                    active_trades_count += 1
        except Exception:
            pass

    return PerformanceMetrics(
        total_equity=report.current_equity if report else 0.0,
        win_rate=report.win_rate if report else 0.0,
        profit_factor=report.profit_factor if report else 0.0,
        active_trades_count=active_trades_count,
        daily_return_pct=report.roi if report else 0.0,
    )
