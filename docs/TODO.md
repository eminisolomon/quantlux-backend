# QuantLux Trading Bot - Roadmap & TODO

This document outlines the planned enhancements and missing features for the QuantLux FX trading system.

## 1. Core Infrastructure & Persistence

- [~] **Database Integration**: Implement a persistence layer (SQLite/PostgreSQL) for storing: (CANCELLED)
  - [~] Order and trade history.
  - [~] Daily/Total equity curve snapshots.
  - [~] Strategy performance logs.
- [x] **Dynamic Configuration**: Move hardcoded strategy parameters and symbol lists to a `config/settings.yaml` or `.env` file.
- [x] **Dependency Injection Refactor**: Further decouple services to allow easier unit testing and mocking of the MetaApi adapter.

## 2. Strategy Framework

- [x] **Multi-Strategy Support**: Enable running multiple strategies (RSI, Mean Reversion, SMC) concurrently on the same or different symbols.
- [ ] **Strategy Composition**: Implement a "Master Strategy" that aggregates signals from multiple sub-strategies.
- [x] **Market Regime Detection**: Implement a module to detect if the market is trending or ranging and adjust strategy behavior accordingly.

## 3. Order Execution & Risk Management

- [x] **Volatility-Based Position Sizing**: Use ATR (Average True Range) to calculate dynamic lot sizes and SL/TP levels.
- [x] **Advanced Trade Management**:
  - [x] **Partial Take Profits**: Close a percentage of a position at specific targets.
  - [x] **Trailing Stop Loss**: Automatically follow price movements to lock in profits.
  - [x] **Breakeven Trigger**: Move SL to entry after a certain profit threshold.
- [ ] **Slippage Analytics**: Track and log the difference between requested price and fill price.

## 4. News & Event Handling

- [x] **News Filter Integration**:
  - [x] Auto-pause trading 30 minutes before/after high-impact news (NFP, Rate Decisions).
  - [ ] Use AI to analyze news sentiment and adjust risk levels.

## 5. Analytics & Monitoring

- [ ] **Performance Dashboard**: Create a web-based UI (Next.js/React) for real-time monitoring.
- [x] **Advanced Metrics**: Calculate and display:
  - [x] Sharpe Ratio
  - [x] Sortino Ratio
  - [x] Recovery Factor
  - [x] Profit Factor
- [ ] **Health Monitoring**: Monitor connection stability and data feed latency; send alerts via Telegram on downtime.

## 6. Backtesting & Optimization

- [x] **Walk-Forward Analysis**: Implement a systematic backtesting pipeline for validating strategies on out-of-sample data.
- [x] **Parameter Optimizer**: Tool for finding the best strategy parameters (RSI periods, thresholds, etc.) using genetic algorithms or grid search.
