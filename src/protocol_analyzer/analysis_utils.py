"""
Analysis Utilities

This module provides utility functions for analyzing Ethereum protocol data.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import logging
from src.models.protocol_data import ProtocolMetric

logger = logging.getLogger(__name__)


def calculate_growth_rate(
    metrics: List[ProtocolMetric], 
    time_period_days: int = 30
) -> float:
    """
    Calculate the growth rate for a metric over the specified time period.
    
    Args:
        metrics: List of ProtocolMetric objects sorted by timestamp
        time_period_days: Time period in days to calculate growth over
        
    Returns:
        Growth rate as a decimal (e.g., 0.05 for 5% growth)
    """
    if not metrics or len(metrics) < 2:
        logger.warning("Not enough data points to calculate growth rate")
        return 0.0
    
    # Sort metrics by timestamp
    sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
    
    # Get the most recent value
    latest_value = sorted_metrics[-1].value
    latest_timestamp = sorted_metrics[-1].timestamp
    
    # Find the value from time_period_days ago
    target_timestamp = latest_timestamp - timedelta(days=time_period_days)
    
    # Find the closest metric to target_timestamp
    closest_metric = sorted_metrics[0]
    for metric in sorted_metrics:
        if abs((metric.timestamp - target_timestamp).total_seconds()) < \
           abs((closest_metric.timestamp - target_timestamp).total_seconds()):
            closest_metric = metric
    
    previous_value = closest_metric.value
    
    # Handle edge case where previous value is 0
    if previous_value == 0:
        logger.warning("Previous value is 0, cannot calculate percentage growth")
        return 1.0 if latest_value > 0 else 0.0
    
    # Calculate growth rate
    growth_rate = (latest_value - previous_value) / previous_value
    
    return growth_rate


def detect_outliers(
    metrics: List[ProtocolMetric],
    n_std: float = 2.0
) -> List[ProtocolMetric]:
    """
    Detect outliers in metric values using standard deviation.
    
    Args:
        metrics: List of ProtocolMetric objects
        n_std: Number of standard deviations to use as threshold
        
    Returns:
        List of metrics that are outliers
    """
    if not metrics or len(metrics) < 3:
        logger.warning("Not enough data points to detect outliers")
        return []
    
    values = [m.value for m in metrics]
    mean = np.mean(values)
    std = np.std(values)
    
    threshold = n_std * std
    outliers = [m for m in metrics if abs(m.value - mean) > threshold]
    
    return outliers


def calculate_correlation(
    metrics_a: List[ProtocolMetric],
    metrics_b: List[ProtocolMetric]
) -> Optional[float]:
    """
    Calculate the correlation coefficient between two sets of metrics.
    
    Args:
        metrics_a: First list of ProtocolMetric objects
        metrics_b: Second list of ProtocolMetric objects
        
    Returns:
        Correlation coefficient or None if calculation is not possible
    """
    if not metrics_a or not metrics_b or len(metrics_a) < 2 or len(metrics_b) < 2:
        logger.warning("Not enough data points to calculate correlation")
        return None
    
    # Match metrics by timestamp
    paired_values = []
    
    # Create dictionary of timestamps for the second metric list
    metrics_b_dict = {m.timestamp.isoformat(): m.value for m in metrics_b}
    
    for metric_a in metrics_a:
        timestamp_a = metric_a.timestamp.isoformat()
        if timestamp_a in metrics_b_dict:
            paired_values.append((metric_a.value, metrics_b_dict[timestamp_a]))
    
    if len(paired_values) < 2:
        logger.warning("Not enough matching timestamps to calculate correlation")
        return None
    
    # Calculate correlation
    a_values = [p[0] for p in paired_values]
    b_values = [p[1] for p in paired_values]
    
    try:
        correlation = np.corrcoef(a_values, b_values)[0, 1]
        return correlation
    except Exception as e:
        logger.error(f"Error calculating correlation: {e}")
        return None


def forecast_trend(
    metrics: List[ProtocolMetric], 
    days_ahead: int = 30
) -> Tuple[float, float]:
    """
    Forecast the trend for a metric using simple linear regression.
    
    Args:
        metrics: List of ProtocolMetric objects sorted by timestamp
        days_ahead: Number of days ahead to forecast
        
    Returns:
        Tuple of (forecasted_value, confidence)
    """
    if not metrics or len(metrics) < 3:
        logger.warning("Not enough data points to forecast trend")
        return (metrics[-1].value if metrics else 0.0, 0.0)
    
    # Sort metrics by timestamp
    sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
    
    # Convert timestamps to days since first measurement
    first_timestamp = sorted_metrics[0].timestamp
    x = [(m.timestamp - first_timestamp).total_seconds() / 86400 for m in sorted_metrics]
    y = [m.value for m in sorted_metrics]
    
    # Perform linear regression
    try:
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs
        
        # Calculate R-squared as confidence measure
        y_pred = np.polyval(coeffs, x)
        ss_total = np.sum((y - np.mean(y))**2)
        ss_residual = np.sum((y - y_pred)**2)
        r_squared = 1 - (ss_residual / ss_total) if ss_total != 0 else 0
        
        # Forecast
        forecast_x = x[-1] + days_ahead
        forecast_value = slope * forecast_x + intercept
        
        return (forecast_value, r_squared)
    except Exception as e:
        logger.error(f"Error forecasting trend: {e}")
        return (sorted_metrics[-1].value, 0.0)


def identify_change_points(
    metrics: List[ProtocolMetric],
    threshold_ratio: float = 0.2
) -> List[ProtocolMetric]:
    """
    Identify significant change points in a metric time series.
    
    Args:
        metrics: List of ProtocolMetric objects sorted by timestamp
        threshold_ratio: Minimum change ratio to be considered significant
        
    Returns:
        List of metrics at change points
    """
    if not metrics or len(metrics) < 3:
        logger.warning("Not enough data points to identify change points")
        return []
    
    # Sort metrics by timestamp
    sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
    
    change_points = []
    for i in range(1, len(sorted_metrics)):
        prev_value = sorted_metrics[i-1].value
        curr_value = sorted_metrics[i].value
        
        if prev_value == 0:
            if curr_value != 0:
                change_points.append(sorted_metrics[i])
        else:
            change_ratio = abs(curr_value - prev_value) / prev_value
            if change_ratio > threshold_ratio:
                change_points.append(sorted_metrics[i])
    
    return change_points


def extract_seasonal_patterns(
    metrics: List[ProtocolMetric],
    period_days: int = 7
) -> Dict[str, Any]:
    """
    Extract seasonal patterns from metric time series.
    
    Args:
        metrics: List of ProtocolMetric objects sorted by timestamp
        period_days: Expected period length in days
        
    Returns:
        Dictionary with pattern information
    """
    if not metrics or len(metrics) < period_days*2:
        logger.warning(f"Not enough data points to extract {period_days}-day patterns")
        return {"detected": False, "confidence": 0.0, "details": {}}
    
    # Sort metrics by timestamp
    sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
    
    # Group metrics by day of week (for weekly patterns)
    if period_days == 7:
        day_groups = [[] for _ in range(7)]
        for metric in sorted_metrics:
            day_of_week = metric.timestamp.weekday()
            day_groups[day_of_week].append(metric.value)
        
        # Calculate average and std for each day
        day_stats = []
        for day, values in enumerate(day_groups):
            if values:
                day_stats.append({
                    "day": day,
                    "avg_value": np.mean(values),
                    "std_value": np.std(values),
                    "sample_size": len(values)
                })
        
        # Calculate day-to-day variation
        day_avgs = [s["avg_value"] for s in day_stats if "avg_value" in s]
        if day_avgs:
            max_day = max(day_avgs)
            min_day = min(day_avgs)
            overall_avg = np.mean(day_avgs)
            
            variation = (max_day - min_day) / overall_avg if overall_avg != 0 else 0
            
            return {
                "detected": variation > 0.1,  # 10% variation threshold
                "confidence": min(1.0, variation * 3),  # Scale confidence
                "details": {
                    "day_stats": day_stats,
                    "max_day_value": max_day,
                    "min_day_value": min_day,
                    "variation_ratio": variation
                }
            }
    
    # Generic implementation for other periods
    return {"detected": False, "confidence": 0.0, "details": {}}


def calculate_threshold_crossing_times(
    metrics: List[ProtocolMetric],
    threshold: float
) -> Dict[str, Any]:
    """
    Calculate when a metric will cross a threshold based on current trend.
    
    Args:
        metrics: List of ProtocolMetric objects sorted by timestamp
        threshold: The threshold value
        
    Returns:
        Dictionary with crossing information
    """
    if not metrics or len(metrics) < 3:
        logger.warning("Not enough data points to calculate threshold crossing")
        return {"will_cross": False, "days_until_crossing": None}
    
    # Sort metrics by timestamp
    sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
    
    # Get current trend using last 10 points or all if fewer
    recent_metrics = sorted_metrics[-min(10, len(sorted_metrics)):]
    
    # Convert timestamps to days since first measurement
    first_timestamp = recent_metrics[0].timestamp
    x = [(m.timestamp - first_timestamp).total_seconds() / 86400 for m in recent_metrics]
    y = [m.value for m in recent_metrics]
    
    # Current value
    current_value = y[-1]
    
    # Check if already crossed
    if (current_value >= threshold and sorted_metrics[0].value < threshold) or \
       (current_value <= threshold and sorted_metrics[0].value > threshold):
        return {"will_cross": True, "days_until_crossing": 0}
    
    # Perform linear regression
    try:
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs
        
        # If slope is near zero, won't cross
        if abs(slope) < 1e-6:
            return {"will_cross": False, "days_until_crossing": None}
        
        # Calculate days until crossing
        days_until_crossing = (threshold - intercept) / slope - x[-1]
        
        will_cross = (days_until_crossing > 0)
        
        if will_cross:
            return {
                "will_cross": True,
                "days_until_crossing": days_until_crossing,
                "direction": "up" if slope > 0 else "down",
                "confidence": min(1.0, abs(slope) / (abs(current_value) + 1e-6))
            }
        else:
            return {"will_cross": False, "days_until_crossing": None}
            
    except Exception as e:
        logger.error(f"Error calculating threshold crossing: {e}")
        return {"will_cross": False, "days_until_crossing": None} 