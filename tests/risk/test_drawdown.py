import pytest
import fakeredis.aioredis
from app.risk.drawdown import DrawdownManager
from app.core.redis_client import redis_client


@pytest.fixture(autouse=True)
async def mock_redis(monkeypatch):
    r = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr(redis_client, "_redis", r)
    yield r
    await r.flushall()


def test_initialization_sync():
    manager = DrawdownManager(
        max_daily_dd_pct=5.0, max_total_dd_pct=15.0, warning_threshold_pct=75.0
    )
    assert manager.max_daily_dd == 5.0
    assert manager.max_total_dd == 15.0
    assert manager.warning_threshold == 0.75


@pytest.mark.asyncio
async def test_initialization():
    manager = DrawdownManager()
    await manager.initialize(starting_equity=10000.0)
    state = await manager._get_state()
    assert state["daily_start_equity"] == 10000.0
    assert state["peak_equity"] == 10000.0
    allowed, _ = await manager.is_trading_allowed()
    assert allowed is True


@pytest.mark.asyncio
async def test_check_drawdown_limits_no_breach():
    manager = DrawdownManager()
    await manager.initialize(10000.0)

    status = await manager.check_drawdown_limits(9800.0)
    assert status["halt_trading"] is False
    assert status["reduce_position_size"] is False
    assert status["warning"] == ""


@pytest.mark.asyncio
async def test_check_drawdown_limits_warning():
    manager = DrawdownManager(max_daily_dd_pct=10.0, warning_threshold_pct=80.0)
    await manager.initialize(10000.0)

    status = await manager.check_drawdown_limits(9100.0)
    assert status["halt_trading"] is False
    assert status["reduce_position_size"] is True
    assert "Daily DD at" in status["warning"]


@pytest.mark.asyncio
async def test_check_drawdown_limits_halt_daily():
    manager = DrawdownManager(max_daily_dd_pct=5.0)
    await manager.initialize(10000.0)

    status = await manager.check_drawdown_limits(9400.0)
    assert status["halt_trading"] is True
    allowed, _ = await manager.is_trading_allowed()
    assert allowed is False


@pytest.mark.asyncio
async def test_check_drawdown_limits_halt_total():
    manager = DrawdownManager(max_daily_dd_pct=100.0, max_total_dd_pct=15.0)
    await manager.initialize(10000.0)

    # Manually update peak equity
    state = await manager._get_state()
    state["peak_equity"] = 12000.0
    await manager._save_state(state)

    status = await manager.check_drawdown_limits(10000.0)
    assert status["halt_trading"] is True
    allowed, _ = await manager.is_trading_allowed()
    assert allowed is False


@pytest.mark.asyncio
async def test_update_peak():
    manager = DrawdownManager()
    await manager.initialize(10000.0)
    await manager.update_peak(11000.0)
    state = await manager._get_state()
    assert state["peak_equity"] == 11000.0

    await manager.update_peak(10500.0)
    state = await manager._get_state()
    assert state["peak_equity"] == 11000.0


@pytest.mark.asyncio
async def test_reset_daily():
    manager = DrawdownManager(max_daily_dd_pct=5.0)
    await manager.initialize(10000.0)

    await manager.check_drawdown_limits(9600.0)

    await manager.reset_daily(9600.0)
    state = await manager._get_state()
    assert state["daily_start_equity"] == 9600.0

    status = await manager.check_drawdown_limits(9600.0)
    assert status["daily_dd"] == 0.0
