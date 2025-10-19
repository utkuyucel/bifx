import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import APIConfig, DataConfig, DataSourceConfig, DataSources


logger = logging.getLogger(__name__)


def _get_cache_path(source_name: str, config: DataConfig) -> Path:
    config.cache_dir.mkdir(parents=True, exist_ok=True)
    return config.cache_dir / f"{source_name}.parquet"


def _is_cache_valid(cache_path: Path, config: DataConfig) -> bool:
    if not cache_path.exists():
        return False
    if not config.use_cache:
        return False

    file_age_days = (datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)).days
    return file_age_days < config.cache_days_valid


def _load_from_yfinance(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Load data from Yahoo Finance."""
    try:
        import yfinance as yf

        logger.info(f"Fetching {symbol} from yfinance ({start_date} to {end_date})")
        df = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)

        if df.empty:
            logger.warning(f"No data returned for {symbol}")
            return df

        # Flatten multi-index columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df

    except Exception as e:
        logger.error(f"Failed to load {symbol} from yfinance: {e}")
        return pd.DataFrame()


def _load_from_alphavantage(
    symbol: str, start_date: str, end_date: str, api_config: APIConfig
) -> pd.DataFrame:
    """Load data from Alpha Vantage."""
    api_key = api_config.get_key("alphavantage")

    if not api_key:
        logger.warning(
            f"Alpha Vantage API key not configured - skipping {symbol}. "
            "Add ALPHAVANTAGE_API_KEY to .env or disable this source in config.py"
        )
        return pd.DataFrame()

    try:
        import requests

        logger.info(f"Fetching {symbol} from Alpha Vantage ({start_date} to {end_date})")

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "FX_DAILY",
            "from_symbol": "USD",
            "to_symbol": symbol,
            "apikey": api_key,
            "outputsize": "full",
        }

        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        if "Time Series FX (Daily)" not in data:
            logger.error(f"Invalid response from Alpha Vantage: {data.get('Note', data)}")
            return pd.DataFrame()

        # Convert to DataFrame
        ts_data = data["Time Series FX (Daily)"]
        df = pd.DataFrame.from_dict(ts_data, orient="index")
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        # Rename columns
        df.columns = ["Open", "High", "Low", "Close"]
        df = df.astype(float)

        # Filter by date range
        df = df.loc[start_date:end_date]

        return df

    except Exception as e:
        logger.error(f"Failed to load {symbol} from Alpha Vantage: {e}")
        return pd.DataFrame()


def _load_from_pytrends(keywords: list, start_date: str, end_date: str) -> pd.DataFrame:
    """Load Google Trends data."""
    try:
        from pytrends.request import TrendReq

        logger.info(f"Fetching Google Trends for keywords: {keywords}")
        pytrends = TrendReq(hl="tr-TR", tz=180)

        # Build payload with date range
        pytrends.build_payload(keywords, timeframe=f"{start_date} {end_date}", geo="TR")
        df = pytrends.interest_over_time()

        if not df.empty and "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])

        return df

    except Exception as e:
        logger.error(f"Failed to load Google Trends: {e}")
        return pd.DataFrame()


def _load_manual_csv(filename: str, config: DataConfig) -> pd.DataFrame:
    """Load manually provided CSV data."""
    manual_path = config.cache_dir / filename

    if not manual_path.exists():
        logger.warning(f"Manual data file not found: {manual_path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(manual_path, parse_dates=["Date"], index_col="Date")
        logger.info(f"Loaded manual data from {manual_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load manual CSV {filename}: {e}")
        return pd.DataFrame()


def _load_source(
    source_config: DataSourceConfig, config: DataConfig, api_config: APIConfig
) -> pd.DataFrame:
    """Load data for a single source using configured provider."""
    cache_path = _get_cache_path(source_config.name, config)

    # Check cache first
    if _is_cache_valid(cache_path, config):
        logger.info(f"Loading {source_config.name} from cache")
        return pd.read_parquet(cache_path)

    # Load from provider
    df = pd.DataFrame()

    if source_config.provider == "yfinance":
        df = _load_from_yfinance(source_config.symbol, config.start_date, config.end_date)
    elif source_config.provider == "alphavantage":
        df = _load_from_alphavantage(
            source_config.symbol, config.start_date, config.end_date, api_config
        )
    elif source_config.provider == "manual":
        df = _load_manual_csv(source_config.symbol, config)
    else:
        logger.error(f"Unknown provider: {source_config.provider}")
        return pd.DataFrame()

    # Cache if data loaded successfully
    if not df.empty and config.use_cache:
        df.to_parquet(cache_path)
        logger.info(f"Cached {source_config.name} to {cache_path}")

    return df


def load_data(
    config: DataConfig = None, sources: DataSources = None, api_config: APIConfig = None
) -> dict[str, pd.DataFrame]:
    """Load all configured data sources."""
    if config is None:
        config = DataConfig()
    if sources is None:
        sources = DataSources()
    if api_config is None:
        api_config = APIConfig()

    logger.info("Starting data load process")

    data = {}

    # Load regular data sources
    for source_config in sources.sources:
        if not source_config.enabled:
            logger.debug(f"Skipping disabled source: {source_config.name}")
            continue

        df = _load_source(source_config, config, api_config)
        if not df.empty:
            data[source_config.name] = df

    # Load Google Trends separately
    if sources.google_trends_keywords:
        cache_path = _get_cache_path("GoogleTrends", config)

        if _is_cache_valid(cache_path, config):
            logger.info("Loading Google Trends from cache")
            data["GoogleTrends"] = pd.read_parquet(cache_path)
        else:
            df = _load_from_pytrends(
                sources.google_trends_keywords, config.start_date, config.end_date
            )
            if not df.empty:
                data["GoogleTrends"] = df
                if config.use_cache:
                    df.to_parquet(cache_path)
                    logger.info(f"Cached Google Trends to {cache_path}")

    logger.info(f"Data load complete. Sources loaded: {list(data.keys())}")

    return data
