import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import DataConfig, DataSourceConfig, DataSources


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


def _load_from_alphavantage(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Load data from Alpha Vantage (requires API key in .env)."""
    try:
        import os

        import requests
        from dotenv import load_dotenv

        load_dotenv()

        api_key = os.getenv("ALPHAVANTAGE_API_KEY")
        if not api_key:
            logger.warning(
                f"ALPHAVANTAGE_API_KEY not found in .env file - skipping {symbol}. "
                "Add API key to .env or disable this source in config.py"
            )
            return pd.DataFrame()

        logger.info(f"Fetching {symbol} from Alpha Vantage ({start_date} to {end_date})")

        # For forex (e.g., TRY), use FX_DAILY
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


def _load_from_ccxt(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Load crypto data from CCXT (multiple exchanges)."""
    try:
        import ccxt

        logger.info(f"Fetching {symbol} from CCXT/Binance ({start_date} to {end_date})")

        exchange = ccxt.binance({"enableRateLimit": True})

        # Convert dates to milliseconds timestamp
        start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
        end_ts = int(pd.Timestamp(end_date).timestamp() * 1000)

        # Fetch OHLCV data
        ohlcv = []
        current_ts = start_ts

        while current_ts < end_ts:
            try:
                batch = exchange.fetch_ohlcv(symbol, "1d", since=current_ts, limit=1000)
                if not batch:
                    break
                ohlcv.extend(batch)
                current_ts = batch[-1][0] + 86400000  # Add 1 day in ms
            except Exception as e:
                logger.warning(f"CCXT batch fetch error: {e}")
                break

        if not ohlcv:
            logger.warning(f"No data returned for {symbol} from CCXT")
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms")
        df = df.set_index("Timestamp")
        df = df.loc[start_date:end_date]

        return df

    except Exception as e:
        logger.error(f"Failed to load {symbol} from CCXT: {e}")
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


def _load_source(source_config: DataSourceConfig, config: DataConfig) -> pd.DataFrame:
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
        df = _load_from_alphavantage(source_config.symbol, config.start_date, config.end_date)
    elif source_config.provider == "ccxt":
        df = _load_from_ccxt(source_config.symbol, config.start_date, config.end_date)
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


def load_data(config: DataConfig = None, sources: DataSources = None) -> dict[str, pd.DataFrame]:
    """Load all configured data sources."""
    if config is None:
        config = DataConfig()
    if sources is None:
        sources = DataSources()

    logger.info("Starting data load process")

    data = {}

    # Load regular data sources
    for source_config in sources.sources:
        if not source_config.enabled:
            logger.debug(f"Skipping disabled source: {source_config.name}")
            continue

        df = _load_source(source_config, config)
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
