import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv


# Load environment variables once at module level
load_dotenv()


# =============================================================================
# AUTHENTICATION & API CONFIGURATION
# =============================================================================


@dataclass(frozen=True)
class APIConfig:
    """API keys and authentication configuration (provider-agnostic)."""

    api_keys: dict = None

    def __post_init__(self):
        if self.api_keys is None:
            keys = {
                "alphavantage": os.getenv("ALPHAVANTAGE_API_KEY", ""),
                # Add more providers here as needed
            }
            object.__setattr__(self, "api_keys", keys)

    def get_key(self, provider: str) -> str:
        """Get API key for a specific provider."""
        print(f"Retrieving API key for provider: {provider}")
        if provider not in self.api_keys or not self.api_keys[provider]:
            print(f"  ⚠️  Warning: API key for {provider} is missing or not set.")

        else:
            print(f"  ✅ API key for {provider} found.")

        return self.api_keys.get(provider, "")


# =============================================================================
# DATA LOADING CONFIGURATION
# =============================================================================


@dataclass(frozen=True)
class DataSourceConfig:
    """Configuration for a single data source."""

    name: str  # Display name (e.g., "XU100", "USDTRY")
    provider: str  # Provider name: "yfinance", "alphavantage", "pytrends", "manual"
    symbol: str  # Provider-specific symbol/ticker
    enabled: bool = True  # Whether to load this source


@dataclass(frozen=True)
class DataSources:
    """Configure all data sources with their providers."""

    sources: list = None  # List of DataSourceConfig objects
    google_trends_keywords: list = None

    def __post_init__(self):
        # Default data sources configuration
        if self.sources is None:
            default_sources = [
                # Stock market indices
                DataSourceConfig("XU100", "yfinance", "XU100.IS"),
                DataSourceConfig("SP500", "yfinance", "^GSPC"),
                DataSourceConfig("VIX", "yfinance", "^VIX"),
                # Forex
                # DataSourceConfig("USDTRY", "yfinance", "TRY=X"),
                DataSourceConfig("USDTRY", "alphavantage", "TRY"),
                # Commodities
                DataSourceConfig("BRENT", "yfinance", "BZ=F"),
                DataSourceConfig("GOLD", "yfinance", "GC=F"),
                # Crypto
                DataSourceConfig("BTC", "yfinance", "BTC-USD"),
                # Manual data
                # DataSourceConfig("CDS", "manual", "cds_manual.csv"),
            ]
            object.__setattr__(self, "sources", default_sources)

        if self.google_trends_keywords is None:
            object.__setattr__(
                self, "google_trends_keywords", ["borsa istanbul", "dolar", "ekonomi krizi", "faiz"]
            )


@dataclass(frozen=True)
class DataConfig:
    """Date range and caching configuration."""

    years_back: int = 5  # Number of years back from today (if start_date not provided)
    start_date: str = None  # Manual start date in 'YYYY-MM-DD' format, or None for auto
    end_date: str = None  # Manual end date in 'YYYY-MM-DD' format, or None for today
    cache_dir: Path = Path(__file__).parent / "data" / "raw"
    use_cache: bool = True
    cache_days_valid: int = 1

    def __post_init__(self):
        # Calculate start_date if not provided
        if self.start_date is None:
            calculated_start = (datetime.now() - timedelta(days=365 * self.years_back)).strftime(
                "%Y-%m-%d"
            )
            object.__setattr__(self, "start_date", calculated_start)

        # Calculate end_date if not provided
        if self.end_date is None:
            calculated_end = datetime.now().strftime("%Y-%m-%d")
            object.__setattr__(self, "end_date", calculated_end)


# =============================================================================
# FEATURE ENGINEERING CONFIGURATION
# =============================================================================


@dataclass(frozen=True)
class FeatureConfig:
    """Parameters for feature calculations."""

    realized_vol_window: int = 20
    usdtry_shock_window: int = 20
    cds_spike_window: int = 60
    sentiment_window: int = 30


# =============================================================================
# FEAR INDEX CALCULATION CONFIGURATION
# =============================================================================


@dataclass(frozen=True)
class IndexConfig:
    """Fear index normalization and weighting configuration."""

    normalization_method: str = "zscore_minmax"
    min_value: float = 0.0
    max_value: float = 100.0
    ema_span: int = 5
    default_weights: dict = None

    def __post_init__(self):
        if self.default_weights is None:
            object.__setattr__(
                self,
                "default_weights",
                {
                    "realized_vol": 0.25,
                    "usdtry_shock": 0.20,
                    "cds_spike": 0.20,
                    "sentiment_trends": 0.15,
                    "vix_level": 0.10,
                    "correlation_breakdown": 0.10,
                },
            )


# =============================================================================
# BACKTESTING CONFIGURATION
# =============================================================================


@dataclass(frozen=True)
class BacktestConfig:
    """Backtest thresholds and evaluation parameters."""

    crash_threshold: float = -0.02
    high_fear_threshold: float = 70.0
    low_fear_threshold: float = 30.0
    risk_free_rate: float = 0.0
    plot_results: bool = True
