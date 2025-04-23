"""
Protocol Metrics Analyzer

This module implements analysis of protocol metrics to identify:
1. Anomalies and threshold violations
2. Trends and patterns
3. Insights and recommendations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from src.models.protocol_data import (
    ProtocolMetric,
    ProtocolAlert,
    EIPRecommendation,
    MetricThreshold,
    AlertSeverity,
    ThresholdType,
    MetricSnapshot,
    InsightReport,
    MetricCategory
)
from src.protocol_analyzer.protocol_data_manager import ProtocolDataManager

logger = logging.getLogger(__name__)


class MetricsAnalyzer:
    """
    Analyzes protocol metrics to identify issues, trends, and opportunities.
    
    This class is responsible for:
    1. Detecting threshold violations
    2. Identifying anomalies using statistical methods
    3. Generating recommendations based on metric patterns
    4. Creating comprehensive insight reports
    """
    
    def __init__(self, data_manager: ProtocolDataManager):
        """
        Initialize metrics analyzer.
        
        Args:
            data_manager: Protocol data manager for accessing metrics
        """
        self.data_manager = data_manager
        
    def generate_insight_report(self) -> InsightReport:
        """Generate a comprehensive insight report based on protocol metrics."""
        # Get recent metrics
        recent_metrics = self.data_manager.get_recent_metrics(days=7)
        
        # Detect alerts
        alerts = self.detect_alerts(recent_metrics)
        
        # Generate recommendations based on metrics and alerts
        recommendations = self.generate_recommendations(recent_metrics, alerts)
        
        # Create a snapshot of current metrics
        snapshot = self.create_metric_snapshot(recent_metrics)
        
        # Generate a summary
        summary = self._generate_summary(recent_metrics, alerts, recommendations)
        
        return InsightReport(
            metrics=recent_metrics,
            alerts=alerts,
            recommendations=recommendations,
            timestamp=datetime.now(),
            summary=summary,
            snapshot=snapshot
        )
    
    def detect_alerts(
        self, 
        metrics: Optional[List[ProtocolMetric]] = None,
        days: int = 7
    ) -> List[ProtocolAlert]:
        """
        Detect alerts based on thresholds and anomaly detection.
        
        Args:
            metrics: Pre-fetched metrics (optional)
            days: Days of data to analyze if metrics not provided
            
        Returns:
            List of ProtocolAlert objects
        """
        alerts = []
        
        # Get metrics if not provided
        if metrics is None:
            metrics = self._collect_key_metrics(days)
            
        # Group metrics by type
        metrics_by_type = {}
        for metric in metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric)
            
        # Sort metrics within each type by timestamp
        for metric_type in metrics_by_type:
            metrics_by_type[metric_type].sort(key=lambda m: m.timestamp)
            
        # Get thresholds
        thresholds = self.data_manager.get_metric_thresholds()
        
        # Check each threshold
        for threshold in thresholds:
            if threshold.metric_type not in metrics_by_type:
                continue
                
            metric_list = metrics_by_type[threshold.metric_type]
            
            # Skip if we don't have enough data
            if not metric_list or len(metric_list) < 2:
                continue
                
            # Get latest metric value
            latest_metric = metric_list[-1]
            
            # Check threshold type
            if threshold.threshold_type == ThresholdType.UPPER:
                if latest_metric.value > threshold.value:
                    alerts.append(self._create_threshold_alert(latest_metric, threshold))
                    
            elif threshold.threshold_type == ThresholdType.LOWER:
                if latest_metric.value < threshold.value:
                    alerts.append(self._create_threshold_alert(latest_metric, threshold))
                    
            elif threshold.threshold_type == ThresholdType.RATE_OF_CHANGE:
                # Need at least 2 data points
                if len(metric_list) >= 2:
                    previous_metric = metric_list[-2]
                    if previous_metric.value != 0:
                        change_rate = (latest_metric.value - previous_metric.value) / abs(previous_metric.value)
                        if change_rate < threshold.value:  # Threshold for negative changes
                            alerts.append(self._create_rate_change_alert(
                                latest_metric, previous_metric, threshold, change_rate
                            ))
            
        # Add anomaly detection
        anomaly_alerts = self._detect_anomalies(metrics_by_type)
        alerts.extend(anomaly_alerts)
        
        return alerts
    
    def generate_recommendations(
        self,
        metrics: List[ProtocolMetric],
        alerts: List[ProtocolAlert]
    ) -> List[EIPRecommendation]:
        """
        Generate recommendations based on metrics and alerts.
        
        Args:
            metrics: Protocol metrics
            alerts: Detected alerts
            
        Returns:
            List of EIPRecommendation objects
        """
        recommendations = []
        
        # Group metrics by type
        metrics_by_type = {}
        for metric in metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric)
            
        # Group alerts by metric type
        alerts_by_type = {}
        for alert in alerts:
            if alert.metric_type not in alerts_by_type:
                alerts_by_type[alert.metric_type] = []
            alerts_by_type[alert.metric_type].append(alert)
            
        # Check gas price issues
        if "gas_price" in metrics_by_type and len(metrics_by_type["gas_price"]) > 0:
            gas_prices = [m.value for m in metrics_by_type["gas_price"]]
            avg_gas = sum(gas_prices) / len(gas_prices)
            
            if avg_gas > 80:  # Arbitrary threshold for example
                recommendations.append(
                    EIPRecommendation(
                        title="Gas Optimization Research",
                        category="ECONOMICS",
                        priority="HIGH",
                        rationale="Sustained high gas prices indicate a need for gas optimization"
                    )
                )
                
        # Check transaction count trends
        if "transaction_count" in metrics_by_type and len(metrics_by_type["transaction_count"]) > 14:
            # Get last 14 days
            tx_data = metrics_by_type["transaction_count"][-14:]
            tx_values = [m.value for m in tx_data]
            
            # Check if there's a downtrend
            slope, _, _, _, _ = stats.linregress(range(len(tx_values)), tx_values)
            
            if slope < -10:  # Arbitrary threshold for example
                recommendations.append(
                    EIPRecommendation(
                        title="Transaction Fee Mechanism Review",
                        category="ECONOMICS",
                        priority="MEDIUM",
                        rationale="Declining transaction count may indicate fee market issues"
                    )
                )
                
        # Check for missed attestations issues
        if "missed_attestations" in alerts_by_type:
            recommendations.append(
                EIPRecommendation(
                    title="Beacon Chain Participation Incentives",
                    category="CONSENSUS",
                    priority="HIGH",
                    rationale="High rate of missed attestations suggests validator incentive issues"
                )
            )
            
        # Check for uncle rate issues
        if "uncle_rate" in alerts_by_type:
            recommendations.append(
                EIPRecommendation(
                    title="Block Propagation Improvements",
                    category="NETWORK",
                    priority="MEDIUM",
                    rationale="Elevated uncle rates indicate network propagation limitations"
                )
            )
            
        # Add some generic recommendations if we don't have enough data
        if len(recommendations) < 3:
            recommendations.extend([
                EIPRecommendation(
                    title="Layer 2 Integration Standards",
                    category="LAYER2",
                    priority="MEDIUM",
                    rationale="Standardizing L2 integration points can improve cross-layer composability"
                ),
                EIPRecommendation(
                    title="Gas Market Efficiency Research",
                    category="ECONOMICS",
                    priority="LOW",
                    rationale="Research into gas market efficiency could identify optimization opportunities"
                ),
                EIPRecommendation(
                    title="User Experience Standardization",
                    category="USER",
                    priority="LOW",
                    rationale="Standardizing wallet interactions would improve overall ecosystem UX"
                ),
            ])
            
        return recommendations[:5]  # Return top 5 recommendations
    
    def _collect_key_metrics(self, days: int = 7) -> List[ProtocolMetric]:
        """Collect key metrics for analysis"""
        key_metrics = [
            "gas_price",
            "transaction_count",
            "block_time",
            "eth_price",
            "total_value_locked",
            "validator_participation",
            "missed_attestations",
            "uncle_rate",
            "reorg_count",
            "active_addresses",
            "new_addresses",
        ]
        
        metrics = []
        for metric_type in key_metrics:
            try:
                metric_data = self.data_manager.get_metric_data(
                    metric_type=metric_type,
                    days=days,
                    resolution="1d"
                )
                metrics.extend(metric_data)
            except Exception as e:
                logger.error(f"Failed to fetch {metric_type}: {e}")
                
        return metrics
    
    def _create_threshold_alert(
        self, 
        metric: ProtocolMetric, 
        threshold: MetricThreshold
    ) -> ProtocolAlert:
        """Create alert for threshold violation"""
        return ProtocolAlert(
            metric_type=metric.metric_type,
            threshold_type=threshold.threshold_type,
            threshold_value=threshold.value,
            actual_value=metric.value,
            timestamp=metric.timestamp,
            severity=threshold.severity,
            description=threshold.description
        )
    
    def _create_rate_change_alert(
        self,
        current_metric: ProtocolMetric,
        previous_metric: ProtocolMetric,
        threshold: MetricThreshold,
        change_rate: float
    ) -> ProtocolAlert:
        """Create alert for rate of change violation"""
        return ProtocolAlert(
            metric_type=current_metric.metric_type,
            threshold_type=threshold.threshold_type,
            threshold_value=threshold.value,
            actual_value=change_rate,
            timestamp=current_metric.timestamp,
            severity=threshold.severity,
            description=f"{threshold.description} (Change: {change_rate:.2%})"
        )
    
    def _detect_anomalies(
        self, 
        metrics_by_type: Dict[str, List[ProtocolMetric]]
    ) -> List[ProtocolAlert]:
        """Detect anomalies using statistical methods"""
        anomaly_alerts = []
        
        for metric_type, metrics in metrics_by_type.items():
            # Need enough data points for anomaly detection
            if len(metrics) < 10:
                continue
                
            # Extract values and timestamps
            values = np.array([m.value for m in metrics])
            timestamps = [m.timestamp for m in metrics]
            
            # Detect anomalies using Z-score
            z_scores = np.abs(stats.zscore(values))
            anomaly_indices = np.where(z_scores > 3.0)[0]  # Z-score > 3 considered anomalous
            
            for idx in anomaly_indices:
                # Only alert on recent anomalies
                if idx >= len(values) - 3:  # Last 3 data points
                    anomaly_alerts.append(
                        ProtocolAlert(
                            metric_type=metric_type,
                            threshold_type=ThresholdType.ANOMALY,
                            threshold_value=None,
                            actual_value=values[idx],
                            timestamp=timestamps[idx],
                            severity="medium",
                            description=f"Anomalous {metric_type} detected (z-score: {z_scores[idx]:.2f})"
                        )
                    )
                    
        return anomaly_alerts
    
    def create_metric_snapshot(self, metrics: List[ProtocolMetric]) -> MetricSnapshot:
        """Create a snapshot of key protocol metrics."""
        # Group metrics by type and get latest values
        latest_metrics = {}
        for metric in metrics:
            if metric.metric_type not in latest_metrics or \
               metric.timestamp > latest_metrics[metric.metric_type].timestamp:
                latest_metrics[metric.metric_type] = metric
        
        # Extract key metric values
        key_metrics = {m_type: m.value for m_type, m in latest_metrics.items()}
        
        # Calculate health scores
        network_score = self._calculate_network_health(key_metrics)
        economic_score = self._calculate_economic_health(key_metrics)
        security_score = self._calculate_security_health(key_metrics)
        
        return MetricSnapshot(
            timestamp=datetime.now(),
            key_metrics=key_metrics,
            network_health_score=network_score,
            economic_health_score=economic_score,
            security_health_score=security_score
        )
    
    def _calculate_network_health(self, metrics: Dict[str, float]) -> float:
        """Calculate network health score based on network metrics."""
        # Define weights for network metrics
        weights = {
            "active_validators": 0.3,
            "node_count": 0.2,
            "network_latency": 0.15,
            "block_time": 0.15,
            "transaction_throughput": 0.2
        }
        
        # Define baseline values for comparison
        baselines = {
            "active_validators": 400000,  # Expected number of validators
            "node_count": 5000,          # Expected number of nodes
            "network_latency": 200,      # Target latency in ms (lower is better)
            "block_time": 12,           # Target block time in seconds
            "transaction_throughput": 30  # Target TPS
        }
        
        # Calculate weighted score
        score = 0
        available_metrics = 0
        
        for metric_type, weight in weights.items():
            if metric_type in metrics:
                available_metrics += weight
                
                # Calculate individual score based on metric type
                if metric_type in ["network_latency", "block_time"]:
                    # For these metrics, lower is better
                    metric_score = min(1.0, baselines[metric_type] / max(0.1, metrics[metric_type]))
                else:
                    # For these metrics, higher is better
                    metric_score = min(1.0, metrics[metric_type] / baselines[metric_type])
                
                score += weight * metric_score
        
        # Normalize score if we have available metrics
        return score / available_metrics if available_metrics > 0 else 0.5

    def _calculate_economic_health(self, metrics: Dict[str, float]) -> float:
        """Calculate economic health score based on economic metrics."""
        # Define weights for economic metrics
        weights = {
            "eth_price": 0.2,
            "eth_staked": 0.25,
            "defi_tvl": 0.15,
            "gas_price": 0.2,
            "protocol_revenue": 0.2
        }
        
        # Define baseline values for comparison
        baselines = {
            "eth_price": 3000,      # USD
            "eth_staked": 20000000,  # ETH
            "defi_tvl": 40000000000,  # USD
            "gas_price": 40,        # Gwei (lower is better)
            "protocol_revenue": 5000000  # Daily USD
        }
        
        # Calculate weighted score
        score = 0
        available_metrics = 0
        
        for metric_type, weight in weights.items():
            if metric_type in metrics:
                available_metrics += weight
                
                # Calculate individual score based on metric type
                if metric_type == "gas_price":
                    # For gas price, lower is better
                    metric_score = min(1.0, baselines[metric_type] / max(0.1, metrics[metric_type]))
                else:
                    # For these metrics, higher is better
                    metric_score = min(1.0, metrics[metric_type] / baselines[metric_type])
                
                score += weight * metric_score
        
        # Normalize score if we have available metrics
        return score / available_metrics if available_metrics > 0 else 0.5

    def _calculate_security_health(self, metrics: Dict[str, float]) -> float:
        """Calculate security health score based on security metrics."""
        # Define weights for security metrics
        weights = {
            "slashing_events": 0.2,
            "client_diversity": 0.3,
            "validator_effectiveness": 0.3,
            "mev_extracted": 0.1,
            "censorship_resistance": 0.1
        }
        
        # Define baseline values for comparison
        baselines = {
            "slashing_events": 5,      # Weekly events (lower is better)
            "client_diversity": 0.8,    # Ideal diversity score
            "validator_effectiveness": 0.95,  # Expected effectiveness
            "mev_extracted": 1000000,   # USD (lower is better)
            "censorship_resistance": 0.9  # Ideal score
        }
        
        # Calculate weighted score
        score = 0
        available_metrics = 0
        
        for metric_type, weight in weights.items():
            if metric_type in metrics:
                available_metrics += weight
                
                # Calculate individual score based on metric type
                if metric_type in ["slashing_events", "mev_extracted"]:
                    # For these metrics, lower is better
                    metric_score = min(1.0, baselines[metric_type] / max(0.1, metrics[metric_type]))
                else:
                    # For these metrics, higher is better
                    metric_score = min(1.0, metrics[metric_type] / baselines[metric_type])
                
                score += weight * metric_score
        
        # Normalize score if we have available metrics
        return score / available_metrics if available_metrics > 0 else 0.5

    def _generate_summary(self, metrics: List[ProtocolMetric], alerts: List[ProtocolAlert], 
                         recommendations: List[EIPRecommendation]) -> str:
        """Generate a summary of the protocol state based on metrics, alerts, and recommendations."""
        # Group metrics by type and get latest values
        latest_metrics = {}
        for metric in metrics:
            if metric.metric_type not in latest_metrics or \
               metric.timestamp > latest_metrics[metric.metric_type].timestamp:
                latest_metrics[metric.metric_type] = metric
        
        # Extract values for key metrics
        metric_values = {m_type: m.value for m_type, m in latest_metrics.items()}
        
        # Calculate overall health scores
        network_health = self._calculate_network_health(metric_values)
        economic_health = self._calculate_economic_health(metric_values)
        security_health = self._calculate_security_health(metric_values)
        
        # Calculate overall protocol health
        overall_health = (network_health * 0.35) + (economic_health * 0.35) + (security_health * 0.3)
        
        # Count critical alerts
        critical_alerts = sum(1 for alert in alerts if alert.severity == "critical")
        
        # Generate summary text
        status = "healthy" if overall_health > 0.7 else "concerning" if overall_health > 0.4 else "critical"
        
        summary = f"Ethereum Protocol Health: {status.upper()} ({overall_health:.2f})\n\n"
        summary += f"Network Health: {network_health:.2f} | Economic Health: {economic_health:.2f} | "
        summary += f"Security Health: {security_health:.2f}\n\n"
        
        if critical_alerts > 0:
            summary += f"ATTENTION: {critical_alerts} critical alerts detected that require immediate action.\n\n"
        
        if recommendations:
            top_recommendations = sorted(recommendations, key=lambda r: r.priority, reverse=True)[:3]
            summary += f"Top {len(top_recommendations)} recommendations:\n"
            for i, rec in enumerate(top_recommendations, 1):
                summary += f"{i}. {rec.title} (Priority: {rec.priority})\n"
        
        return summary 