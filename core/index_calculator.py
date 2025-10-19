import logging

import pandas as pd

from config import IndexConfig


logger = logging.getLogger(__name__)


def _normalize_zscore_minmax(series: pd.Series, min_val: float, max_val: float) -> pd.Series:
    # First convert to z-score
    z_score = (series - series.mean()) / series.std()

    # Then normalize to 0-1 range using robust scaling
    z_min, z_max = z_score.quantile(0.01), z_score.quantile(0.99)
    normalized = (z_score - z_min) / (z_max - z_min)

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

    weighted_sum = pd.Series(0.0, index=normalized_df.index)
    total_weight = 0.0

    for col in normalized_df.columns:
        weight = weights.get(col, 0.0)
        if weight > 0:
            weighted_sum += normalized_df[col] * weight
            total_weight += weight

    # Normalize by total weight to ensure output stays in 0-100 range
    if total_weight > 0:
        weighted_sum = weighted_sum / total_weight * 100.0

    return weighted_sum


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
