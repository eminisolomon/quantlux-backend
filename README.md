# QuantLux 🚀

A production-ready automated trading system built on **MetaApi Cloud SDK** with advanced risk management, multi-strategy confluence, and a rich Telegram interface.

## 🌟 Key Features

### 🤖 Intelligent Trading

- **Multi-Strategy Confluence**: Combines ICT (Smart Money Concepts), Mean Reversion, and RSI strategies.
- **Adaptive Execution**: Supports "Split Execution" for partial take profits (TP1, TP2, TP3).
- **High-Accuracy Logic**: Uses advanced market structure analysis (FVG, Order Blocks).

### ☁️ Cloud-Native (MetaApi)

- **Zero Local Footprint**: 100% cloud-based execution via MetaApi SDK.
- **Enterprise Resilience**: Auto-reconnect, rate limiting, and latency monitoring built-in.
- **No MT5 Required**: Runs entirely on python, removing the need for a local terminal.

### 🛡️ Risk Management

- **Volatility Sizing**: Auto-calculates lot sizes based on ATR and account equity.
- **Drawdown Protection**: Daily and Total drawdown limiters (Circuit Breakers).
- **Split Execution**: Hardened partial exits stored on the broker server.

### 📱 Telegram Command Center

- **Real-Time Control**: Monitor and control your bot from anywhere.
- **Rich Notifications**: Beautifully formatted trade alerts and performance reports.
- **Interactive Commands**: `/status`, `/balance`, `/positions`, `/enable`, `/disable`.

### 🧠 AI-Powered Intelligence (Gemini)

- **Market Analysis**: `/ai_analyze EURUSD H4` — AI trade bias, S/R levels, setup ideas.
- **Performance Coaching**: `/ai_report` — AI coaching with pattern recognition and action plans.
- **Trade History Q&A**: `/ai_ask` — Natural language questions over your trade database.
- **Strategy Optimiser**: `/ai_optimize` — AI-driven parameter tuning suggestions.
- **Risk Guard**: Pre-trade AI gate evaluating drawdown, correlation, and news risk.
- **Natural Language Chat**: Message the bot in plain English for trading assistance.

## 📚 Documentation

Detailed guides can be found in the `docs/` directory:

- **[Installation Guide](docs/INSTALLATION.md)**: Setup, configuration, and running the bot.
- **[Strategy Overview](docs/STRATEGIES.md)**: Logic behind ICT, Mean Reversion, and RSI strategies.
- **[AI Features Guide](docs/AI_FEATURES.md)**: Gemini AI setup, commands, architecture, and prompt engineering.

## 🚀 Quick Links

- [MetaApi Dashboard](https://app.metaapi.cloud)
- [Telegram Bot Father](https://t.me/botfather)

**⚠️ Risk Warning**: Trading Forex and CFDs involves significant risk. This software is for educational purposes only. Use at your own risk.
