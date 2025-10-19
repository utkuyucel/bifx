import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

from config import DataConfig, DataSources


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


def _load_from_yfinance(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    logger.info(f"Fetching {ticker} from yfinance ({start_date} to {end_date})")
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if df.empty:
        logger.warning(f"No data returned for {ticker}")
    return df


def _load_source(source_name: str, ticker: str, config: DataConfig) -> pd.DataFrame:
    cache_path = _get_cache_path(source_name, config)

    if _is_cache_valid(cache_path, config):
        logger.info(f"Loading {source_name} from cache")
        return pd.read_parquet(cache_path)

    df = _load_from_yfinance(ticker, config.start_date, config.end_date)

    if not df.empty and config.use_cache:
        df.to_parquet(cache_path)
        logger.info(f"Cached {source_name} to {cache_path}")

    return df


def _load_google_trends(keywords: list, config: DataConfig) -> pd.DataFrame:
    cache_path = _get_cache_path("GoogleTrends", config)

    if _is_cache_valid(cache_path, config):
        logger.info("Loading Google Trends from cache")
        return pd.read_parquet(cache_path)

    try:
        from pytrends.request import TrendReq

        logger.info(f"Fetching Google Trends for keywords: {keywords}")
        pytrends = TrendReq(hl="tr-TR", tz=180)

        # Build payload with date range
        pytrends.build_payload(
            keywords, timeframe=f"{config.start_date} {config.end_date}", geo="TR"
        )
        df = pytrends.interest_over_time()

        if not df.empty and "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])

        if not df.empty and config.use_cache:
            df.to_parquet(cache_path)
            logger.info(f"Cached Google Trends to {cache_path}")

        return df

    except Exception as e:
        logger.error(f"Failed to load Google Trends: {e}")
        return pd.DataFrame()


def _load_cds_data(config: DataConfig) -> pd.DataFrame:
    cache_path = _get_cache_path("CDS", config)

    if _is_cache_valid(cache_path, config):
        logger.info("Loading CDS from cache")
        return pd.read_parquet(cache_path)

    # CDS data requires manual download from TradingEconomics or similar
    # For now, return empty DataFrame with note to user
    logger.warning("CDS data not available - requires manual CSV in data/raw/cds_manual.csv")

    manual_path = config.cache_dir / "cds_manual.csv"
    if manual_path.exists():
        df = pd.read_csv(manual_path, parse_dates=["Date"], index_col="Date")
        logger.info(f"Loaded manual CDS data from {manual_path}")
        return df

    return pd.DataFrame()


def load_data(config: DataConfig = None, sources: DataSources = None) -> dict[str, pd.DataFrame]:
    if config is None:
        config = DataConfig()
    if sources is None:
        sources = DataSources()

    logger.info("Starting data load process")

    data = {
        "XU100": _load_source("XU100", sources.xu100_ticker, config),
        "USDTRY": _load_source("USDTRY", sources.usdtry_ticker, config),
        "VIX": _load_source("VIX", sources.vix_ticker, config),
        "SP500": _load_source("SP500", sources.sp500_ticker, config),
        "BRENT": _load_source("BRENT", sources.brent_ticker, config),
        "GOLD": _load_source("GOLD", sources.gold_ticker, config),
        "BTC": _load_source("BTC", sources.btc_ticker, config),
        "CDS": _load_cds_data(config),
        "GoogleTrends": _load_google_trends(sources.google_trends_keywords, config),
    }

    logger.info(
        f"Data load complete. Sources loaded: {[k for k, v in data.items() if not v.empty]}"
    )

    return data
