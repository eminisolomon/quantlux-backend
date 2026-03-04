# QuantLux Installation

Algorithmic trading system with MetaApi cloud integration and high-accuracy strategies.

---

## Environment Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -r requirements.txt
```

---

## MetaApi Configuration

1. **Get credentials:** [MetaApi Dashboard](https://app.metaapi.cloud/)
2. **Connect MT5 account:** [Add Account](https://app.metaapi.cloud/accounts)
3. **Copy token & account ID:** [API Tokens](https://app.metaapi.cloud/token)

```bash
cp .env.example .env
```

**Required in `.env`:**

```bash
METAAPI_TOKEN=your_token
METAAPI_ACCOUNT_ID=your_account_id
METAAPI_REGION=new-york
```

**Test connection:**

```bash
python scripts/test_metaapi_connection.py
```

---

## Strategies

Three high-accuracy strategies auto-enabled:

| Strategy        | Win Rate | Best For         |
| --------------- | -------- | ---------------- |
| Smart Money ICT | 75-85%   | Trending markets |
| Mean Reversion  | 72-78%   | Ranging markets  |
| RSI (basic)     | 60-70%   | General          |

**Configure in `.env`:**

```bash
USE_ICT_STRATEGY=true
USE_MEAN_REVERSION_STRATEGY=true
USE_RSI_STRATEGY=false
```

See `STRATEGIES.md` for details.

---

## Run

```bash
# Test strategies
python scripts/test_strategy_integration.py

# Run bot
python main.py
```

---

## Key Files

- `.env` - Configuration
- `STRATEGIES.md` - Strategy documentation
- `app/strategies/adapter.py` - Strategy integration
- `app/strategies/smart_money/` - ICT strategy
- `app/strategies/mean_reversion.py` - Mean reversion strategy

---

## Troubleshooting

**MetaApi not connecting:**

- Verify token/account ID
- Check account status: [MetaApi Accounts](https://app.metaapi.cloud/accounts)
- Wait 2-5 min after adding account

**No signals:**

- Strategies need specific market conditions
- Check logs for data fetching
- Lower `min_confidence` in strategy config

---

## Development

```bash
uv pip install -r requirements-dev.txt
pytest tests/
black .
```

---

**Ready to trade? Test on demo first, then configure for live trading in `.env`**
