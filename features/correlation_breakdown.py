# Correlation breakdown between XU100 and SP500
import pandas as pd


def compute(data: dict) -> pd.Series:
    xu100_df = data.get("XU100")
    sp500_df = data.get("SP500")

    if xu100_df is None or xu100_df.empty or sp500_df is None or sp500_df.empty:
        return pd.Series(dtype=float, name="correlation_breakdown")

    # Calculate returns
    xu100_returns = xu100_df["Close"].pct_change()
    sp500_returns = sp500_df["Close"].pct_change()

    # Align the two series by their index
    xu100_returns = xu100_returns.dropna()
    sp500_returns = sp500_returns.dropna()

    # Find common dates
    common_index = xu100_returns.index.intersection(sp500_returns.index)

    if len(common_index) < 60:
        return pd.Series(dtype=float, name="correlation_breakdown")

    # Combine into single DataFrame for correlation calculation
    combined = pd.DataFrame(
        {"xu100": xu100_returns.loc[common_index], "sp500": sp500_returns.loc[common_index]}
    )

    # Calculate rolling correlation
    rolling_corr = combined["xu100"].rolling(60).corr(combined["sp500"])

    # Breakdown = 1 - correlation (higher value = more breakdown = more fear)
    correlation_breakdown = 1 - rolling_corr

    # Set the series name
    correlation_breakdown.name = "correlation_breakdown"
    return correlation_breakdown
