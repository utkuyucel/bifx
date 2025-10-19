import pandas as pd
from config import FeatureConfig


def compute(data: dict) -> pd.Series:
    config = FeatureConfig()
    
    df = data.get("XU100")
    if df is None or df.empty:
        return pd.Series(dtype=float, name="realized_vol")
    
    # Calculate 20-day realized volatility using close-to-close returns
    returns = df["Close"].pct_change()
    realized_vol = returns.rolling(window=config.realized_vol_window).std() * (252 ** 0.5)
    
    return realized_vol.rename("realized_vol")
