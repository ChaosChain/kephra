"""
Protocol Insights Module

This module provides functionality for analyzing Ethereum protocol data and generating insights.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

from src.models.protocol_data import (
    ProtocolMetric, 
    InsightReport, 
    EIPRecommendation,
    ProposalAnalysis,
    ProtocolAlert
)
from src.protocol_analyzer.analysis_utils import (
    calculate_growth_rate,
    detect_outliers,
    calculate_correlation,
    forecast_trend,
    identify_change_points,
    extract_seasonal_patterns,
    calculate_threshold_crossing_times
)

logger = logging.getLogger(__name__)

class ProtocolInsights:
    """
    Analyzes Ethereum protocol metrics and generates actionable insights.
    """
    
    def __init__(self, data_manager=None):
        """
        Initialize the insights engine.
        
        Args:
            data_manager: Optional data manager for retrieving protocol metrics
        """
        self.data_manager = data_manager
        self._metrics_cache = {}
        self._last_update = {}
    
    def refresh_metrics(self, metric_type: str) -> List[ProtocolMetric]:
        """
        Refresh metrics from data source.
        
        Args:
            metric_type: Type of metric to refresh
            
        Returns:
            List of refreshed metrics
        """
        if not self.data_manager:
            logger.warning("No data manager available to refresh metrics")
            return self._metrics_cache.get(metric_type, [])
        
        try:
            self._metrics_cache[metric_type] = self.data_manager.get_metrics(metric_type)
            self._last_update[metric_type] = datetime.now()
            return self._metrics_cache[metric_type]
        except Exception as e:
            logger.error(f"Error refreshing metrics for {metric_type}: {e}")
            return self._metrics_cache.get(metric_type, [])
    
    def get_metrics(self, metric_type: str, max_age_minutes: int = 60) -> List[ProtocolMetric]:
        """
        Get metrics, refreshing if needed.
        
        Args:
            metric_type: Type of metric to get
            max_age_minutes: Maximum age of cache in minutes
            
        Returns:
            List of metrics
        """
        last_update = self._last_update.get(metric_type)
        needs_refresh = (
            not last_update or 
            (datetime.now() - last_update) > timedelta(minutes=max_age_minutes)
        )
        
        if needs_refresh and self.data_manager:
            return self.refresh_metrics(metric_type)
        
        return self._metrics_cache.get(metric_type, [])
    
    def analyze_growth(self, metric_type: str, time_periods: List[int] = [30, 90, 365]) -> Dict[str, Any]:
        """
        Analyze growth rates for a metric over multiple time periods.
        
        Args:
            metric_type: Type of metric to analyze
            time_periods: List of time periods in days
            
        Returns:
            Dictionary with growth analysis
        """
        metrics = self.get_metrics(metric_type)
        
        if not metrics:
            return {"status": "error", "message": f"No data available for {metric_type}"}
        
        growth_analysis = {
            "metric_type": metric_type,
            "current_value": metrics[-1].value if metrics else None,
            "growth_rates": {},
            "forecast": {}
        }
        
        for period in time_periods:
            growth_rate = calculate_growth_rate(metrics, period)
            growth_analysis["growth_rates"][f"{period}_day"] = growth_rate
        
        # Add forecast for next 30 days
        forecast_value, forecast_confidence = forecast_trend(metrics, 30)
        growth_analysis["forecast"] = {
            "days_ahead": 30,
            "value": forecast_value,
            "confidence": forecast_confidence,
            "change_percent": ((forecast_value - metrics[-1].value) / metrics[-1].value) * 100 
            if metrics and metrics[-1].value != 0 else 0
        }
        
        # Add outlier detection
        outliers = detect_outliers(metrics)
        if outliers:
            growth_analysis["outliers"] = {
                "count": len(outliers),
                "recent_outliers": [o.to_dict() for o in outliers[-3:]]
            }
        
        return growth_analysis
    
    def generate_correlation_matrix(self, metric_types: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Generate correlation matrix between multiple metrics.
        
        Args:
            metric_types: List of metric types to correlate
            
        Returns:
            Dictionary with correlation matrix
        """
        matrix = {}
        
        for i, type_a in enumerate(metric_types):
            matrix[type_a] = {}
            metrics_a = self.get_metrics(type_a)
            
            for type_b in metric_types[i:]:
                if type_a == type_b:
                    matrix[type_a][type_b] = 1.0
                    continue
                    
                metrics_b = self.get_metrics(type_b)
                correlation = calculate_correlation(metrics_a, metrics_b)
                
                matrix[type_a][type_b] = correlation if correlation is not None else 0.0
                
                # Mirror correlation
                if type_b not in matrix:
                    matrix[type_b] = {}
                matrix[type_b][type_a] = matrix[type_a][type_b]
        
        return matrix
    
    def detect_anomalies(self, metric_types: List[str]) -> List[Dict[str, Any]]:
        """
        Detect anomalies across multiple metrics.
        
        Args:
            metric_types: List of metric types to check
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        for metric_type in metric_types:
            metrics = self.get_metrics(metric_type)
            
            if not metrics or len(metrics) < 5:
                continue
                
            # Check for outliers
            outliers = detect_outliers(metrics, n_std=3.0)
            
            # Check for change points
            change_points = identify_change_points(metrics)
            
            # Check for sudden growth
            recent_metrics = metrics[-10:] if len(metrics) >= 10 else metrics
            growth = calculate_growth_rate(recent_metrics, 
                                          time_period_days=min(7, len(recent_metrics)-1))
            
            # Record anomalies
            if outliers and outliers[-1].timestamp >= (datetime.now() - timedelta(days=7)):
                anomalies.append({
                    "metric_type": metric_type,
                    "anomaly_type": "outlier",
                    "severity": "high" if abs(outliers[-1].value - metrics[-2].value) > 3 * abs(metrics[-2].value) else "medium",
                    "timestamp": outliers[-1].timestamp.isoformat(),
                    "details": {
                        "expected_range": [metrics[-3].value * 0.8, metrics[-3].value * 1.2],
                        "actual_value": outliers[-1].value
                    }
                })
                
            if change_points and change_points[-1].timestamp >= (datetime.now() - timedelta(days=7)):
                anomalies.append({
                    "metric_type": metric_type,
                    "anomaly_type": "change_point",
                    "severity": "medium",
                    "timestamp": change_points[-1].timestamp.isoformat(),
                    "details": {
                        "previous_value": change_points[-2].value if len(change_points) > 1 else metrics[-2].value,
                        "new_value": change_points[-1].value,
                        "percent_change": ((change_points[-1].value - change_points[-2].value) / change_points[-2].value) * 100
                        if len(change_points) > 1 and change_points[-2].value != 0 else 0
                    }
                })
                
            if abs(growth) > 0.5:  # 50% growth in short period
                anomalies.append({
                    "metric_type": metric_type,
                    "anomaly_type": "rapid_growth",
                    "severity": "high" if abs(growth) > 1.0 else "medium",
                    "timestamp": metrics[-1].timestamp.isoformat(),
                    "details": {
                        "growth_rate": growth,
                        "period_days": min(7, len(recent_metrics)-1),
                        "start_value": recent_metrics[0].value,
                        "end_value": recent_metrics[-1].value
                    }
                })
                
        return anomalies
    
    def generate_eip_recommendations(self, protocol_health: Dict[str, Any]) -> List[EIPRecommendation]:
        """
        Generate EIP recommendations based on protocol health metrics.
        
        Args:
            protocol_health: Dictionary with protocol health metrics
            
        Returns:
            List of EIP recommendations
        """
        recommendations = []
        
        # Example logic for generating recommendations
        if protocol_health.get("gas_usage", {}).get("growth_rates", {}).get("30_day", 0) > 0.2:
            # Gas usage growing rapidly
            recommendations.append(EIPRecommendation(
                title="Gas Optimization Proposal",
                priority=0.8,
                rationale="Gas usage has increased by over 20% in the last 30 days",
                metrics=["gas_usage", "transaction_throughput"],
                improvement_areas=["efficiency", "cost"],
                estimated_impact=0.7
            ))
        
        if protocol_health.get("network_congestion", {}).get("current_value", 0) > 0.7:
            # Network is congested
            recommendations.append(EIPRecommendation(
                title="Throughput Enhancement Proposal",
                priority=0.9,
                rationale="Network congestion is above 70%, impacting transaction confirmation times",
                metrics=["network_congestion", "transaction_throughput", "pending_transactions"],
                improvement_areas=["scalability", "user_experience"],
                estimated_impact=0.8
            ))
        
        if protocol_health.get("validator_diversity", {}).get("current_value", 0) < 0.4:
            # Low validator diversity
            recommendations.append(EIPRecommendation(
                title="Validator Diversity Improvement",
                priority=0.7,
                rationale="Validator diversity is below optimal threshold, risking centralization",
                metrics=["validator_diversity", "staking_distribution"],
                improvement_areas=["decentralization", "security"],
                estimated_impact=0.6
            ))
        
        return recommendations
    
    def analyze_proposal(self, proposal_id: str, proposal_data: Dict[str, Any]) -> ProposalAnalysis:
        """
        Analyze an EIP proposal against current protocol metrics.
        
        Args:
            proposal_id: ID of the proposal
            proposal_data: Data about the proposal
            
        Returns:
            ProposalAnalysis object with the analysis
        """
        # Extract relevant metrics based on the proposal type
        relevant_metrics = []
        if "gas" in proposal_data.get("keywords", []):
            relevant_metrics.append("gas_usage")
        if "consensus" in proposal_data.get("keywords", []):
            relevant_metrics.extend(["validator_participation", "finality_rate"])
        if "scalability" in proposal_data.get("keywords", []):
            relevant_metrics.extend(["transaction_throughput", "block_size", "network_congestion"])
        
        # Get baseline metrics for comparison
        baseline_metrics = {}
        for metric_type in relevant_metrics:
            metrics = self.get_metrics(metric_type)
            if metrics:
                baseline_metrics[metric_type] = {
                    "current": metrics[-1].value,
                    "30d_trend": calculate_growth_rate(metrics, 30),
                    "forecast_30d": forecast_trend(metrics, 30)[0]
                }
        
        # Calculate impact scores based on proposal claims vs. metrics
        impact_scores = {}
        for area in proposal_data.get("impact_areas", []):
            if area == "gas_efficiency" and "gas_usage" in baseline_metrics:
                claimed_improvement = proposal_data.get("claimed_improvements", {}).get("gas_reduction", 0)
                current_usage = baseline_metrics["gas_usage"]["current"]
                potential_savings = current_usage * claimed_improvement
                normalized_score = min(1.0, potential_savings / (current_usage * 0.5))
                impact_scores["gas_efficiency"] = normalized_score
            
            elif area == "throughput" and "transaction_throughput" in baseline_metrics:
                claimed_improvement = proposal_data.get("claimed_improvements", {}).get("throughput_increase", 0)
                current_throughput = baseline_metrics["transaction_throughput"]["current"]
                potential_gain = current_throughput * claimed_improvement
                normalized_score = min(1.0, potential_gain / (current_throughput * 1.0))
                impact_scores["throughput"] = normalized_score
        
        # Calculate overall score (weighted average)
        weights = {
            "gas_efficiency": 0.3,
            "throughput": 0.4,
            "security": 0.5,
            "decentralization": 0.4
        }
        
        score_sum = sum(score * weights.get(area, 0.2) for area, score in impact_scores.items())
        weight_sum = sum(weights.get(area, 0.2) for area in impact_scores.keys())
        
        overall_score = score_sum / weight_sum if weight_sum > 0 else 0
        
        # Generate analysis object
        return ProposalAnalysis(
            proposal_id=proposal_id,
            timestamp=datetime.now(),
            overall_score=overall_score,
            impact_scores=impact_scores,
            relevant_metrics=baseline_metrics,
            improvement_potential={
                metric: baseline_metrics[metric]["forecast_30d"] * (1 + impact_scores.get(area, 0))
                for metric, area in [("gas_usage", "gas_efficiency"), 
                                    ("transaction_throughput", "throughput")]
                if metric in baseline_metrics and area in impact_scores
            },
            risks=[],  # Would need more context to generate meaningful risks
            synergies=[]  # Would need to compare with other active proposals
        )
    
    def generate_insight_report(self, include_metrics: List[str] = None) -> InsightReport:
        """
        Generate a comprehensive insight report on protocol health.
        
        Args:
            include_metrics: Optional list of specific metrics to include
            
        Returns:
            InsightReport object
        """
        # Default metrics if none specified
        if not include_metrics:
            include_metrics = [
                "gas_usage", "transaction_throughput", "block_size",
                "network_congestion", "validator_participation",
                "staking_distribution", "active_addresses"
            ]
        
        # Collect growth analysis for each metric
        growth_analyses = {}
        for metric_type in include_metrics:
            growth_analyses[metric_type] = self.analyze_growth(metric_type)
        
        # Generate correlation matrix
        correlations = self.generate_correlation_matrix(include_metrics)
        
        # Detect anomalies
        anomalies = self.detect_anomalies(include_metrics)
        
        # Generate recommendations
        recommendations = self.generate_eip_recommendations(growth_analyses)
        
        # Create high-level summary
        summary = []
        
        # Add growth trends to summary
        for metric, analysis in growth_analyses.items():
            if "growth_rates" in analysis and "30_day" in analysis["growth_rates"]:
                growth_30d = analysis["growth_rates"]["30_day"]
                if abs(growth_30d) > 0.1:  # 10% change is significant
                    direction = "increased" if growth_30d > 0 else "decreased"
                    summary.append(
                        f"{metric.replace('_', ' ').title()} has {direction} by "
                        f"{abs(growth_30d)*100:.1f}% over the last 30 days."
                    )
        
        # Add anomalies to summary
        if anomalies:
            for anomaly in anomalies[:3]:  # Top 3 anomalies
                metric = anomaly["metric_type"].replace('_', ' ').title()
                if anomaly["anomaly_type"] == "outlier":
                    summary.append(
                        f"Detected an outlier in {metric} on {anomaly['timestamp'].split('T')[0]}."
                    )
                elif anomaly["anomaly_type"] == "change_point":
                    summary.append(
                        f"Significant change detected in {metric} on {anomaly['timestamp'].split('T')[0]}."
                    )
                elif anomaly["anomaly_type"] == "rapid_growth":
                    summary.append(
                        f"Unusually rapid growth in {metric} ({anomaly['details']['growth_rate']*100:.1f}%)."
                    )
        
        # Add recommendations to summary
        if recommendations:
            top_recommendation = max(recommendations, key=lambda r: r.priority)
            summary.append(
                f"Top recommendation: {top_recommendation.title} "
                f"(priority: {top_recommendation.priority:.1f})."
            )
        
        # Generate the report
        return InsightReport(
            timestamp=datetime.now(),
            summary=summary,
            metrics=growth_analyses,
            correlations=correlations,
            anomalies=anomalies,
            recommendations=[r.to_dict() for r in recommendations],
            forecast={
                metric: analysis.get("forecast", {})
                for metric, analysis in growth_analyses.items()
                if "forecast" in analysis
            }
        )
    
    def detect_alerts(self, thresholds: Dict[str, Dict[str, float]]) -> List[ProtocolAlert]:
        """
        Detect alerts based on configured thresholds.
        
        Args:
            thresholds: Dictionary of metric thresholds
            
        Returns:
            List of ProtocolAlert objects
        """
        alerts = []
        
        for metric_type, threshold_config in thresholds.items():
            metrics = self.get_metrics(metric_type)
            
            if not metrics:
                continue
                
            current_value = metrics[-1].value
            
            # Check upper threshold
            if "upper" in threshold_config and current_value > threshold_config["upper"]:
                alerts.append(ProtocolAlert(
                    metric_type=metric_type,
                    timestamp=datetime.now(),
                    value=current_value,
                    threshold_value=threshold_config["upper"],
                    comparison="above",
                    severity=threshold_config.get("severity", "medium"),
                    message=f"{metric_type.replace('_', ' ').title()} exceeded upper threshold: "
                            f"{current_value:.2f} > {threshold_config['upper']:.2f}"
                ))
            
            # Check lower threshold
            if "lower" in threshold_config and current_value < threshold_config["lower"]:
                alerts.append(ProtocolAlert(
                    metric_type=metric_type,
                    timestamp=datetime.now(),
                    value=current_value,
                    threshold_value=threshold_config["lower"],
                    comparison="below",
                    severity=threshold_config.get("severity", "medium"),
                    message=f"{metric_type.replace('_', ' ').title()} fell below lower threshold: "
                            f"{current_value:.2f} < {threshold_config['lower']:.2f}"
                ))
            
            # Check rate of change if we have enough history
            if "rate_of_change" in threshold_config and len(metrics) >= 2:
                prev_value = metrics[-2].value
                if prev_value != 0:
                    rate_of_change = (current_value - prev_value) / prev_value
                    if abs(rate_of_change) > threshold_config["rate_of_change"]:
                        direction = "increased" if rate_of_change > 0 else "decreased"
                        alerts.append(ProtocolAlert(
                            metric_type=metric_type,
                            timestamp=datetime.now(),
                            value=rate_of_change,
                            threshold_value=threshold_config["rate_of_change"],
                            comparison="rate_exceeded",
                            severity=threshold_config.get("severity", "high"),
                            message=f"{metric_type.replace('_', ' ').title()} {direction} by "
                                    f"{abs(rate_of_change)*100:.1f}%, exceeding threshold of "
                                    f"{threshold_config['rate_of_change']*100:.1f}%"
                        ))
        
        return alerts 