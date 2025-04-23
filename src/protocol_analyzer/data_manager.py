"""
Protocol Data Manager

This module provides functionality to fetch, store, and retrieve protocol metrics
from various data sources like Ethereum nodes, APIs, and databases.
"""

import logging
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

import pandas as pd
import numpy as np

from src.models.protocol_data import (
    ProtocolMetric,
    MetricCategory,
    MetricThreshold,
    AlertSeverity,
    ThresholdType
)

logger = logging.getLogger(__name__)


class ProtocolDataManager:
    """Manager for protocol metrics data retrieval and storage"""
    
    def __init__(self, config=None):
        """
        Initialize the protocol data manager.
        
        Args:
            config: Configuration for data sources and credentials
        """
        self.config = config or {}
        self.metric_cache = {}
        self.thresholds = self._initialize_thresholds()
        
    def get_metric_data(self, metric_type: str, days: int = 30) -> List[ProtocolMetric]:
        """
        Get historical data for a specific metric.
        
        Args:
            metric_type: The type of metric to fetch
            days: Number of days of historical data to retrieve
            
        Returns:
            List of ProtocolMetric objects
        """
        # Check if data is in cache
        cache_key = f"{metric_type}_{days}"
        if cache_key in self.metric_cache:
            return self.metric_cache[cache_key]
        
        # In a real implementation, this would fetch data from APIs, nodes, etc.
        # For now, we'll generate synthetic data
        metrics = self._generate_synthetic_data(metric_type, days)
        
        # Cache the result
        self.metric_cache[cache_key] = metrics
        return metrics
    
    def get_metric_dataframe(self, metric_type: str, days: int = 30) -> pd.DataFrame:
        """
        Get historical data for a specific metric as a pandas DataFrame.
        
        Args:
            metric_type: The type of metric to fetch
            days: Number of days of historical data to retrieve
            
        Returns:
            DataFrame with timestamp index and metric values
        """
        metrics = self.get_metric_data(metric_type, days)
        
        # Convert to DataFrame
        data = {
            'timestamp': [m.timestamp for m in metrics],
            'value': [m.value for m in metrics]
        }
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        return df
    
    def get_related_metrics(self, primary_metric: str) -> List[str]:
        """
        Get a list of metrics that are related to the primary metric.
        
        Args:
            primary_metric: The primary metric to find relations for
            
        Returns:
            List of related metric types
        """
        # Define relationships between metrics
        relationships = {
            # Network metrics
            'network_peers': ['network_latency', 'block_propagation_time'],
            'network_bandwidth': ['transaction_throughput', 'uncle_rate'],
            'block_propagation_time': ['uncle_rate', 'network_latency'],
            
            # Economic metrics
            'gas_price': ['transaction_volume', 'block_fullness', 'transaction_fee_revenue'],
            'eth_price': ['transaction_volume', 'gas_price', 'total_value_locked'],
            'transaction_fee_revenue': ['validator_revenue', 'gas_price'],
            
            # Consensus metrics
            'validator_count': ['consensus_participation', 'staking_yield'],
            'staking_yield': ['validator_count', 'eth_price', 'transaction_fee_revenue'],
            'consensus_participation': ['validator_count', 'network_peers'],
            
            # User metrics
            'daily_active_addresses': ['transaction_volume', 'new_addresses'],
            'transaction_volume': ['gas_price', 'eth_price', 'daily_active_addresses'],
            'average_transaction_fee': ['gas_price', 'transaction_complexity'],
            
            # Layer 2 metrics
            'l2_total_value_locked': ['eth_price', 'l2_transaction_volume'],
            'l2_transaction_volume': ['transaction_fee_revenue', 'gas_price'],
            
            # Security metrics
            'hash_rate': ['uncle_rate', 'network_peers'],
            'uncle_rate': ['block_propagation_time', 'block_size'],
        }
        
        if primary_metric in relationships:
            return relationships[primary_metric]
        return []
    
    def get_thresholds(self, metric_type: str) -> List[MetricThreshold]:
        """
        Get defined thresholds for a specific metric.
        
        Args:
            metric_type: The type of metric
            
        Returns:
            List of threshold objects for the metric
        """
        return [t for t in self.thresholds if t.metric_type == metric_type]
    
    def _initialize_thresholds(self) -> List[MetricThreshold]:
        """
        Initialize predefined thresholds for various metrics.
        
        Returns:
            List of threshold objects
        """
        thresholds = [
            # Network metrics
            MetricThreshold(
                metric_type="network_peers",
                threshold_type=ThresholdType.LOWER,
                value=10,
                severity=AlertSeverity.HIGH,
                description="Network peer count is critically low"
            ),
            MetricThreshold(
                metric_type="block_propagation_time",
                threshold_type=ThresholdType.UPPER,
                value=1.5,
                severity=AlertSeverity.MEDIUM,
                description="Block propagation time is higher than normal"
            ),
            
            # Economic metrics
            MetricThreshold(
                metric_type="gas_price",
                threshold_type=ThresholdType.UPPER,
                value=100,
                severity=AlertSeverity.HIGH,
                description="Gas price is extremely high"
            ),
            MetricThreshold(
                metric_type="gas_price",
                threshold_type=ThresholdType.RATE_OF_CHANGE,
                value=0.5,
                severity=AlertSeverity.MEDIUM,
                description="Gas price is rapidly increasing"
            ),
            
            # Consensus metrics
            MetricThreshold(
                metric_type="consensus_participation",
                threshold_type=ThresholdType.LOWER,
                value=0.90,
                severity=AlertSeverity.CRITICAL,
                description="Participation rate is below critical threshold"
            ),
            
            # User metrics
            MetricThreshold(
                metric_type="transaction_volume",
                threshold_type=ThresholdType.RATE_OF_CHANGE,
                value=-0.3,
                severity=AlertSeverity.MEDIUM,
                description="Transaction volume is rapidly decreasing"
            ),
            
            # Security metrics
            MetricThreshold(
                metric_type="uncle_rate",
                threshold_type=ThresholdType.UPPER,
                value=0.05,
                severity=AlertSeverity.HIGH,
                description="Uncle rate is abnormally high"
            ),
        ]
        return thresholds
    
    def _get_metric_category(self, metric_type: str) -> MetricCategory:
        """Map metric type to its category"""
        category_map = {
            # Network metrics
            'network_peers': MetricCategory.NETWORK,
            'network_latency': MetricCategory.NETWORK,
            'block_propagation_time': MetricCategory.NETWORK,
            'network_bandwidth': MetricCategory.NETWORK,
            
            # Economic metrics
            'gas_price': MetricCategory.ECONOMICS,
            'eth_price': MetricCategory.ECONOMICS,
            'transaction_fee_revenue': MetricCategory.ECONOMICS,
            'total_value_locked': MetricCategory.ECONOMICS,
            
            # Consensus metrics
            'validator_count': MetricCategory.CONSENSUS,
            'staking_yield': MetricCategory.CONSENSUS,
            'consensus_participation': MetricCategory.CONSENSUS,
            'validator_revenue': MetricCategory.CONSENSUS,
            
            # User metrics
            'daily_active_addresses': MetricCategory.USER,
            'transaction_volume': MetricCategory.TRANSACTION,
            'average_transaction_fee': MetricCategory.TRANSACTION,
            'new_addresses': MetricCategory.USER,
            'transaction_complexity': MetricCategory.TRANSACTION,
            
            # Layer 2 metrics
            'l2_total_value_locked': MetricCategory.LAYER2,
            'l2_transaction_volume': MetricCategory.LAYER2,
            
            # Security metrics
            'hash_rate': MetricCategory.SECURITY,
            'uncle_rate': MetricCategory.SECURITY,
            'block_size': MetricCategory.TRANSACTION,
            'block_fullness': MetricCategory.TRANSACTION,
        }
        
        return category_map.get(metric_type, MetricCategory.NETWORK)
    
    def _generate_synthetic_data(self, metric_type: str, days: int) -> List[ProtocolMetric]:
        """Generate synthetic data for demonstration purposes"""
        metrics = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        category = self._get_metric_category(metric_type)
        
        # Generate a time series with trend and some noise
        # Different metrics have different baseline values and characteristics
        base_value_map = {
            'network_peers': 50,
            'network_latency': 100,  # ms
            'block_propagation_time': 0.8,  # seconds
            'gas_price': 30,  # gwei
            'eth_price': 2500,  # USD
            'transaction_fee_revenue': 1000,  # ETH
            'validator_count': 500000,
            'staking_yield': 4.0,  # percent
            'consensus_participation': 0.95,  # percentage as decimal
            'daily_active_addresses': 500000,
            'transaction_volume': 1000000,
            'average_transaction_fee': 5,  # USD
            'l2_total_value_locked': 10000000000,  # USD
            'l2_transaction_volume': 5000000,
            'hash_rate': 900,  # TH/s
            'uncle_rate': 0.01,  # percentage as decimal
            'network_bandwidth': 200,  # Mbps
            'new_addresses': 10000,
            'block_size': 2,  # MB
            'block_fullness': 0.8,  # percentage as decimal
            'total_value_locked': 20000000000,  # USD
            'transaction_complexity': 50000,  # gas units
            'validator_revenue': 5,  # ETH per day
        }
        
        volatility_map = {
            'eth_price': 0.05,
            'gas_price': 0.1,
            'transaction_volume': 0.08,
            'daily_active_addresses': 0.04,
            'l2_transaction_volume': 0.06,
        }
        
        trend_map = {
            'validator_count': 0.001,  # slowly increasing
            'daily_active_addresses': 0.002,  # slowly increasing
            'l2_total_value_locked': 0.003,  # more rapidly increasing
            'transaction_volume': -0.0005,  # slightly decreasing
        }
        
        # Get baseline values for this metric
        base_value = base_value_map.get(metric_type, 100)
        volatility = volatility_map.get(metric_type, 0.02)
        trend = trend_map.get(metric_type, 0)
        
        # Generate time series
        current_date = start_date
        current_value = base_value
        
        while current_date <= end_date:
            # Add random walk with trend
            current_value = current_value * (1 + np.random.normal(trend, volatility))
            
            # Add some seasonality for certain metrics
            if metric_type in ['transaction_volume', 'daily_active_addresses', 'gas_price']:
                # Weekly pattern (higher on weekdays)
                if current_date.weekday() < 5:  # Monday to Friday
                    current_value *= 1.1
                else:  # Weekend
                    current_value *= 0.9
            
            # Ensure non-negative values
            current_value = max(current_value, 0.01 * base_value)
            
            # Create metric object
            metric = ProtocolMetric(
                metric_type=metric_type,
                value=current_value,
                timestamp=current_date,
                category=category,
                source="synthetic",
                tags={"environment": "development"}
            )
            metrics.append(metric)
            
            # Move to next day
            current_date += timedelta(days=1)
        
        return metrics 