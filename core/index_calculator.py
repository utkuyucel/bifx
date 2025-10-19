import logging

import pandas as pd

from config import IndexConfig


logger = logging.getLogger(__name__)


def _normalize_zscore_minmax(series: pd.Series, min_val: float, max_val: float) -> pd.Series:
    # Drop NaN values for calculation
    series_clean = series.dropna()

    if len(series_clean) < 10:
        return pd.Series(50.0, index=series.index)

    # Use robust scaling with percentiles
    p01 = series_clean.quantile(0.01)
    p99 = series_clean.quantile(0.99)

    if p99 == p01:
        return pd.Series(50.0, index=series.index)

    # Normalize to 0-1 range
    normalized = (series - p01) / (p99 - p01)

    # Scale to target range and clip
    scaled = normalized * (max_val - min_val) + min_val
    return scaled.clip(min_val, max_val)


def _normalize_features(feature_df: pd.DataFrame, config: IndexConfig) -> pd.DataFrame:
    logger.info("Normalizing features")

    normalized = pd.DataFrame(index=feature_df.index)

    for col in feature_df.columns:
        if feature_df[col].std() == 0 or feature_df[col].isna().all():
            logger.warning(f"Feature {col} has zero variance or all NaN, skipping")
            continue

        normalized[col] = _normalize_zscore_minmax(
            feature_df[col], config.min_value, config.max_value
        )

    return normalized


def _apply_weights(normalized_df: pd.DataFrame, weights: dict) -> pd.Series:
    logger.info("Applying feature weights")

    # Initialize result series
    weighted_sum = pd.Series(0.0, index=normalized_df.index)
    weights_used = pd.Series(0.0, index=normalized_df.index)

    # Apply weights for each feature, handling NaN values per row
    for col in normalized_df.columns:
        weight = weights.get(col, 0.0)
        if weight > 0:
            # Only add where values are not NaN
            valid_mask = normalized_df[col].notna()
            weighted_sum[valid_mask] += normalized_df.loc[valid_mask, col] * weight
            weights_used[valid_mask] += weight

    # Normalize by total weight per row
    # Weights are fractions that sum to 1.0, features are 0-100
    # So weighted average of 0-100 values should also be 0-100
    result = weighted_sum / weights_used

    # Replace inf/NaN with NaN (happens when no features available for a row)
    result = result.replace([float("inf"), float("-inf")], float("nan"))

    return result


def _apply_ema_smoothing(series: pd.Series, span: int) -> pd.Series:
    logger.info(f"Applying EMA smoothing with span={span}")
    return series.ewm(span=span, adjust=False).mean()


def calculate_fear_index(feature_df: pd.DataFrame, config: IndexConfig = None) -> pd.DataFrame:
    if config is None:
        config = IndexConfig()

    if feature_df.empty:
        logger.error("Cannot calculate fear index: feature_df is empty")
        return pd.DataFrame()

    logger.info(f"Calculating fear index from {len(feature_df.columns)} features")

    # Normalize features to 0-100 scale
    normalized_df = _normalize_features(feature_df, config)

    if normalized_df.empty:
        logger.error("All features failed normalization")
        return pd.DataFrame()

    # Apply weights and compute raw fear index
    fear_index_raw = _apply_weights(normalized_df, config.default_weights)

    # Apply EMA smoothing
    fear_index_smoothed = _apply_ema_smoothing(fear_index_raw, config.ema_span)

    # Final clipping to ensure range
    fear_index_smoothed = fear_index_smoothed.clip(config.min_value, config.max_value)

    # Create output DataFrame
    result = pd.DataFrame({"fear_index": fear_index_smoothed})

    logger.info(
        f"Fear index calculated. Mean: {fear_index_smoothed.mean():.2f}, "
        f"Std: {fear_index_smoothed.std():.2f}, "
        f"Range: [{fear_index_smoothed.min():.2f}, {fear_index_smoothed.max():.2f}]"
    )

    return result
