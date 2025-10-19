import pandas as pd

from config import FeatureConfig


def compute(data: dict) -> pd.Series:
    config = FeatureConfig()

    df = data.get("CDS")
    if df is None or df.empty:
        return pd.Series(dtype=float, name="cds_spike")

    # Assume CDS data has a 'Value' or 'Close' column
    cds_column = (
        "Value" if "Value" in df.columns else "Close" if "Close" in df.columns else df.columns[0]
    )
    cds_values = df[cds_column]

    # Calculate z-score over rolling window
    rolling_mean = cds_values.rolling(window=config.cds_spike_window).mean()
    rolling_std = cds_values.rolling(window=config.cds_spike_window).std()

    cds_zscore = (cds_values - rolling_mean) / rolling_std

    # Set the series name
    cds_zscore.name = "cds_spike"
    return cds_zscore
