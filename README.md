# 🏗️ BIFX — Borsa İstanbul Fear Index

Modular, plugin-based Fear Index system for Turkish stock market (BIST/XU100).

## Overview

BIFX computes a normalized 0-100 fear index using multiple data sources and customizable feature plugins:

- **XU100** — Turkish stock market index
- **USDTRY** — Turkish Lira volatility
- **VIX** — Global fear gauge
- **Turkey 5Y CDS** — Sovereign risk
- **Google Trends** — Sentiment data
- **Commodities** — Brent, Gold, BTC
- **SP500** — Global equity correlation

## Architecture

```
bifx_project/
├── data/raw/          # Cached market data
├── features/          # Feature plugins (drop-in .py files)
├── core/              # Core engine modules
│   ├── data_loader.py
│   ├── feature_engine.py
│   ├── index_calculator.py
│   └── backtest.py
├── run_pipeline.py    # Main entry point
├── config.py          # All configuration
└── requirements.txt
```

## Quick Start

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run full pipeline
python run_pipeline.py
```

## Feature Plugin System

Each feature is a single `.py` file in `features/` with a `compute(data)` function:

```python
# features/example_feature.py
def compute(data):
    df = data["XU100"]
    return df["Close"].pct_change().rolling(20).std().rename("my_feature")
```

The feature engine auto-discovers and executes all plugins.

## Included Features

- `realized_vol.py` — XU100 20-day realized volatility
- `usdtry_shock.py` — USDTRY daily shock z-score
- `cds_spike.py` — Turkey CDS spike detection
- `sentiment_trends.py` — Google Trends sentiment
- `example_double_price.py` — Demo plugin (XU100 * 2)

## Backtest Metrics

- **Correlation** — Spearman correlation with next-day absolute returns
- **ROC-AUC** — Crash prediction (< -2% days)
- **Sharpe Ratio** — Simple overlay strategy performance

## Configuration

Edit `config.py` to customize:

### Date Configuration
```python
from config import DataConfig

# Default: 1 year back from today
config = DataConfig()

# Custom: 3 years back
config = DataConfig(years_back=3)

# Manual start date, auto end date (today)
config = DataConfig(start_date='2020-01-01')

# Both dates manual
config = DataConfig(start_date='2020-01-01', end_date='2023-12-31')
```

### Other Settings
- Feature parameters (windows, thresholds)
- Index weights (realized_vol: 0.25, usdtry_shock: 0.20, etc.)
- Backtest thresholds

## Code Quality

This project uses black, ruff, and mypy for code quality:

```bash
# Run all checks and auto-fix (recommended)
./lint.sh

# Or run individually:
# Format code
black .

# Lint code
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Type checking
mypy config.py core/ features/
```

Configured limits:
- Max line length: 100 characters
- Max function complexity: 10
- Type checking: mypy (non-blocking warnings)

## Adding New Features

1. Create `features/my_new_feature.py`
2. Implement `compute(data: dict) -> pd.Series`
3. Return Series indexed by date
4. Run pipeline — feature auto-discovered

### Example Feature

```python
import pandas as pd

def compute(data: dict) -> pd.Series:
    df = data.get("XU100")
    if df is None or df.empty:
        return pd.Series(dtype=float, name="my_feature")
    
    # Your calculation here
    result = df["Close"].pct_change().rolling(20).std()
    
    return result.rename("my_feature")
```

### Available Data Sources

- `XU100` — Borsa Istanbul 100 Index
- `USDTRY` — USD/TRY Exchange Rate
- `VIX` — CBOE Volatility Index
- `SP500` — S&P 500 Index
- `BRENT` — Brent Crude Oil
- `GOLD` — Gold Futures
- `BTC` — Bitcoin USD
- `CDS` — Turkey 5Y CDS (manual)
- `GoogleTrends` — Search trends

## License

MIT License — see LICENSE file

## Data Sources

- yfinance (market data)
- Google Trends (pytrends)
- Manual CDS data (TradingEconomics fallback)
