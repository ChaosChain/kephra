"""
Protocol Data Models

This module defines data models for protocol metrics, alerts, analysis results, 
and improvement recommendations.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel


class MetricCategory(str, Enum):
    """Categories of protocol metrics"""
    NETWORK = "network"
    ECONOMICS = "economics"
    CONSENSUS = "consensus"
    SECURITY = "security"
    USER = "user"
    LAYER2 = "layer2"
    OTHER = "other"


class ThresholdType(str, Enum):
    """Types of metric thresholds"""
    UPPER = "upper"
    LOWER = "lower"
    RATE_OF_CHANGE = "rate_of_change"
    STANDARD_DEVIATION = "standard_deviation"
    MOVING_AVERAGE = "moving_average"
    ANOMALY = "anomaly"  # For anomaly detection


class AlertSeverity(str, Enum):
    """Severity levels for protocol alerts"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProtocolMetric(BaseModel):
    """Model representing a single protocol metric data point"""
    metric_type: str
    value: float
    timestamp: datetime
    unit: Optional[str] = None
    source: Optional[str] = None
    category: MetricCategory = MetricCategory.OTHER
    metadata: Optional[Dict[str, Any]] = None


class MetricThreshold(BaseModel):
    """Model for metric threshold definition"""
    metric_type: str
    threshold_type: ThresholdType
    value: float
    severity: AlertSeverity = AlertSeverity.MEDIUM
    description: Optional[str] = None


class ProtocolAlert(BaseModel):
    """Model for a protocol alert triggered by threshold or anomaly detection"""
    metric_type: str
    threshold_type: ThresholdType
    threshold_value: float
    actual_value: float
    timestamp: datetime
    severity: AlertSeverity
    description: str
    related_eips: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class EIPRecommendation(BaseModel):
    """Model for protocol improvement recommendations"""
    title: str
    category: MetricCategory
    priority: str
    rationale: str
    metrics: List[str]
    potential_impact: str
    notes: Optional[str] = None
    related_eips: Optional[List[str]] = None
    
    
class MetricSnapshot(BaseModel):
    """Snapshot of key protocol metrics at a specific time"""
    timestamp: datetime
    key_metrics: Dict[str, float]  # Map of metric type to latest value
    network_health_score: float
    economic_health_score: float
    security_health_score: Optional[float] = None
    
    
class InsightReport(BaseModel):
    """Comprehensive protocol insight report"""
    metrics: List[ProtocolMetric]
    alerts: List[ProtocolAlert]
    recommendations: List[EIPRecommendation]
    timestamp: datetime
    summary: Optional[str] = None
    snapshot: Optional[MetricSnapshot] = None 