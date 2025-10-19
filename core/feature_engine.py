import logging
from importlib import import_module
from pathlib import Path

import pandas as pd


logger = logging.getLogger(__name__)


def _discover_features(features_dir: Path) -> list[str]:
    features = []
    for file_path in features_dir.glob("*.py"):
        if file_path.name != "__init__.py":
            module_name = file_path.stem
            features.append(module_name)

    logger.info(f"Discovered {len(features)} feature modules: {features}")
    return features


def _execute_feature(module_name: str, data: dict) -> pd.Series:
    try:
        module = import_module(f"features.{module_name}")

        if not hasattr(module, "compute"):
            logger.error(f"Feature {module_name} missing compute() function")
            return None

        logger.info(f"Computing feature: {module_name}")
        result = module.compute(data)

        if not isinstance(result, pd.Series):
            logger.error(f"Feature {module_name} returned {type(result)}, expected pd.Series")
            return None

        return result

    except Exception as e:
        logger.error(f"Failed to execute feature {module_name}: {e}", exc_info=True)
        return None


def compute_all_features(data: dict, features_dir: Path = None) -> pd.DataFrame:
    if features_dir is None:
        features_dir = Path(__file__).parent.parent / "features"

    logger.info("Starting feature computation")

    feature_modules = _discover_features(features_dir)

    if not feature_modules:
        logger.warning("No feature modules found")
        return pd.DataFrame()

    feature_series = {}

    for module_name in feature_modules:
        result = _execute_feature(module_name, data)
        if result is not None and not result.empty:
            feature_series[module_name] = result

    if not feature_series:
        logger.warning("No features successfully computed")
        return pd.DataFrame()

    # Combine all features into single DataFrame
    feature_df = pd.DataFrame(feature_series)

    logger.info(f"Feature computation complete. Shape: {feature_df.shape}")
    logger.info(f"Features: {list(feature_df.columns)}")

    # Check and log features with high null percentage
    _check_null_percentage(feature_df, threshold=0.30)

    return feature_df


def _check_null_percentage(feature_df: pd.DataFrame, threshold: float = 0.30) -> None:
    """Log warning for features with null percentage above threshold."""
    if feature_df.empty:
        return

    total_rows = len(feature_df)
    high_null_features = []

    for col in feature_df.columns:
        null_count = feature_df[col].isnull().sum()
        null_percentage = null_count / total_rows

        if null_percentage > threshold:
            high_null_features.append((col, null_percentage, null_count))
            logger.warning(
                f"Feature '{col}' has {null_percentage*100:.1f}% null values "
                f"({null_count}/{total_rows} rows) - exceeds {threshold*100:.0f}% threshold"
            )

    if high_null_features:
        logger.warning(
            f"Total features with >{threshold*100:.0f}% nulls: {len(high_null_features)}"
        )
    else:
        logger.info(f"All features have <{threshold*100:.0f}% null values")
