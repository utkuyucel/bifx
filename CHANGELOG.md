# BIFX Changelog

## [Unreleased] - Dynamic Data Sources

### Major Changes
- **Dynamic Data Source System**: Completely refactored data loading architecture to support multiple providers
  - Created `DataSourceConfig` dataclass for individual source configuration
  - Added provider-specific loaders: `yfinance`, `alphavantage`, `ccxt`, `pytrends`, `manual`
  - Sources can be enabled/disabled dynamically in `config.py`
  - Alternative providers can be configured for same asset (e.g., USDTRY from yfinance OR alphavantage)

### New Features
- **Alpha Vantage Integration**: Alternative provider for forex and stocks (requires API key)
- **CCXT Integration**: Direct cryptocurrency exchange data (Binance default)
- **Provider Switching**: Easy provider swapping without code changes
- **Manual CSV Upload**: Support for custom data via CSV files

### Configuration Changes
- `DataSources` class restructured to use list of `DataSourceConfig` objects
- Each source now has: name, provider, symbol, enabled flag
- Old individual ticker fields (xu100_ticker, etc.) replaced with dynamic list

### Dependencies Added
- `alpha-vantage>=2.3.0` - Alpha Vantage API client
- `requests>=2.31.0` - HTTP library for API calls

### Breaking Changes
- `config.py` structure changed (old ticker fields removed)
- `data_loader.py` completely rewritten with new provider system
- Features should continue to work without changes (uses source names like "XU100", "USDTRY", etc.)

### Migration Guide

**Old config.py:**
```python
@dataclass
class DataSources:
    xu100_ticker: str = "XU100.IS"
    usdtry_ticker: str = "TRY=X"
    # ...
```

**New config.py:**
```python
@dataclass
class DataSources:
    sources: list[DataSourceConfig] = field(default_factory=lambda: [
        DataSourceConfig(name="XU100", provider="yfinance", symbol="XU100.IS"),
        DataSourceConfig(name="USDTRY", provider="yfinance", symbol="TRY=X"),
        DataSourceConfig(name="USDTRY_AV", provider="alphavantage", symbol="TRY", enabled=False),
        # ...
    ])
```

### Example: Switching to Alternative Provider

```python
# Use Alpha Vantage for USDTRY instead of yfinance
DataSourceConfig(name="USDTRY", provider="yfinance", symbol="TRY=X", enabled=False),
DataSourceConfig(name="USDTRY_AV", provider="alphavantage", symbol="TRY", enabled=True),

# Use CCXT for BTC instead of yfinance
DataSourceConfig(name="BTC", provider="yfinance", symbol="BTC-USD", enabled=False),
DataSourceConfig(name="BTC_CCXT", provider="ccxt", symbol="BTC/USDT", enabled=True),
```

### Testing
- Pipeline tested successfully with all enabled sources
- Cache system working correctly with new structure
- All existing features continue to work unchanged

## Previous Releases

### [v0.3] - 2025-10-19 - Organization & Quality
- Moved all outputs to `output/` directory
- Added mypy type checking to lint workflow
- Updated README with comprehensive documentation

### [v0.2] - 2025-10-19 - Monitoring & Configuration
- Added null percentage monitoring (>30% threshold warnings)
- Flexible date configuration with `years_back` parameter
- Default changed from 3 years to 1 year of data

### [v0.1] - 2025-10-19 - Initial Implementation
- Core pipeline: data loading, feature engine, index calculation, backtesting
- Plugin-based feature system with auto-discovery
- Fixed yfinance compatibility issues
- Fixed fear index calculation (10.55-85.01 range)
- Established code quality tooling (black, ruff, mypy)
