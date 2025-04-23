"""
Protocol Analyzer

This module provides functionality to analyze protocol metrics,
detect anomalies, and generate insights and recommendations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from scipy import stats

from src.models.protocol_data import (
    ProtocolMetric, 
    ProtocolAlert,
    EIPRecommendation,
    InsightReport,
    AlertSeverity,
    MetricCategory,
    ThresholdType
)
from src.protocol_analyzer.data_manager import ProtocolDataManager

logger = logging.getLogger(__name__)


class ProtocolAnalyzer:
    """Analyzer for detecting protocol issues and generating insights"""
    
    def __init__(self, data_manager: ProtocolDataManager):
        """
        Initialize the protocol analyzer.
        
        Args:
            data_manager: Manager for protocol metrics data
        """
        self.data_manager = data_manager
    
    def generate_full_report(self, days: int = 30) -> InsightReport:
        """
        Generate a comprehensive protocol insight report.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Full insight report with metrics, alerts, and recommendations
        """
        # Define the key metrics to analyze
        key_metrics = [
            # Network metrics
            "network_peers",
            "block_propagation_time",
            "network_latency",
            
            # Economic metrics
            "gas_price",
            "transaction_fee_revenue",
            
            # Consensus metrics
            "validator_count",
            "consensus_participation",
            
            # User metrics
            "daily_active_addresses",
            "transaction_volume",
            
            # Security metrics
            "uncle_rate"
        ]
        
        # Gather data for all metrics
        all_metrics = []
        for metric_type in key_metrics:
            metrics = self.data_manager.get_metric_data(metric_type, days)
            all_metrics.extend(metrics)
        
        # Generate alerts
        alerts = self.detect_alerts(key_metrics, days)
        
        # Generate recommendations based on alerts
        recommendations = self.generate_recommendations(alerts)
        
        # Create the report
        report = InsightReport(
            metrics=all_metrics[-100:],  # Include only the most recent metrics to keep the report size manageable
            alerts=alerts,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
        
        return report
    
    def detect_alerts(self, metric_types: List[str], days: int = 30) -> List[ProtocolAlert]:
        """
        Detect protocol alerts based on thresholds and anomalies.
        
        Args:
            metric_types: List of metric types to analyze
            days: Number of days to analyze
            
        Returns:
            List of detected alerts
        """
        alerts = []
        
        for metric_type in metric_types:
            # Get metric data
            metrics = self.data_manager.get_metric_data(metric_type, days)
            if not metrics:
                continue
                
            # Get predefined thresholds for this metric
            thresholds = self.data_manager.get_thresholds(metric_type)
            
            # Convert to DataFrame for easier analysis
            df = self.data_manager.get_metric_dataframe(metric_type, days)
            
            # Check each threshold
            for threshold in thresholds:
                new_alerts = self._check_threshold(df, threshold)
                alerts.extend(new_alerts)
            
            # Detect anomalies (even if no thresholds are defined)
            anomaly_alerts = self._detect_anomalies(df, metric_type)
            alerts.extend(anomaly_alerts)
        
        # Sort alerts by severity and timestamp
        alerts.sort(key=lambda x: (
            -self._severity_to_value(x.severity),  # Sort by severity (descending)
            x.timestamp  # Then by timestamp (ascending)
        ))
        
        return alerts
    
    def generate_recommendations(self, alerts: List[ProtocolAlert]) -> List[EIPRecommendation]:
        """
        Generate protocol improvement recommendations based on detected alerts.
        
        Args:
            alerts: List of protocol alerts
            
        Returns:
            List of improvement recommendations
        """
        recommendations = []
        
        # Group alerts by metric type
        metric_alerts = {}
        for alert in alerts:
            if alert.metric_type not in metric_alerts:
                metric_alerts[alert.metric_type] = []
            metric_alerts[alert.metric_type].append(alert)
        
        # Analysis patterns
        if "gas_price" in metric_alerts and len(metric_alerts["gas_price"]) >= 2:
            high_severity = any(a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] 
                              for a in metric_alerts["gas_price"])
            if high_severity:
                recommendations.append(
                    EIPRecommendation(
                        title="Adaptive Gas Market Mechanism",
                        category=MetricCategory.ECONOMICS,
                        priority="High" if high_severity else "Medium",
                        rationale="Gas prices have shown abnormal volatility and sustained high values, "
                                 "indicating potential inefficiencies in the current gas market mechanism.",
                        metrics=["gas_price", "transaction_volume", "block_fullness"],
                        potential_impact="Reduced transaction costs during peak times, more predictable fees, "
                                        "and improved user experience.",
                        notes="Consider implementing an adaptive gas pricing formula that adjusts based on recent "
                             "block utilization trends rather than just immediate demand."
                    )
                )
        
        if "block_propagation_time" in metric_alerts:
            high_prop_time = any(a.severity in [AlertSeverity.MEDIUM, AlertSeverity.HIGH] 
                               for a in metric_alerts["block_propagation_time"])
            if high_prop_time and "uncle_rate" in metric_alerts:
                recommendations.append(
                    EIPRecommendation(
                        title="Enhanced Block Propagation Protocol",
                        category=MetricCategory.NETWORK,
                        priority="High",
                        rationale="Block propagation times are elevated, coupled with increased uncle rates, "
                                 "suggesting network inefficiencies.",
                        metrics=["block_propagation_time", "uncle_rate", "network_peers"],
                        potential_impact="Reduced uncle rates, faster block propagation, and improved network efficiency.",
                        notes="Consider implementing compact block relay or transaction bloom filtering to "
                             "reduce the amount of data that needs to be transmitted for each block."
                    )
                )
        
        if "consensus_participation" in metric_alerts:
            low_participation = any(a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] 
                                  for a in metric_alerts["consensus_participation"])
            if low_participation:
                recommendations.append(
                    EIPRecommendation(
                        title="Optimized Validator Incentives",
                        category=MetricCategory.CONSENSUS,
                        priority="Critical" if any(a.severity == AlertSeverity.CRITICAL 
                                              for a in metric_alerts["consensus_participation"]) else "High",
                        rationale="Consensus participation has dropped below acceptable thresholds, "
                                 "posing a risk to network security and liveness.",
                        metrics=["consensus_participation", "validator_count", "staking_yield"],
                        potential_impact="Improved validator participation, enhanced network security, "
                                        "and more stable consensus.",
                        notes="Review validator rewards and penalties to better incentivize participation. "
                             "Consider adjusting inactivity leak parameters or introducing rewards for consistent performance."
                    )
                )
        
        if "daily_active_addresses" in metric_alerts and "transaction_volume" in metric_alerts:
            # Look for divergence between user activity and transaction volume
            recommendations.append(
                EIPRecommendation(
                    title="Layer 1 User Experience Enhancements",
                    category=MetricCategory.USER,
                    priority="Medium",
                    rationale="Analysis shows potential friction in user experience, with changes in "
                              "active addresses not corresponding to expected transaction activity.",
                    metrics=["daily_active_addresses", "transaction_volume", "average_transaction_fee"],
                    potential_impact="Improved user retention, increased transaction volume, "
                                    "and broader protocol adoption.",
                    notes="Consider UX improvements like account abstraction, batched transactions, "
                          "or subscription-based fee models to reduce friction for regular users."
                )
            )
        
        # Custom recommendation based on overall network health
        if len(alerts) > 10 and any(a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] for a in alerts):
            recommendations.append(
                EIPRecommendation(
                    title="Protocol Health Monitoring Framework",
                    category=MetricCategory.NETWORK,
                    priority="High",
                    rationale="Multiple high-severity alerts across different protocol aspects indicate "
                              "a need for systematic health monitoring and response.",
                    metrics=["network_peers", "consensus_participation", "gas_price", "uncle_rate"],
                    potential_impact="Earlier detection of protocol issues, more coordinated responses, "
                                    "and improved protocol stability.",
                    notes="Implement a standardized health monitoring framework with automated responses "
                          "for common issues and coordinated processes for handling complex scenarios."
                )
            )
        
        return recommendations
    
    def _check_threshold(self, df: pd.DataFrame, threshold) -> List[ProtocolAlert]:
        """
        Check if metric values violate a specific threshold.
        
        Args:
            df: DataFrame containing metric values
            threshold: The threshold to check against
            
        Returns:
            List of alerts for threshold violations
        """
        alerts = []
        
        # Get the most recent value
        latest_value = df.iloc[-1]['value']
        
        # Check threshold based on type
        if threshold.threshold_type == ThresholdType.UPPER:
            if latest_value > threshold.value:
                alerts.append(self._create_alert(
                    df.index[-1], 
                    threshold.metric_type,
                    threshold.threshold_type,
                    threshold.value,
                    latest_value,
                    threshold.severity,
                    f"{threshold.metric_type} exceeded upper threshold of {threshold.value:.2f}"
                ))
                
        elif threshold.threshold_type == ThresholdType.LOWER:
            if latest_value < threshold.value:
                alerts.append(self._create_alert(
                    df.index[-1], 
                    threshold.metric_type,
                    threshold.threshold_type,
                    threshold.value,
                    latest_value,
                    threshold.severity,
                    f"{threshold.metric_type} fell below lower threshold of {threshold.value:.2f}"
                ))
                
        elif threshold.threshold_type == ThresholdType.RATE_OF_CHANGE:
            # Calculate rate of change over the last 7 days
            if len(df) >= 8:  # Need at least 8 days of data to calculate 7-day rate of change
                week_ago_value = df.iloc[-8]['value']
                rate_of_change = (latest_value - week_ago_value) / week_ago_value
                
                if abs(rate_of_change) > abs(threshold.value):
                    direction = "increase" if rate_of_change > 0 else "decrease"
                    alerts.append(self._create_alert(
                        df.index[-1], 
                        threshold.metric_type,
                        threshold.threshold_type,
                        threshold.value,
                        rate_of_change,
                        threshold.severity,
                        f"{threshold.metric_type} showed rapid {direction} of {rate_of_change:.2%}"
                    ))
        
        return alerts
    
    def _detect_anomalies(self, df: pd.DataFrame, metric_type: str) -> List[ProtocolAlert]:
        """
        Detect statistical anomalies in metric data.
        
        Args:
            df: DataFrame containing metric values
            metric_type: The type of metric being analyzed
            
        Returns:
            List of anomaly alerts
        """
        alerts = []
        
        # Need at least 14 data points for meaningful anomaly detection
        if len(df) < 14:
            return alerts
        
        # Calculate rolling statistics
        window = min(14, len(df) - 1)
        df['rolling_mean'] = df['value'].rolling(window=window).mean()
        df['rolling_std'] = df['value'].rolling(window=window).std()
        
        # Calculate z-scores
        df['z_score'] = (df['value'] - df['rolling_mean']) / df['rolling_std']
        
        # Fill NaN values
        df.fillna(0, inplace=True)
        
        # Look for significant anomalies (z-score > 3 or < -3) in the last 3 days
        for i in range(min(3, len(df))):
            idx = -1 - i  # Start from the most recent data point
            z_score = df.iloc[idx]['z_score']
            
            if abs(z_score) > 3:
                direction = "high" if z_score > 0 else "low"
                severity = AlertSeverity.MEDIUM if abs(z_score) > 4 else AlertSeverity.LOW
                
                alerts.append(self._create_alert(
                    df.index[idx], 
                    metric_type,
                    ThresholdType.STANDARD_DEVIATION,
                    3.0,
                    z_score,
                    severity,
                    f"{metric_type} is abnormally {direction} (z-score: {z_score:.2f})"
                ))
        
        return alerts
    
    def _create_alert(
        self, 
        timestamp, 
        metric_type: str, 
        threshold_type: ThresholdType,
        threshold_value: float,
        actual_value: float,
        severity: AlertSeverity,
        description: str
    ) -> ProtocolAlert:
        """Helper method to create a protocol alert"""
        return ProtocolAlert(
            metric_type=metric_type,
            threshold_type=threshold_type,
            threshold_value=threshold_value,
            actual_value=actual_value,
            timestamp=timestamp,
            severity=severity,
            description=description
        )
    
    def _severity_to_value(self, severity: AlertSeverity) -> int:
        """Convert severity enum to numeric value for sorting"""
        severity_map = {
            AlertSeverity.CRITICAL: 4,
            AlertSeverity.HIGH: 3,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 1,
            AlertSeverity.INFO: 0
        }
        return severity_map.get(severity, 0) 