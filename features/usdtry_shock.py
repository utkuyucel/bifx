import pandas as pd

from config import FeatureConfig


def compute(data: dict) -> pd.Series:
    config = FeatureConfig()

    df = data.get("USDTRY")
    if df is None or df.empty:
        return pd.Series(dtype=float, name="usdtry_shock")

    # Calculate daily absolute change
    daily_change = df["Close"].diff().abs()

    # Calculate rolling standard deviation
    rolling_std = daily_change.rolling(window=config.usdtry_shock_window).std()

    # Z-score of daily shock
    shock_zscore = (
        daily_change - daily_change.rolling(config.usdtry_shock_window).mean()
    ) / rolling_std

    return shock_zscore.rename("usdtry_shock")
