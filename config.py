from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class DataConfig:
    start_date: str = (datetime.now() - timedelta(days=365 * 3)).strftime("%Y-%m-%d")
    end_date: str = datetime.now().strftime("%Y-%m-%d")
    cache_dir: Path = Path(__file__).parent / "data" / "raw"
    use_cache: bool = True
    cache_days_valid: int = 1


@dataclass(frozen=True)
class FeatureConfig:
    realized_vol_window: int = 20
    usdtry_shock_window: int = 20
    cds_spike_window: int = 60
    sentiment_window: int = 30


@dataclass(frozen=True)
class IndexConfig:
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


@dataclass(frozen=True)
class BacktestConfig:
    crash_threshold: float = -0.02
    high_fear_threshold: float = 70.0
    low_fear_threshold: float = 30.0
    risk_free_rate: float = 0.0
    plot_results: bool = True


@dataclass(frozen=True)
class DataSources:
    xu100_ticker: str = "XU100.IS"
    usdtry_ticker: str = "TRY=X"
    vix_ticker: str = "^VIX"
    sp500_ticker: str = "^GSPC"
    brent_ticker: str = "BZ=F"
    gold_ticker: str = "GC=F"
    btc_ticker: str = "BTC-USD"
    google_trends_keywords: list = None

    def __post_init__(self):
        if self.google_trends_keywords is None:
            object.__setattr__(
                self, "google_trends_keywords", ["borsa istanbul", "dolar", "ekonomi krizi", "faiz"]
            )
