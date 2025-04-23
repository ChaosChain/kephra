"""
Protocol Analyzer for Kephra.

This package implements tools for analyzing blockchain protocol metrics,
identifying bottlenecks, and simulating proposed improvements. It connects
to live blockchain data and provides insights for agent decision-making.
"""

from .metrics_collector import MetricsCollector
from .trend_analyzer import TrendAnalyzer
from .simulation_engine import SimulationEngine
from .protocol_insights import ProtocolInsights

__all__ = [
    "MetricsCollector",
    "TrendAnalyzer",
    "SimulationEngine",
    "ProtocolInsights",
] 