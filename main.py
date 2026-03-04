"""QuantLux Trading Bot - Main Entry Point."""

import asyncio
import signal
import sys

from app.core import logger
from app.core import messages as msg
from app.engine.lifecycle import (
    init_ai_services,
    init_engine_services,
    init_trading_logic,
    synchronize_state,
)
from app.engine.queue import order_queue


async def setup_signals(stop_event: asyncio.Event):
    """Register SIGINT/SIGTERM handlers for graceful shutdown."""
    loop = asyncio.get_running_loop()

    def signal_handler():
        logger.info(msg.SHUTDOWN_SIGNAL)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)


async def main():
    """Initialize infrastructure, start services, wait for shutdown."""
    try:
        (
            symbol_manager,
            correlation_manager,
            news_manager,
            broker,
        ) = await init_engine_services()

        order_queue.initialize(broker)
        gemini = init_ai_services()

        (
            drawdown_manager,
            tracker,
            risk_manager,
            trading_bot,
        ) = await init_trading_logic(
            symbol_manager,
            correlation_manager,
            news_manager,
            broker,
            gemini=gemini,
        )

        await synchronize_state(broker, drawdown_manager, tracker)

        stop_event = asyncio.Event()
        await setup_signals(stop_event)

        await order_queue.start()
        await trading_bot.start()

        logger.success(msg.RUNNING_MESSAGE)
        await stop_event.wait()

        logger.info(msg.SHUTDOWN_START)
        await order_queue.stop()
        await trading_bot.stop()
        await broker.shutdown()
        logger.info(msg.SHUTDOWN_COMPLETE_GOODBYE)

    except Exception as e:
        logger.error(msg.FATAL_ERROR.format(error=e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
