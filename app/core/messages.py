"""Centralized repository for all system messages and strings."""

CONNECT_SUCCESS = "✅ Connected to MetaApi — Account: {account_id}"
CONNECT_FAILED = "❌ Failed to connect to MetaApi. Check your credentials."
MT_NOT_CONNECTED = "❌ MetaApi Not Connected."
ACC_INFO_FAILED = "❌ Could not retrieve account info."
SERVICE_SYNC = "✅ Services synchronized with live equity: ${equity:.2f}"
LATENCY_WARNING = "⚠️ HIGH LATENCY: {operation} took {latency:.2f}ms"
APP_START = "🚀 Starting QuantLux Trading Bot"
SYNC_FAILED = "⚠️ Could not sync with live account info; using default levels."
SYNC_ERROR = "⚠️ Sync error: {error}. Defaulting risk levels."
SHUTDOWN_SIGNAL = "Shutdown signal received"
RUNNING_MESSAGE = "QuantLux-FX is running! Press Ctrl+C to stop."
SHUTDOWN_START = "Initiating graceful shutdown..."
SHUTDOWN_COMPLETE_GOODBYE = "Shutdown complete. Goodbye!"
FATAL_ERROR = "Fatal application error: {error}"

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
STRATEGY_REG_DEBUG = "Registered {strategy} for {symbol}"


TRADE_EXECUTION_FAILED = "❌ EXECUTION FAILED {symbol}: {error}"
TRADE_SUCCESS = "✅ {symbol} Order executed: {volume} {action} @ {price}"
SPLIT_TRADE_SUCCESS = (
    "✅ {symbol} Order {index}/{total} executed: {volume} lots @ TP {tp}"
)
SPLIT_TRADE_FAILED = "❌ {symbol} Order {index}/{total} failed: {error}"
ALL_SPLIT_SUCCESS = "✅ All split orders executed for {symbol}"

SPLITTER_DISABLED = "Split execution disabled. Executing single order for {symbol}."
SPLITTER_START = "Splitting execution for {symbol}: {volumes} lots at TPs {levels}"

RISK_LIMIT_EXCEEDED = "❌ Risk limit exceeded: {reason}"
INSUFFICIENT_MARGIN = "❌ Insufficient margin for trade on {symbol}"
MAX_POSITIONS_REACHED = "❌ Maximum position limit reached for {symbol}"
SPREAD_TOO_WIDE = "❌ Spread too wide for {symbol}: {spread} pips (Limit: {limit})"
MARGIN_LEVEL_LOW = "⚠️ Margin Level Low: {level:.2f}% (Limit: {limit}%)"
DRAWDOWN_WARNING_DAILY = "⚠️ Daily DD at {percent:.0f}% of limit ({value:.2f}%)"
DRAWDOWN_WARNING_TOTAL = "⚠️ Total DD at {percent:.0f}% of limit ({value:.2f}%)"

WATCHDOG_PAUSE = (
    "⚠️ Watchdog: Pausing {symbol} — high spread {spread:.5f} > {limit:.5f}"
)
WATCHDOG_NORMAL = "✅ Watchdog: Market conditions normalized for {symbol}."
WATCHDOG_STALE = "🚨 Watchdog: Stale data detected for {symbol}!"

RISK_DRAWDOWN_BLOCKED = "⚠️ Trade blocked by Drawdown Manager: {reason}"
RISK_ACCOUNT_DISABLED = "⚠️ Risk Check Failed: Account trading is disabled."
RISK_CORRELATION_BLOCKED = (
    "⚠️ Trade blocked by Correlation Check: {symbol} vs Portfolio"
)
RISK_POSITIONS_FETCH_ERROR = "❌ Error fetching open positions for risk check: {error}"

NO_CANDLE_DATA = "⚠️ No candle data available for {symbol} {timeframe}."
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
TRACKER_NO_HISTORY = "No historical trades found."

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
BACKTEST_NO_DATA = "❌ No data found for {symbol}. Check if the symbol is correct or data is available."
