import logging

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

from config import BacktestConfig


logger = logging.getLogger(__name__)


def _merge_data(fear_index_df: pd.DataFrame, xu100_df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Merging fear index with XU100 data")

    # Extract close prices from XU100
    xu100_close = xu100_df[["Close"]].rename(columns={"Close": "xu100_close"})

    # Merge on date index
    merged = fear_index_df.join(xu100_close, how="inner")

    # Calculate returns
    merged["xu100_return"] = merged["xu100_close"].pct_change()
    merged["xu100_abs_return"] = merged["xu100_return"].abs()

    # Calculate next-day return for predictive metrics
    merged["next_day_return"] = merged["xu100_return"].shift(-1)
    merged["next_day_abs_return"] = merged["xu100_abs_return"].shift(-1)

    # Drop NaN rows
    merged = merged.dropna()

    logger.info(f"Merged data shape: {merged.shape}")
    return merged


def _calculate_correlation(merged_df: pd.DataFrame) -> float:
    logger.info("Calculating Spearman correlation")

    # Correlation between fear index and next-day absolute return
    corr, p_value = spearmanr(merged_df["fear_index"], merged_df["next_day_abs_return"])

    logger.info(f"Spearman correlation: {corr:.4f} (p-value: {p_value:.4e})")
    return corr


def _calculate_roc_auc(merged_df: pd.DataFrame, crash_threshold: float) -> float:
    logger.info(f"Calculating ROC-AUC for crash prediction (threshold: {crash_threshold*100:.1f}%)")

    # Define crash days
    merged_df["crash_day"] = (merged_df["next_day_return"] < crash_threshold).astype(int)

    if merged_df["crash_day"].sum() < 2:
        logger.warning("Insufficient crash days for ROC-AUC calculation")
        return 0.0

    # Higher fear index should predict crash days
    roc_auc = roc_auc_score(merged_df["crash_day"], merged_df["fear_index"])

    logger.info(f"ROC-AUC: {roc_auc:.4f} (crash days: {merged_df['crash_day'].sum()})")
    return roc_auc


def _calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float) -> float:
    excess_returns = returns - risk_free_rate / 252
    if excess_returns.std() == 0:
        return 0.0
    return (excess_returns.mean() / excess_returns.std()) * (252**0.5)


def _backtest_overlay_strategy(merged_df: pd.DataFrame, config: BacktestConfig) -> dict:
    logger.info("Backtesting overlay strategy")

    # Calculate exposure based on fear index
    def calculate_exposure(fear_level):
        if fear_level > config.high_fear_threshold:
            return 0.0
        elif fear_level < config.low_fear_threshold:
            return 1.0
        else:
            # Linear interpolation between thresholds
            range_size = config.high_fear_threshold - config.low_fear_threshold
            return 1.0 - (fear_level - config.low_fear_threshold) / range_size

    merged_df["exposure"] = merged_df["fear_index"].apply(calculate_exposure)

    # Calculate strategy returns
    merged_df["strategy_return"] = merged_df["exposure"] * merged_df["xu100_return"]

    # Calculate cumulative returns
    merged_df["xu100_cumulative"] = (1 + merged_df["xu100_return"]).cumprod()
    merged_df["strategy_cumulative"] = (1 + merged_df["strategy_return"]).cumprod()

    # Calculate metrics
    sharpe_xu100 = _calculate_sharpe_ratio(merged_df["xu100_return"], config.risk_free_rate)
    sharpe_strategy = _calculate_sharpe_ratio(merged_df["strategy_return"], config.risk_free_rate)

    total_return_xu100 = merged_df["xu100_cumulative"].iloc[-1] - 1
    total_return_strategy = merged_df["strategy_cumulative"].iloc[-1] - 1

    results = {
        "sharpe_xu100": sharpe_xu100,
        "sharpe_strategy": sharpe_strategy,
        "total_return_xu100": total_return_xu100,
        "total_return_strategy": total_return_strategy,
        "merged_df": merged_df,
    }

    logger.info(f"XU100 Sharpe: {sharpe_xu100:.4f}, Strategy Sharpe: {sharpe_strategy:.4f}")
    logger.info(
        f"XU100 Return: {total_return_xu100*100:.2f}%, Strategy Return: {total_return_strategy*100:.2f}%"
    )

    return results


def _plot_results(merged_df: pd.DataFrame, metrics: dict):
    logger.info("Generating backtest plots")

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    # Plot 1: Fear Index vs XU100
    ax1 = axes[0]
    ax1_twin = ax1.twinx()

    ax1.plot(merged_df.index, merged_df["fear_index"], color="red", label="Fear Index")
    ax1_twin.plot(merged_df.index, merged_df["xu100_close"], color="blue", alpha=0.6, label="XU100")

    ax1.set_ylabel("Fear Index", color="red")
    ax1_twin.set_ylabel("XU100 Close", color="blue")
    ax1.set_title("Fear Index vs XU100")
    ax1.grid(True, alpha=0.3)

    # Plot 2: Strategy Equity Curves
    ax2 = axes[1]
    ax2.plot(merged_df.index, merged_df["xu100_cumulative"], label="XU100 Buy & Hold")
    ax2.plot(merged_df.index, merged_df["strategy_cumulative"], label="Fear-Based Strategy")
    ax2.set_ylabel("Cumulative Return")
    ax2.set_title("Strategy Performance")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Rolling Correlation
    ax3 = axes[2]
    rolling_corr = merged_df["fear_index"].rolling(60).corr(merged_df["next_day_abs_return"])
    ax3.plot(merged_df.index, rolling_corr)
    ax3.axhline(y=0, color="black", linestyle="--", alpha=0.5)
    ax3.set_ylabel("Correlation")
    ax3.set_title("60-Day Rolling Correlation: Fear Index vs Next-Day Absolute Return")
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("bifx_backtest_results.png", dpi=150)
    logger.info("Plots saved to bifx_backtest_results.png")
    plt.close()


def run_backtest(
    fear_index_df: pd.DataFrame, xu100_df: pd.DataFrame, config: BacktestConfig = None
) -> dict:
    if config is None:
        config = BacktestConfig()

    logger.info("Starting backtest")

    # Merge data
    merged_df = _merge_data(fear_index_df, xu100_df)

    if merged_df.empty:
        logger.error("Cannot run backtest: merged data is empty")
        return {}

    # Calculate metrics
    correlation = _calculate_correlation(merged_df)
    roc_auc = _calculate_roc_auc(merged_df, config.crash_threshold)
    strategy_results = _backtest_overlay_strategy(merged_df, config)

    metrics = {
        "correlation": correlation,
        "roc_auc": roc_auc,
        "sharpe_xu100": strategy_results["sharpe_xu100"],
        "sharpe_strategy": strategy_results["sharpe_strategy"],
        "total_return_xu100": strategy_results["total_return_xu100"],
        "total_return_strategy": strategy_results["total_return_strategy"],
    }

    # Plot results
    if config.plot_results:
        _plot_results(strategy_results["merged_df"], metrics)

    logger.info("Backtest complete")

    return metrics
