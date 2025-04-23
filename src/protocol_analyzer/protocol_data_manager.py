"""
Protocol Data Manager

This module implements a data manager for retrieving, processing, and storing 
protocol metrics from various sources (node APIs, indexed data, external APIs).
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

import numpy as np
import pandas as pd

from src.models.protocol_data import (
    ProtocolMetric, 
    MetricThreshold,
    MetricCategory,
    ThresholdType
)

logger = logging.getLogger(__name__)


class ProtocolDataManager:
    """
    Manages protocol metrics data collection, storage, and retrieval.
    
    This class is responsible for:
    1. Retrieving metrics from various data sources
    2. Processing and normalizing data
    3. Storing metrics for analysis
    4. Providing threshold definitions for alerting
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the protocol data manager.
        
        Args:
            config: Configuration dictionary with API endpoints, 
                   credentials, and other settings
        """
        self.config = config or {}
        self._metrics_cache = {}
        self._thresholds = self._load_default_thresholds()
        
    def get_metric_data(
        self, 
        metric_type: str, 
        days: int = 30,
        resolution: str = "1d"
    ) -> List[ProtocolMetric]:
        """
        Retrieve historical data for a specific metric.
        
        Args:
            metric_type: Type of metric to retrieve
            days: Number of days of historical data
            resolution: Data resolution (1h, 1d, etc.)
            
        Returns:
            List of ProtocolMetric objects
        """
        # In a real implementation, this would fetch from a database or API
        # For demo purposes, generate synthetic data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        if resolution == "1d":
            date_range = pd.date_range(start=start_date, end=end_date, freq="D")
        elif resolution == "1h":
            date_range = pd.date_range(start=start_date, end=end_date, freq="H")
        else:
            raise ValueError(f"Unsupported resolution: {resolution}")
            
        # Generate synthetic data based on metric type
        values = self._generate_synthetic_data(metric_type, len(date_range))
        
        return [
            ProtocolMetric(
                metric_type=metric_type,
                value=float(value),
                timestamp=timestamp,
                category=self._get_category_for_metric(metric_type),
                unit=self._get_unit_for_metric(metric_type)
            )
            for timestamp, value in zip(date_range, values)
        ]
    
    def get_metric_thresholds(self, metric_type: Optional[str] = None) -> List[MetricThreshold]:
        """
        Get threshold definitions for metrics.
        
        Args:
            metric_type: Optional filter for specific metric type
            
        Returns:
            List of threshold definitions
        """
        if metric_type:
            return [t for t in self._thresholds if t.metric_type == metric_type]
        return self._thresholds
        
    def _generate_synthetic_data(self, metric_type: str, n_points: int) -> np.ndarray:
        """Generate synthetic data for demo purposes"""
        np.random.seed(hash(metric_type) % 10000)  # Consistent randomness per metric
        
        # Base pattern with some trend and seasonality
        x = np.linspace(0, 4 * np.pi, n_points)
        trend = 0.1 * x
        seasonality = 2 * np.sin(x)
        noise = np.random.normal(0, 0.5, n_points)
        
        # Add occasional spikes/anomalies
        anomaly_indices = np.random.choice(n_points, size=max(1, n_points // 20), replace=False)
        anomalies = np.zeros(n_points)
        anomalies[anomaly_indices] = np.random.normal(0, 3, len(anomaly_indices))
        
        # Different metrics have different patterns
        if "gas" in metric_type:
            base = 50 + trend + 10 * seasonality + noise + anomalies
        elif "transaction" in metric_type:
            base = 1000 + 500 * np.sin(x/2) + 20 * noise + anomalies * 100
        elif "staking" in metric_type:
            base = 30 + np.cumsum(np.random.normal(0, 0.05, n_points))
        elif "activity" in metric_type:
            base = 500 + 50 * seasonality + 10 * noise + anomalies * 50
        elif "price" in metric_type or "value" in metric_type:
            base = 1800 + 200 * np.sin(x/4) + np.cumsum(np.random.normal(0, 1, n_points))
        else:
            # Generic pattern
            base = 100 + trend + seasonality + noise + anomalies
            
        # Ensure no negative values for metrics that don't make sense as negative
        if any(s in metric_type for s in ["count", "gas", "fee", "size", "time"]):
            base = np.maximum(base, 0)
            
        return base
    
    def _get_category_for_metric(self, metric_type: str) -> MetricCategory:
        """Map metric type to a category"""
        if any(s in metric_type for s in ["transaction", "block", "gas", "node", "network"]):
            return MetricCategory.NETWORK
        elif any(s in metric_type for s in ["price", "fee", "value", "market", "reward"]):
            return MetricCategory.ECONOMICS
        elif any(s in metric_type for s in ["validator", "consensus", "fork", "finality"]):
            return MetricCategory.CONSENSUS
        elif any(s in metric_type for s in ["attack", "vulnerability", "security"]):
            return MetricCategory.SECURITY
        elif any(s in metric_type for s in ["user", "wallet", "activity", "adoption"]):
            return MetricCategory.USER
        elif any(s in metric_type for s in ["l2", "rollup", "optimism", "arbitrum", "zk"]):
            return MetricCategory.LAYER2
        else:
            return MetricCategory.OTHER
    
    def _get_unit_for_metric(self, metric_type: str) -> str:
        """Determine appropriate unit based on metric type"""
        if "gas" in metric_type:
            return "gwei"
        elif "price" in metric_type or "value" in metric_type or "cost" in metric_type:
            return "USD"
        elif "time" in metric_type or "duration" in metric_type:
            return "seconds"
        elif "size" in metric_type:
            return "bytes"
        elif "percentage" in metric_type or metric_type.endswith("_rate"):
            return "%"
        else:
            return "count"
    
    def _load_default_thresholds(self) -> List[MetricThreshold]:
        """Load default threshold definitions"""
        return [
            # Network metrics
            MetricThreshold(
                metric_type="gas_price",
                threshold_type=ThresholdType.UPPER,
                value=100,
                severity="medium",
                description="Gas price is abnormally high"
            ),
            MetricThreshold(
                metric_type="transaction_count",
                threshold_type=ThresholdType.LOWER,
                value=500,
                severity="low",
                description="Transaction volume is unusually low"
            ),
            MetricThreshold(
                metric_type="block_time",
                threshold_type=ThresholdType.UPPER,
                value=15,
                severity="high",
                description="Block time is significantly increased"
            ),
            
            # Economic metrics
            MetricThreshold(
                metric_type="eth_price",
                threshold_type=ThresholdType.RATE_OF_CHANGE,
                value=-0.1,  # 10% drop
                severity="medium",
                description="ETH price dropped significantly in 24h"
            ),
            MetricThreshold(
                metric_type="total_value_locked",
                threshold_type=ThresholdType.RATE_OF_CHANGE,
                value=-0.2,  # 20% drop
                severity="high",
                description="Total value locked decreased significantly"
            ),
            
            # Consensus metrics
            MetricThreshold(
                metric_type="validator_participation",
                threshold_type=ThresholdType.LOWER,
                value=0.9,  # 90%
                severity="high",
                description="Validator participation below healthy threshold"
            ),
            MetricThreshold(
                metric_type="missed_attestations",
                threshold_type=ThresholdType.UPPER,
                value=0.05,  # 5%
                severity="medium",
                description="High rate of missed attestations"
            ),
            
            # Security metrics
            MetricThreshold(
                metric_type="uncle_rate",
                threshold_type=ThresholdType.UPPER,
                value=0.05,
                severity="medium",
                description="Uncle rate indicates potential network issues"
            ),
            MetricThreshold(
                metric_type="reorg_count",
                threshold_type=ThresholdType.UPPER,
                value=0,
                severity="critical",
                description="Chain reorganizations detected"
            ),
            
            # User metrics
            MetricThreshold(
                metric_type="active_addresses",
                threshold_type=ThresholdType.RATE_OF_CHANGE,
                value=-0.15,  # 15% drop
                severity="low",
                description="Significant drop in active addresses"
            ),
            MetricThreshold(
                metric_type="new_addresses",
                threshold_type=ThresholdType.RATE_OF_CHANGE,
                value=-0.3,  # 30% drop
                severity="low",
                description="Significant drop in new address creation"
            ),
        ] 