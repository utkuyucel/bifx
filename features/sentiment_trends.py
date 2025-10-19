import pandas as pd
from config import FeatureConfig


def compute(data: dict) -> pd.Series:
    config = FeatureConfig()
    
    df = data.get("GoogleTrends")
    if df is None or df.empty:
        return pd.Series(dtype=float, name="sentiment_trends")
    
    # Aggregate all trend columns (keywords) into single sentiment score
    # Higher values = more search interest = more fear/concern
    
    # Take mean across all keyword columns
    sentiment = df.mean(axis=1)
    
    # Normalize using rolling z-score
    rolling_mean = sentiment.rolling(window=config.sentiment_window).mean()
    rolling_std = sentiment.rolling(window=config.sentiment_window).std()
    
    sentiment_zscore = (sentiment - rolling_mean) / rolling_std
    
    return sentiment_zscore.rename("sentiment_trends")
