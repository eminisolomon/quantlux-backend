import asyncio
import json
import pytest
import fakeredis.aioredis
from copy import deepcopy

from app.core import settings
from app.core.enums import SignalAction
from app.core.redis_client import redis_client
from app.engine.queue import OrderQueue, OrderTask
from app.risk.drawdown import DrawdownManager
from app.schemas.signal import TradeSignal
from app.services.analytics_service import AnalyticsService
from app.schemas import Trade
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
async def mock_redis(monkeypatch):
    r = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr(redis_client, "_redis", r)
    yield r
    await r.flushall()


@pytest.mark.asyncio
async def test_order_queue_redis_push_pop(mock_redis):
    queue = OrderQueue()
    queue.queue_key = "test:queue"

    task = OrderTask(
        action=SignalAction.BUY, symbol="EURUSD", volume=1.0, comment="Test Trade"
    )
    await queue.enqueue_order(task)

    length = await mock_redis.llen(queue.queue_key)
    assert length == 1

    result = await mock_redis.blpop(queue.queue_key, timeout=1)
    assert result is not None
    _, data = result
    popped_task = OrderTask.from_dict(json.loads(data))

    assert popped_task.symbol == "EURUSD"
    assert popped_task.action == SignalAction.BUY


@pytest.mark.asyncio
async def test_drawdown_manager_sync(mock_redis):
    dm1 = DrawdownManager(account_id="test_account")
    dm2 = DrawdownManager(account_id="test_account")

    await dm1.initialize(10000.0)

    state = await dm1._get_state()
    state["peak_equity"] = 10500.0
    await dm1._save_state(state)

    await dm2.initialize(10000.0)

    state2 = await dm2._get_state()
    assert state2["peak_equity"] == 10500.0


@pytest.mark.asyncio
async def test_analytics_tracker_redis():
    tracker1 = AnalyticsService(account_id="test_acc", initial_balance=10000.0)
    tracker2 = AnalyticsService(account_id="test_acc", initial_balance=10000.0)

    trade = Trade(
        symbol="EURUSD",
        type="BUY",
        lot_size=1.0,
        open_price=1.1,
        close_price=1.11,
        profit=100.0,
        open_time=datetime.now(tz=timezone.utc),
        close_time=datetime.now(tz=timezone.utc),
    )

    await tracker1.add_trade(trade)

    await tracker2.initialize()

    assert len(tracker2.trades) == 1
    assert tracker2.trades[0].symbol == "EURUSD"
    assert tracker2.current_equity == 10100.0
