from app.risk.drawdown import DrawdownManager


def test_initialization():
    manager = DrawdownManager(
        max_daily_dd_pct=5.0, max_total_dd_pct=15.0, warning_threshold_pct=75.0
    )
    assert manager.max_daily_dd == 5.0
    assert manager.max_total_dd == 15.0
    assert manager.warning_threshold == 0.75

    manager.initialize(starting_equity=10000.0)
    assert manager.daily_start_equity == 10000.0
    assert manager.peak_equity == 10000.0
    assert manager.is_trading_allowed() is True


def test_check_drawdown_limits_no_breach():
    manager = DrawdownManager()
    manager.initialize(10000.0)

    status = manager.check_drawdown_limits(9800.0)  # 2% dropdown
    assert status["halt_trading"] is False
    assert status["reduce_position_size"] is False
    assert status["warning"] == ""


def test_check_drawdown_limits_warning():
    manager = DrawdownManager(
        max_daily_dd_pct=10.0, warning_threshold_pct=80.0
    )  # warning at 8%
    manager.initialize(10000.0)

    status = manager.check_drawdown_limits(9100.0)  # 9% drop
    assert status["halt_trading"] is False
    assert status["reduce_position_size"] is True
    assert "⚠️ Daily DD at 90% of limit" in status["warning"]


def test_check_drawdown_limits_halt_daily():
    manager = DrawdownManager(max_daily_dd_pct=5.0)
    manager.initialize(10000.0)

    status = manager.check_drawdown_limits(9400.0)  # 6% drop
    assert status["halt_trading"] is True
    assert manager.is_trading_allowed() is False
    assert manager.is_halted is True


def test_check_drawdown_limits_halt_total():
    manager = DrawdownManager(max_daily_dd_pct=100.0, max_total_dd_pct=15.0)
    manager.initialize(10000.0)
    manager.update_peak(12000.0)

    status = manager.check_drawdown_limits(
        10000.0
    )  # 2000 / 12000 = 16.6% drop from peak
    assert status["halt_trading"] is True
    assert manager.is_halted is True


def test_update_peak():
    manager = DrawdownManager()
    manager.initialize(10000.0)
    manager.update_peak(11000.0)
    assert manager.peak_equity == 11000.0

    manager.update_peak(10500.0)
    assert manager.peak_equity == 11000.0  # peak doesn't decrease


def test_reset_daily():
    manager = DrawdownManager(max_daily_dd_pct=5.0)
    manager.initialize(10000.0)

    # Simulate being in red initially
    manager.check_drawdown_limits(9600.0)  # 4% drop

    # Force reset
    manager.reset_daily(9600.0)
    assert manager.daily_start_equity == 9600.0

    status = manager.check_drawdown_limits(9600.0)
    assert status["daily_dd"] == 0.0
