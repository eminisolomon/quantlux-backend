"""
QuantLux Trading Bot - Main Entry Point

This module orchestrates the initialization, execution, and graceful shutdown
of the QuantLux trading bot, including engine services, AI risk guards,
and Telegram interface.
"""

import asyncio
import signal
import sys

from app.core import logger
from app.core import messages as msg
from app.engine.bot import TradingBot
from app.engine.lifecycle import (
    init_ai_services,
    init_engine_services,
    init_telegram_interface,
    init_trading_logic,
    synchronize_state,
)
from app.engine.queue import order_queue
from app.telegram.bot import TelegramBot


async def setup_signals(stop_event: asyncio.Event):
    """
    Register SIGINT and SIGTERM handlers to facilitate a graceful shutdown.

    Args:
        stop_event: An asyncio Event that will be set when a shutdown signal is intercepted.
    """
    loop = asyncio.get_running_loop()

    def signal_handler():
        logger.info(msg.SHUTDOWN_SIGNAL)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)


def setup_bot_callbacks(
    trading_bot: TradingBot, telegram_bot: TelegramBot, loop: asyncio.AbstractEventLoop
):
    """
    Establish communication bridges between the trading engine and the Telegram interface.

    Args:
        trading_bot: The core trading engine instance.
        telegram_bot: The Telegram interface instance.
        loop: The primary asyncio event loop.
    """

    def notify_telegram(message: str):
        if telegram_bot.application:
            asyncio.run_coroutine_threadsafe(telegram_bot.send_message(message), loop)

    trading_bot.register_notification_callback(notify_telegram)


async def main():
    """
    Main application loop: initializes infrastructure, starts services,
    and handles graceful termination.
    """
    try:
        # --- INFRASTRUCTURE SETUP ---
        # Initialize brokers, managers, and data feed handlers.
        (
            symbol_manager,
            correlation_manager,
            news_manager,
            broker,
        ) = await init_engine_services()

        # Connect the asynchronous order queue to the broker.
        order_queue.initialize(broker)

        # --- AI & LOGIC INITIALIZATION ---
        gemini = init_ai_services()

        # Set up the core trading logic, risk management, and drawdown monitoring.
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

        # --- INTERFACE SETUP ---
        # Initialize the Telegram bot as the primary user interface.
        telegram_bot = await init_telegram_interface(
            trading_bot,
            tracker,
            drawdown_manager,
            broker,
            gemini=gemini,
        )

        # --- STATE SYNCHRONIZATION ---
        # Ensure the local bot state matches the live broker account state.
        await synchronize_state(broker, drawdown_manager, tracker)

        # --- START SERVICES ---
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        await setup_signals(stop_event)
        setup_bot_callbacks(trading_bot, telegram_bot, loop)

        # Launch background tasks and service loops.
        await order_queue.start()
        await trading_bot.start()
        await telegram_bot.start()

        logger.success(msg.RUNNING_MESSAGE)

        # --- EXECUTION ---
        # Wait indefinitely until a shutdown signal (Ctrl+C) is received.
        await stop_event.wait()

        # --- GRACEFUL SHUTDOWN ---
        logger.info(msg.SHUTDOWN_START)
        await order_queue.stop()
        await telegram_bot.stop()
        await trading_bot.stop()
        await broker.shutdown()
        logger.info(msg.SHUTDOWN_COMPLETE_GOODBYE)

    except Exception as e:
        logger.error(msg.FATAL_ERROR.format(error=e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
