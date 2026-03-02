"""Centralized repository for all system messages and strings."""

# ─── System & Connectivity ──────────────────────────────────────────

CONNECT_SUCCESS = "✅ *Connected to MetaApi*\n\nAccount: {account_id}"
CONNECT_FAILED = "❌ Failed to connect to MetaApi. Check your credentials."
MT_NOT_CONNECTED = "❌ MetaApi Not Connected."
ACC_INFO_FAILED = "❌ Could not retrieve account info."
SERVICE_SYNC = "✅ Services synchronized with live equity: ${equity:.2f}"
LATENCY_WARNING = "⚠️ HIGH LATENCY: {operation} took {latency:.2f}ms"
APP_START = "🚀 Starting QuantLux Application"
AI_ENABLED = "✨ AI features enabled (Gemini)"
AI_DISABLED_KEY = "AI features disabled — set GEMINI_API_KEY to enable."
SYNC_FAILED = "⚠️ Could not sync with live account info; using default levels."
SYNC_ERROR = "⚠️ Sync error: {error}. Defaulting risk levels."
NOTIFY_ERROR = "❌ Notification error: {error}"
SHUTDOWN_SIGNAL = "Shutdown signal received"
RUNNING_MESSAGE = "QuantLux-FX is running! Press Ctrl+C to stop."
SHUTDOWN_START = "Initiating graceful shutdown..."
SHUTDOWN_COMPLETE_GOODBYE = "Shutdown complete. Goodbye!"
FATAL_ERROR = "Fatal application error: {error}"

AI_GUARD_BLOCKED = "🛡️ AI Risk Guard BLOCKED {action} {symbol}: {reason}"
AI_GUARD_APPROVED = "🛡️ AI Risk Guard APPROVED {action} {symbol} (risk: {level})"
AI_GUARD_ERROR = "⚠️ AI risk guard error: {error}"
AI_GUARD_DISABLED = "AI risk guard disabled via settings."
AI_GUARD_FAIL_OPEN = "AI guard error — proceeding with trade."
AI_GUARD_UNAVAILABLE = "AI guard unavailable — proceeding with trade."
AI_GUARD_EMPTY = "AI guard returned empty — proceeding with trade."

CORR_UPDATING = "Updating correlation matrix..."
CORR_UPDATED = "Correlation matrix updated."
CORR_UPDATE_FAILED = "❌ Failed to update correlations: {error}"
CORR_SYM_NOT_FOUND = "⚠️ Symbol {symbol} not in correlation matrix. Skipping check."
CORR_REJECT = "⚠️ Correlation Reject: {symbol} vs {other} ({corr:.2f} > {limit})"
BOT_START = "Bot starting..."
BOT_IDLE = "No strategies registered or symbols configured. DataFeed will be idle."
BOT_ACTIVE = "Trading Bot is active. Operating on {count} symbols."
BOT_STOPPING = "Bot shutdown starting..."
BOT_STOP_COMPLETE = "Bot shutdown complete."
BOT_CLEAR_POSITIONS = "Clearing symbol positions..."
EMERGENCY_CLOSE_COMPLETE = "Emergency close complete: {count} positions closed."
EMERGENCY_CLOSE_ERROR = "Critical error during emergency close: {error}"
BOT_TICK_ERROR = "Error in on_tick for {symbol}: {error}"
BOT_FATAL_ERROR = "Fatal error in bot loop: {error}"
STRATEGY_REG_DEBUG = "Registered {strategy} for {symbol}"

# ─── Trading & Risk ─────────────────────────────────────────────────

TRADE_EXECUTION_FAILED = "❌ EXECUTION FAILED {symbol}: {error}"
TRADE_SUCCESS = "✅ {symbol} Order executed: {volume} {action} @ {price}"
SPLIT_TRADE_SUCCESS = (
    "✅ {symbol} Order {index}/{total} executed: {volume} lots @ TP {tp}"
)
SPLIT_TRADE_FAILED = "❌ {symbol} Order {index}/{total} failed: {error}"
ALL_SPLIT_SUCCESS = "✅ All split orders executed for {symbol}"

SPLITTER_DISABLED = "Split execution disabled. Executing single order for {symbol}."
SPLITTER_START = "Splitting execution for {symbol}: {volumes} lots at TPs {levels}"
NO_PENDING_ORDERS = "No pending orders."

RISK_LIMIT_EXCEEDED = "❌ Risk limit exceeded: {reason}"
INSUFFICIENT_MARGIN = "❌ Insufficient margin for trade on {symbol}"
MAX_POSITIONS_REACHED = "❌ Maximum position limit reached for {symbol}"
SPREAD_TOO_WIDE = "❌ Spread too wide for {symbol}: {spread} pips (Limit: {limit})"
MARGIN_LEVEL_LOW = "⚠️ Margin Level Low: {level:.2f}% (Limit: {limit}%)"
DRAWDOWN_WARNING_DAILY = "⚠️ Daily DD at {percent:.0f}% of limit ({value:.2f}%)"
DRAWDOWN_WARNING_TOTAL = "⚠️ Total DD at {percent:.0f}% of limit ({value:.2f}%)"

WATCHDOG_PAUSE = "⚠️ Market Watchdog: Pausing {symbol} due to high spread: {spread:.5f} > {limit:.5f}"
WATCHDOG_NORMAL = "✅ Market Watchdog: Market conditions normalized for {symbol}."
WATCHDOG_STALE = "🚨 Market Watchdog: Stale data detected for {symbol}!"

RISK_HEALTHY = "🟢 HEALTHY"
RISK_CAUTION = "🟡 CAUTION"
RISK_DANGER = "🔴 DANGER"
RISK_DASHBOARD_TITLE = "⚠️ *RISK DASHBOARD*"
RISK_DRAWDOWN_BLOCKED = "⚠️ Trade blocked by Drawdown Manager: {reason}"
RISK_ACCOUNT_DISABLED = "⚠️ Risk Check Failed: Account trading is disabled."
RISK_CORRELATION_BLOCKED = (
    "⚠️ Trade blocked by Correlation Check: {symbol} vs Portfolio"
)
RISK_POSITIONS_FETCH_ERROR = "❌ Error fetching open positions for risk check: {error}"

# ─── AI, Analytics & Backtesting ────────────────────────────────────

AI_REPORT_GENERATING = "🔄 Generating AI performance report..."
AI_REPORT_FAILED = "⚠️ Could not generate AI report."
AI_MARKET_ANALYSING = "🔄 Analysing market for {symbol}..."
AI_MARKET_FAILED = "⚠️ Could not analyse market."
AI_GUARD_BLOCKED_ALT = "🛡️ AI Risk Guard blocked {action} {symbol}: {reason}"
AI_GUARD_ERROR_ALT = "⚠️ AI Risk Guard error (fail-open): {error}"
AI_FEATURES_DISABLED = "⚠️ AI features are disabled via settings."
AI_UNAVAILABLE_API_KEY = "⚠️ AI features unavailable — GEMINI_API_KEY not configured."
AI_EMPTY_RESPONSE = "⚠️ AI analysis returned empty — please try again later."
NO_CANDLE_DATA = "⚠️ No candle data available for {symbol} {timeframe}."
HISTORY_RETRIEVAL_ERROR = "❌ Error retrieving trade history. Please try again later."
NO_CLOSED_TRADES = "📊 No closed trades found in storage."

NEWS_FETCHING = "Fetching economic calendar..."
NEWS_FETCH_FAILED = "Failed to fetch calendar: {status_code}"
NEWS_ERROR = "Error fetching economic calendar: {error}"
NEWS_START = "Starting News Manager..."
NEWS_FILTER_DISABLED = "News filter disabled in settings."
NEWS_UPDATED = "Calendar updated. {count} events cached."
TRADING_PAUSED_NEWS = "⛔ Trading paused for {symbol} due to news: [{impact}] {currency} - {title} @ {time}"
NEWS_UPDATE_ERROR = "Error in news update loop: {error}"

FEED_START = "Starting Data Feed for {symbols}..."
FEED_ERROR = "Error in DataFeed polling: {error}"

TRACKER_INIT = "Initializing PerformanceTracker..."
TRACKER_LOAD_ERROR = "Error loading trades: {error}"
TRACKER_TRADE_RECORDED = "Trade recorded: {symbol} Profit: {profit}"
TRACKER_SAVE_ERROR = "Error saving trades: {error}"
TRACKER_LOADED = "Loaded {count} trades into performance tracker."

EXECUTOR_SYM_INFO_FAILED = "❌ Cannot execute: failed to get symbol info for {symbol}"
EXECUTOR_ZERO_VOLUME = "⚠️ Calculated volume is 0 for {symbol}. Skipping."
EXECUTOR_RISK_BLOCKED = "⚠️ Trade for {symbol} blocked by Risk Manager."
SIGNAL_PROCESS_ERROR = "❌ Error processing signal for {symbol}: {error}"

STRATEGY_ADDED = "Added strategy for {symbol}"
STRATEGY_ACC_ADDED = "Added high-accuracy strategies for {symbol}"
STRATEGY_ERROR = "Error in strategy {name}: {error}"
STRATEGY_CALC_ERROR = "Error calculating signals for {name}: {error}"
STRATEGY_FETCH_ERROR = "Error fetching data for strategy analysis: {error}"

BACKTEST_FAILED = "❌ Backtest failed due to an internal error."
BACKTEST_INVALID_DAYS = "❌ Days must be a number (e.g., /backtest EURUSD 30)"
BACKTEST_START = "🔄 Starting backtest for *{symbol}*\\n📅 Period: {start} to {end} ({days} days)\\n💰 Initial Cash: ${cash:,.0f}"
BACKTEST_NO_DATA = "❌ No data found for {symbol}. Check if the symbol is correct or data is available."

# ─── Bot Control ────────────────────────────────────────────────────

AUTO_TRADING_ENABLED = "✅ Auto Trading Enabled (Runtime)"
AUTO_TRADING_DISABLED = "🛑 Auto Trading Disabled"
BOT_STOPPED = "🛑 Bot execution stopped."
FEATURE_DISABLED = "⚠️ This feature is currently disabled."
GENERIC_ERROR = "❌ An error occurred processing this command."
MENU_ERROR = "❌ Error processing menu selection."
MAIN_MENU = "🎛️ *MAIN MENU*\\n\\nSelect an option:"
BOT_NOT_INJECTED = "❌ TradingBot not injected. Cannot stop."

# ─── UI Labels & Symbols ────────────────────────────────────────────

SUCCESS = "✅"
ERROR = "❌"
WARNING = "⚠️"
INFO = "ℹ️"
HEALTHY = "🟢"
CAUTION = "🟡"
DANGER = "🔴"
NEUTRAL = "⚪"
CHART = "📊"
MONEY = "💰"
PENDING = "⏳"

# Aliases for Telegram
SYM_SUCCESS = SUCCESS
SYM_ERROR = ERROR
SYM_WARNING = WARNING
SYM_INFO = INFO
SYM_HEALTHY = HEALTHY
SYM_CAUTION = CAUTION
SYM_DANGER = DANGER
SYM_NEUTRAL = NEUTRAL
SYM_CHART = CHART
SYM_MONEY = MONEY
SYM_PENDING = PENDING

LABEL_AUTO = "Auto"
LABEL_MANUAL = "Manual"
LABEL_ONLINE = "Online"
LABEL_OFFLINE = "Offline"

# ─── Information & Help ─────────────────────────────────────────────

WELCOME = """
🤖 *QuantLux Trading Bot*

Welcome! I'm here to help you manage your automated trading system.

*Available Commands:*
/menu - Interactive main menu 🎛️
/status - Get account status
/balance - Get account balance and equity
/positions - List all open positions
/orders - List all pending orders
/connect - Check MetaApi connection status

*Analytics:*
/performance - View trading performance
/risk - View risk dashboard

*Control:*
/enable - Enable auto trading
/disable - Disable auto trading
/help - Show detailed help

💡 Use /menu for an interactive experience!
"""

HELP = """
🤖 *QuantLux-FX Trading Bot Commands*

*Info Commands:*
/status - Show account status
/balance - Show account balance
/positions - Show open positions
/orders - Show pending orders
/summary - Trading summary

*📊 Analytics:*
/performance - Advanced metrics (Sharpe, drawdown)
/drawdown - Current drawdown status
/trades - Recent trade history (from DB)

*Control:*
/enable - Enable auto-trading
/disable - Disable auto-trading
/stop - Stop bot

*Other:*
/risk - Risk analysis
/menu - Main menu

💡 *Tip:* Use interactive buttons to navigate and refresh data!
"""
