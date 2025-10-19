import pandas as pd


def compute(data: dict) -> pd.Series:
    df = data.get("XU100")
    if df is None or df.empty:
        return pd.Series(dtype=float, name="example_double_price")

    # Demo feature: simply double the closing price
    double_close = df["Close"] * 2

    return double_close.rename("example_double_price")
