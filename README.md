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
├── output/            # Generated results (CSV, plots)
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

# Output files are saved to output/ directory
# - output/bifx_fear_index.csv
# - output/bifx_backtest_results.png
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

## Dynamic Data Sources

BIFX now supports multiple data providers dynamically configured in `config.py`:

### Available Providers

- **yfinance** — Yahoo Finance (default for most assets)
- **alphavantage** — Alpha Vantage (forex, stocks) — requires API key
- **ccxt** — Cryptocurrency exchanges (Binance default)
- **pytrends** — Google Trends
- **manual** — Manual CSV uploads

### Configuration

Edit `config.py` to enable/disable sources or switch providers:

```python
@dataclass
class DataSources:
    sources: list[DataSourceConfig] = field(default_factory=lambda: [
        DataSourceConfig(name="XU100", provider="yfinance", symbol="XU100.IS"),
        DataSourceConfig(name="USDTRY", provider="yfinance", symbol="TRY=X"),
        DataSourceConfig(name="USDTRY_AV", provider="alphavantage", symbol="TRY", enabled=False),
        DataSourceConfig(name="BTC", provider="yfinance", symbol="BTC-USD"),
        DataSourceConfig(name="BTC_CCXT", provider="ccxt", symbol="BTC/USDT", enabled=False),
        # ... more sources
    ])
```

### Alpha Vantage Setup (Optional)

To use Alpha Vantage provider:

1. Get free API key from: https://www.alphavantage.co/support/#api-key
2. Copy `.env.example` to `.env` and add your key:
   ```bash
   cp .env.example .env
   # Edit .env and add: ALPHAVANTAGE_API_KEY=your_actual_key
   ```
3. Enable Alpha Vantage sources in `config.py`:
   ```python
   DataSourceConfig(name="USDTRY_AV", provider="alphavantage", symbol="TRY", enabled=True)
   ```

API keys are centrally managed in `config.py` via the `APIConfig` class.

### CCXT Crypto Data (Optional)

CCXT provides direct crypto exchange data:

```python
# Enable CCXT for BTC instead of yfinance
DataSourceConfig(name="BTC", provider="yfinance", symbol="BTC-USD", enabled=False),
DataSourceConfig(name="BTC_CCXT", provider="ccxt", symbol="BTC/USDT", enabled=True),
```

### Manual Data Upload

For sources not available via API (e.g., CDS):

```python
DataSourceConfig(name="CDS", provider="manual", symbol="cds_manual.csv")
```

Place CSV file in `data/raw/` with format:
```
Date,Close
2024-01-01,350.5
2024-01-02,352.3
```

## Data Sources

- **yfinance** — Primary market data provider
- **Alpha Vantage** — Alternative for forex/stocks (requires API key)
- **CCXT** — Cryptocurrency exchange data (Binance)
- **Google Trends** — Search sentiment (pytrends)
- **Manual CSV** — Custom data upload
