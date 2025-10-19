# Additional VIX-based feature
import pandas as pd


def compute(data: dict) -> pd.Series:
    df = data.get("VIX")
    if df is None or df.empty:
        return pd.Series(dtype=float, name="vix_level")

    # VIX level normalized as a feature
    # Higher VIX = higher global fear
    vix_values = df["Close"]

    # Set the series name
    vix_values.name = "vix_level"
    return vix_values
