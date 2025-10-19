import logging
from pathlib import Path

from core.backtest import run_backtest
from core.data_loader import load_data
from core.feature_engine import compute_all_features
from core.index_calculator import calculate_fear_index


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 80)
    logger.info("BIFX Pipeline Started")
    logger.info("=" * 80)

    # Load all data sources
    logger.info("Step 1/4: Loading data...")
    data = load_data()

    if not data or all(df.empty for df in data.values()):
        logger.error("No data loaded. Exiting.")
        return

    # Compute all features
    logger.info("\nStep 2/4: Computing features...")
    features = compute_all_features(data)

    if features.empty:
        logger.error("No features computed. Exiting.")
        return

    logger.info(f"Computed {len(features.columns)} features: {list(features.columns)}")

    # Calculate fear index
    logger.info("\nStep 3/4: Calculating fear index...")
    fear_index = calculate_fear_index(features)

    if fear_index.empty:
        logger.error("Fear index calculation failed. Exiting.")
        return

    # Run backtest
    logger.info("\nStep 4/4: Running backtest...")

    if data.get("XU100") is None or data["XU100"].empty:
        logger.error("XU100 data not available for backtest. Exiting.")
        return

    metrics = run_backtest(fear_index, data["XU100"])

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("BIFX Pipeline Complete - Summary")
    logger.info("=" * 80)
    logger.info(f"Data period: {fear_index.index.min()} to {fear_index.index.max()}")
    logger.info(f"Total observations: {len(fear_index)}")
    logger.info("\nBacktest Metrics:")
    logger.info(f"  Spearman Correlation: {metrics.get('correlation', 0):.4f}")
    logger.info(f"  ROC-AUC (Crash Pred): {metrics.get('roc_auc', 0):.4f}")
    logger.info(f"  XU100 Sharpe Ratio:   {metrics.get('sharpe_xu100', 0):.4f}")
    logger.info(f"  Strategy Sharpe:      {metrics.get('sharpe_strategy', 0):.4f}")
    logger.info(f"  XU100 Total Return:   {metrics.get('total_return_xu100', 0)*100:.2f}%")
    logger.info(f"  Strategy Return:      {metrics.get('total_return_strategy', 0)*100:.2f}%")
    logger.info("=" * 80)

    # Save fear index to CSV
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "bifx_fear_index.csv"
    fear_index.to_csv(output_path)
    logger.info(f"\nFear index saved to: {output_path}")


if __name__ == "__main__":
    main()
