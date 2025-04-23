"""
Protocol Insights Module

This module analyzes Ethereum protocol data and generates actionable insights for
protocol governance, improvement proposals, and ecosystem development.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from src.common.utils import setup_logger
from src.models.protocol_data import ProtocolMetric, InsightReport
from src.protocol_analyzer.metrics_collector import MetricsCollector
from src.protocol_analyzer.trend_analyzer import TrendAnalyzer

logger = setup_logger(__name__)

class ProtocolInsights:
    """
    Analyzes Ethereum protocol data to generate actionable insights for
    governance and improvement proposals.
    """
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None,
                 trend_analyzer: Optional[TrendAnalyzer] = None):
        """
        Initialize the Protocol Insights engine.
        
        Args:
            metrics_collector: An instance of MetricsCollector for retrieving protocol metrics
            trend_analyzer: An instance of TrendAnalyzer for analyzing trends in protocol data
        """
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.trend_analyzer = trend_analyzer or TrendAnalyzer()
        self.latest_insights = None
        logger.info("ProtocolInsights module initialized")
        
    def generate_insights(self, time_period_days: int = 30) -> InsightReport:
        """
        Generate insights from Ethereum protocol data for the specified time period.
        
        Args:
            time_period_days: Number of days to analyze
            
        Returns:
            An InsightReport containing the generated insights
        """
        logger.info(f"Generating protocol insights for past {time_period_days} days")
        
        # Collect relevant metrics
        network_metrics = self.metrics_collector.get_network_metrics(time_period_days)
        gas_metrics = self.metrics_collector.get_gas_metrics(time_period_days)
        defi_metrics = self.metrics_collector.get_defi_metrics(time_period_days)
        
        # Analyze trends
        network_trends = self.trend_analyzer.analyze_network_trends(network_metrics)
        gas_trends = self.trend_analyzer.analyze_gas_trends(gas_metrics)
        defi_trends = self.trend_analyzer.analyze_defi_trends(defi_metrics)
        
        # Generate insights
        scalability_insights = self._analyze_scalability(network_metrics, gas_metrics)
        security_insights = self._analyze_security(network_metrics)
        adoption_insights = self._analyze_adoption(network_metrics, defi_metrics)
        governance_insights = self._analyze_governance(network_metrics)
        
        # Compile the report
        report = InsightReport(
            timestamp=datetime.now(),
            time_period_days=time_period_days,
            scalability_insights=scalability_insights,
            security_insights=security_insights,
            adoption_insights=adoption_insights,
            governance_insights=governance_insights,
            network_trends=network_trends,
            gas_trends=gas_trends,
            defi_trends=defi_trends
        )
        
        self.latest_insights = report
        logger.info("Protocol insights generated successfully")
        
        return report
    
    def _analyze_scalability(self, network_metrics: List[ProtocolMetric], 
                            gas_metrics: List[ProtocolMetric]) -> Dict[str, Any]:
        """
        Analyze protocol scalability based on network and gas metrics.
        
        Args:
            network_metrics: List of network-related metrics
            gas_metrics: List of gas-related metrics
            
        Returns:
            Dictionary of scalability insights
        """
        # Extract relevant metrics
        avg_block_time = self._extract_average_metric(network_metrics, 'block_time')
        avg_tx_count = self._extract_average_metric(network_metrics, 'tx_count')
        avg_gas_used = self._extract_average_metric(gas_metrics, 'gas_used')
        avg_gas_price = self._extract_average_metric(gas_metrics, 'gas_price')
        
        # Determine congestion levels
        if avg_gas_price > 100:  # gwei
            congestion_level = "High"
        elif avg_gas_price > 50:
            congestion_level = "Medium"
        else:
            congestion_level = "Low"
        
        # Calculate chain throughput and efficiency
        throughput = avg_tx_count / avg_block_time if avg_block_time > 0 else 0
        efficiency = self._calculate_throughput_efficiency(throughput, avg_gas_used)
        
        # Generate scalability insights
        return {
            "congestion_level": congestion_level,
            "throughput_tps": round(throughput, 2),
            "efficiency_score": round(efficiency, 2),
            "avg_block_time": round(avg_block_time, 2),
            "avg_gas_price": round(avg_gas_price, 2),
            "bottlenecks": self._identify_scalability_bottlenecks(network_metrics, gas_metrics),
            "improvement_areas": self._recommend_scalability_improvements(
                congestion_level, throughput, efficiency)
        }
    
    def _analyze_security(self, network_metrics: List[ProtocolMetric]) -> Dict[str, Any]:
        """
        Analyze protocol security based on network metrics.
        
        Args:
            network_metrics: List of network-related metrics
            
        Returns:
            Dictionary of security insights
        """
        # Extract relevant metrics
        avg_hashrate = self._extract_average_metric(network_metrics, 'hashrate')
        validator_count = self._extract_latest_metric(network_metrics, 'validator_count')
        active_validators_pct = self._extract_latest_metric(network_metrics, 'active_validators_pct')
        
        # Calculate security score
        decentralization_score = self._calculate_decentralization_score(network_metrics)
        
        # Generate security insights
        return {
            "security_score": round(self._calculate_security_score(
                avg_hashrate, validator_count, active_validators_pct), 2),
            "decentralization_score": round(decentralization_score, 2),
            "validator_participation": round(active_validators_pct, 2),
            "risk_factors": self._identify_security_risk_factors(network_metrics),
            "improvement_areas": self._recommend_security_improvements(
                decentralization_score, active_validators_pct)
        }
    
    def _analyze_adoption(self, network_metrics: List[ProtocolMetric],
                         defi_metrics: List[ProtocolMetric]) -> Dict[str, Any]:
        """
        Analyze protocol adoption based on network and DeFi metrics.
        
        Args:
            network_metrics: List of network-related metrics
            defi_metrics: List of DeFi-related metrics
            
        Returns:
            Dictionary of adoption insights
        """
        # Extract relevant metrics
        active_addresses = self._extract_latest_metric(network_metrics, 'active_addresses')
        new_addresses = self._extract_latest_metric(network_metrics, 'new_addresses')
        total_value_locked = self._extract_latest_metric(defi_metrics, 'total_value_locked')
        
        # Calculate growth rates
        address_growth_rate = self._calculate_growth_rate(network_metrics, 'active_addresses')
        tvl_growth_rate = self._calculate_growth_rate(defi_metrics, 'total_value_locked')
        
        # Generate adoption insights
        return {
            "active_addresses": active_addresses,
            "new_addresses": new_addresses,
            "total_value_locked_usd": total_value_locked,
            "address_growth_rate": round(address_growth_rate, 2),
            "tvl_growth_rate": round(tvl_growth_rate, 2),
            "user_segments": self._identify_user_segments(network_metrics),
            "growth_opportunities": self._identify_growth_opportunities(
                address_growth_rate, tvl_growth_rate, network_metrics, defi_metrics)
        }
    
    def _analyze_governance(self, network_metrics: List[ProtocolMetric]) -> Dict[str, Any]:
        """
        Analyze protocol governance based on network metrics.
        
        Args:
            network_metrics: List of network-related metrics
            
        Returns:
            Dictionary of governance insights
        """
        # Extract relevant metrics
        governance_participation = self._extract_latest_metric(network_metrics, 'governance_participation')
        proposal_success_rate = self._extract_latest_metric(network_metrics, 'proposal_success_rate')
        
        # Calculate governance health score
        governance_health = self._calculate_governance_health(
            governance_participation, proposal_success_rate)
        
        # Generate governance insights
        return {
            "governance_health_score": round(governance_health, 2),
            "participation_rate": round(governance_participation, 2),
            "proposal_success_rate": round(proposal_success_rate, 2),
            "improvement_areas": self._recommend_governance_improvements(
                governance_participation, proposal_success_rate),
            "recurring_issues": self._identify_recurring_governance_issues(network_metrics)
        }
    
    def get_eip_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate EIP (Ethereum Improvement Proposal) recommendations based on insights.
        
        Returns:
            List of EIP recommendations
        """
        if not self.latest_insights:
            logger.warning("No insights available. Call generate_insights() first.")
            return []
        
        recommendations = []
        
        # Check scalability issues
        if self.latest_insights.scalability_insights['congestion_level'] == "High":
            recommendations.append({
                "title": "Layer 2 Integration Standards",
                "category": "Core",
                "problem": "Network congestion and high gas prices",
                "solution": "Standardize Layer 2 integration patterns to improve scalability",
                "priority": "High",
                "impact_areas": ["Scalability", "User Experience", "Cost"]
            })
        
        # Check security concerns
        if self.latest_insights.security_insights['security_score'] < 0.7:
            recommendations.append({
                "title": "Enhanced Validator Slashing Mechanism",
                "category": "Core",
                "problem": "Security vulnerabilities in the current validation system",
                "solution": "Improve slashing mechanisms to better penalize malicious validators",
                "priority": "High",
                "impact_areas": ["Security", "Consensus", "Decentralization"]
            })
        
        # Check adoption issues
        if self.latest_insights.adoption_insights['address_growth_rate'] < 0.05:
            recommendations.append({
                "title": "Account Abstraction Implementation",
                "category": "ERC",
                "problem": "High barrier to entry for new users",
                "solution": "Implement account abstraction to improve onboarding experience",
                "priority": "Medium",
                "impact_areas": ["Adoption", "User Experience", "Developer Experience"]
            })
        
        # Check governance issues
        if self.latest_insights.governance_insights['governance_health_score'] < 0.6:
            recommendations.append({
                "title": "Distributed Governance Framework",
                "category": "Meta",
                "problem": "Low participation in governance decisions",
                "solution": "Create a more inclusive governance framework with delegated voting",
                "priority": "Medium",
                "impact_areas": ["Governance", "Decentralization", "Community"]
            })
        
        return recommendations
    
    def analyze_proposal_impact(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the potential impact of a proposed protocol change.
        
        Args:
            proposal_data: Data describing the proposal
            
        Returns:
            Dictionary containing impact analysis
        """
        if not self.latest_insights:
            logger.warning("No insights available. Call generate_insights() first.")
            return {}
        
        # Extract proposal details
        proposal_category = proposal_data.get('category', '')
        proposal_changes = proposal_data.get('changes', [])
        
        # Initialize impact scores
        impact_scores = {
            "scalability": 0,
            "security": 0,
            "adoption": 0,
            "governance": 0,
            "overall": 0
        }
        
        # Analyze impact based on proposal category
        if proposal_category.lower() in ['core', 'networking']:
            impact_scores['scalability'] = self._assess_scalability_impact(proposal_changes)
            impact_scores['security'] = self._assess_security_impact(proposal_changes)
        elif proposal_category.lower() in ['erc', 'interface']:
            impact_scores['adoption'] = self._assess_adoption_impact(proposal_changes)
        elif proposal_category.lower() in ['meta', 'informational']:
            impact_scores['governance'] = self._assess_governance_impact(proposal_changes)
        
        # Calculate overall impact
        impact_scores['overall'] = (
            impact_scores['scalability'] * 0.3 +
            impact_scores['security'] * 0.3 +
            impact_scores['adoption'] * 0.2 +
            impact_scores['governance'] * 0.2
        )
        
        # Round all scores
        for key in impact_scores:
            impact_scores[key] = round(impact_scores[key], 2)
        
        # Generate detailed analysis
        analysis = {
            "impact_scores": impact_scores,
            "tradeoffs": self._identify_proposal_tradeoffs(proposal_changes, impact_scores),
            "alignment_with_roadmap": self._assess_roadmap_alignment(proposal_category, proposal_changes),
            "implementation_complexity": self._assess_implementation_complexity(proposal_changes),
            "recommendation": self._generate_proposal_recommendation(impact_scores)
        }
        
        return analysis
    
    # Helper methods
    def _extract_average_metric(self, metrics: List[ProtocolMetric], metric_name: str) -> float:
        """Extract the average value of a specific metric from a list of metrics."""
        values = [m.value for m in metrics if m.name == metric_name]
        return sum(values) / len(values) if values else 0
    
    def _extract_latest_metric(self, metrics: List[ProtocolMetric], metric_name: str) -> float:
        """Extract the latest value of a specific metric from a list of metrics."""
        values = [m.value for m in metrics if m.name == metric_name]
        return values[-1] if values else 0
    
    def _calculate_growth_rate(self, metrics: List[ProtocolMetric], metric_name: str) -> float:
        """Calculate the growth rate of a specific metric over the time period."""
        values = [m.value for m in metrics if m.name == metric_name]
        if len(values) < 2 or values[0] == 0:
            return 0
        return (values[-1] - values[0]) / values[0]
    
    def _calculate_throughput_efficiency(self, throughput: float, avg_gas_used: float) -> float:
        """Calculate the efficiency of throughput relative to gas usage."""
        if avg_gas_used == 0:
            return 0
        # Normalize to a 0-1 scale, higher is better
        return min(1.0, throughput / (avg_gas_used / 1_000_000))
    
    def _calculate_decentralization_score(self, network_metrics: List[ProtocolMetric]) -> float:
        """Calculate a decentralization score based on network metrics."""
        validator_distribution = self._extract_latest_metric(network_metrics, 'validator_distribution')
        client_diversity = self._extract_latest_metric(network_metrics, 'client_diversity')
        
        # Higher scores indicate better decentralization (0-1 scale)
        return (validator_distribution * 0.6 + client_diversity * 0.4)
    
    def _calculate_security_score(self, hashrate: float, validator_count: float, 
                                 active_validators_pct: float) -> float:
        """Calculate a security score based on network metrics."""
        # Normalize inputs to 0-1 scale
        normalized_hashrate = min(1.0, hashrate / 1_000_000_000_000)  # Normalize to petahashes
        normalized_validator_count = min(1.0, validator_count / 500_000)  # Normalize to expected max
        normalized_active_pct = active_validators_pct / 100  # Already 0-1
        
        # Weight and combine
        return (normalized_hashrate * 0.4 + 
                normalized_validator_count * 0.3 + 
                normalized_active_pct * 0.3)
    
    def _calculate_governance_health(self, participation_rate: float, 
                                    proposal_success_rate: float) -> float:
        """Calculate a governance health score."""
        # Normalize inputs to 0-1 scale
        normalized_participation = participation_rate / 100  # Already 0-1
        normalized_success_rate = proposal_success_rate / 100  # Already 0-1
        
        # Weight and combine
        return (normalized_participation * 0.6 + normalized_success_rate * 0.4)
    
    def _identify_scalability_bottlenecks(self, network_metrics: List[ProtocolMetric],
                                         gas_metrics: List[ProtocolMetric]) -> List[str]:
        """Identify scalability bottlenecks based on metrics."""
        bottlenecks = []
        
        # Check block gas limit utilization
        avg_gas_used = self._extract_average_metric(gas_metrics, 'gas_used')
        block_gas_limit = self._extract_latest_metric(network_metrics, 'block_gas_limit')
        if avg_gas_used / block_gas_limit > 0.9:
            bottlenecks.append("High block gas utilization")
        
        # Check transaction queues
        avg_pending_tx = self._extract_average_metric(network_metrics, 'pending_tx_count')
        if avg_pending_tx > 5000:
            bottlenecks.append("Large transaction queue")
        
        # Check state growth
        state_growth_rate = self._calculate_growth_rate(network_metrics, 'state_size')
        if state_growth_rate > 0.1:  # 10% growth over period
            bottlenecks.append("Rapid state growth")
        
        return bottlenecks
    
    def _identify_security_risk_factors(self, network_metrics: List[ProtocolMetric]) -> List[str]:
        """Identify security risk factors based on metrics."""
        risk_factors = []
        
        # Check validator concentration
        validator_distribution = self._extract_latest_metric(network_metrics, 'validator_distribution')
        if validator_distribution < 0.5:  # Lower values indicate higher concentration
            risk_factors.append("High validator concentration")
        
        # Check client diversity
        client_diversity = self._extract_latest_metric(network_metrics, 'client_diversity')
        if client_diversity < 0.6:  # Lower values indicate lower diversity
            risk_factors.append("Low client diversity")
        
        # Check slashing incidents
        slashing_incidents = self._extract_latest_metric(network_metrics, 'slashing_incidents')
        if slashing_incidents > 10:
            risk_factors.append("High number of slashing incidents")
        
        return risk_factors
    
    def _identify_user_segments(self, network_metrics: List[ProtocolMetric]) -> List[Dict[str, Any]]:
        """Identify user segments based on network metrics."""
        # Example implementation - in practice would use more sophisticated analysis
        tx_value_distribution = self._extract_latest_metric(network_metrics, 'tx_value_distribution')
        
        # Simplified segmentation based on transaction values
        segments = [
            {"name": "Retail users", "percentage": 65, "avg_tx_value": 0.05},
            {"name": "DeFi users", "percentage": 25, "avg_tx_value": 0.5},
            {"name": "Institutional", "percentage": 10, "avg_tx_value": 10.0}
        ]
        
        return segments
    
    def _identify_recurring_governance_issues(self, network_metrics: List[ProtocolMetric]) -> List[str]:
        """Identify recurring governance issues based on network metrics."""
        # Example implementation
        issues = []
        
        governance_participation = self._extract_latest_metric(network_metrics, 'governance_participation')
        if governance_participation < 10:
            issues.append("Very low governance participation")
        
        proposal_success_rate = self._extract_latest_metric(network_metrics, 'proposal_success_rate')
        if proposal_success_rate < 30:
            issues.append("Low proposal success rate")
        
        return issues
    
    def _recommend_scalability_improvements(self, congestion_level: str, 
                                          throughput: float, efficiency: float) -> List[str]:
        """Recommend scalability improvements based on metrics."""
        recommendations = []
        
        if congestion_level == "High":
            recommendations.append("Implement more efficient transaction batching")
            recommendations.append("Enhance Layer 2 integration")
        
        if throughput < 15:  # transactions per second
            recommendations.append("Optimize block propagation")
        
        if efficiency < 0.5:
            recommendations.append("Implement gas cost optimizations for common operations")
        
        return recommendations
    
    def _recommend_security_improvements(self, decentralization_score: float,
                                        active_validators_pct: float) -> List[str]:
        """Recommend security improvements based on metrics."""
        recommendations = []
        
        if decentralization_score < 0.6:
            recommendations.append("Incentivize client diversity")
            recommendations.append("Promote smaller validator pools")
        
        if active_validators_pct < 80:
            recommendations.append("Improve validator activation incentives")
        
        return recommendations
    
    def _recommend_governance_improvements(self, participation_rate: float,
                                         success_rate: float) -> List[str]:
        """Recommend governance improvements based on metrics."""
        recommendations = []
        
        if participation_rate < 20:
            recommendations.append("Implement delegation mechanisms")
            recommendations.append("Create tiered governance process")
        
        if success_rate < 50:
            recommendations.append("Improve proposal quality through pre-proposal review")
            recommendations.append("Enhance proposal documentation standards")
        
        return recommendations
    
    def _identify_growth_opportunities(self, address_growth_rate: float, tvl_growth_rate: float,
                                     network_metrics: List[ProtocolMetric],
                                     defi_metrics: List[ProtocolMetric]) -> List[str]:
        """Identify growth opportunities based on metrics."""
        opportunities = []
        
        if address_growth_rate < 0.1:
            opportunities.append("Improve onboarding experience for new users")
        
        if tvl_growth_rate < 0.05:
            opportunities.append("Enhance capital efficiency in DeFi protocols")
        
        # Check for specific opportunities based on usage patterns
        dapp_usage = self._extract_latest_metric(network_metrics, 'dapp_usage')
        if dapp_usage < 0.3:  # less than 30% of txs are dapp interactions
            opportunities.append("Promote dApp development with better tooling")
        
        return opportunities
    
    def _assess_scalability_impact(self, proposal_changes: List[Dict[str, Any]]) -> float:
        """Assess the impact of a proposal on scalability."""
        impact = 0.0
        
        for change in proposal_changes:
            change_type = change.get('type', '').lower()
            description = change.get('description', '').lower()
            
            # Positive impact factors
            if 'gas' in change_type and 'reduc' in description:
                impact += 0.3
            if 'sharding' in description or 'layer 2' in description:
                impact += 0.4
            if 'state' in change_type and ('pruning' in description or 'reduction' in description):
                impact += 0.2
                
            # Negative impact factors
            if 'increase' in description and ('storage' in description or 'computation' in description):
                impact -= 0.2
                
        # Normalize to 0-1 range
        return max(0, min(1, impact))
    
    def _assess_security_impact(self, proposal_changes: List[Dict[str, Any]]) -> float:
        """Assess the impact of a proposal on security."""
        impact = 0.0
        
        for change in proposal_changes:
            change_type = change.get('type', '').lower()
            description = change.get('description', '').lower()
            
            # Positive impact factors
            if 'consensus' in change_type and ('security' in description or 'robust' in description):
                impact += 0.3
            if 'validation' in description and 'improve' in description:
                impact += 0.3
            if 'cryptography' in change_type and 'upgrade' in description:
                impact += 0.4
                
            # Negative impact factors
            if 'backward compatibility' in description and 'break' in description:
                impact -= 0.2
                
        # Normalize to 0-1 range
        return max(0, min(1, impact))
    
    def _assess_adoption_impact(self, proposal_changes: List[Dict[str, Any]]) -> float:
        """Assess the impact of a proposal on adoption."""
        impact = 0.0
        
        for change in proposal_changes:
            change_type = change.get('type', '').lower()
            description = change.get('description', '').lower()
            
            # Positive impact factors
            if 'interface' in change_type and ('usability' in description or 'ux' in description):
                impact += 0.3
            if 'standard' in change_type and 'interoperability' in description:
                impact += 0.3
            if 'cost' in description and 'lower' in description:
                impact += 0.3
                
            # Negative impact factors
            if 'complex' in description:
                impact -= 0.2
                
        # Normalize to 0-1 range
        return max(0, min(1, impact))
    
    def _assess_governance_impact(self, proposal_changes: List[Dict[str, Any]]) -> float:
        """Assess the impact of a proposal on governance."""
        impact = 0.0
        
        for change in proposal_changes:
            change_type = change.get('type', '').lower()
            description = change.get('description', '').lower()
            
            # Positive impact factors
            if 'governance' in change_type and ('participation' in description or 'voting' in description):
                impact += 0.4
            if 'transparency' in description:
                impact += 0.3
            if 'decision' in description and 'process' in description:
                impact += 0.2
                
            # Negative impact factors
            if 'centralization' in description:
                impact -= 0.3
                
        # Normalize to 0-1 range
        return max(0, min(1, impact))
    
    def _identify_proposal_tradeoffs(self, proposal_changes: List[Dict[str, Any]], 
                                   impact_scores: Dict[str, float]) -> List[Dict[str, str]]:
        """Identify tradeoffs in a proposal based on impact analysis."""
        tradeoffs = []
        
        # Check for scalability vs security tradeoff
        if impact_scores['scalability'] > 0.7 and impact_scores['security'] < 0.3:
            tradeoffs.append({
                "dimension1": "Scalability",
                "dimension2": "Security",
                "description": "Improves scalability at the potential cost of security"
            })
        
        # Check for security vs adoption tradeoff
        if impact_scores['security'] > 0.7 and impact_scores['adoption'] < 0.3:
            tradeoffs.append({
                "dimension1": "Security",
                "dimension2": "Adoption",
                "description": "Strengthens security but may impede adoption due to complexity"
            })
        
        # Check for specific tradeoffs in proposal changes
        for change in proposal_changes:
            description = change.get('description', '').lower()
            if 'tradeoff' in description or 'compromise' in description:
                parts = description.split('between')
                if len(parts) > 1:
                    factors = parts[1].split('and')
                    if len(factors) > 1:
                        tradeoffs.append({
                            "dimension1": factors[0].strip().capitalize(),
                            "dimension2": factors[1].strip().capitalize(),
                            "description": description
                        })
        
        return tradeoffs
    
    def _assess_roadmap_alignment(self, proposal_category: str, 
                                proposal_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess how well a proposal aligns with the Ethereum roadmap."""
        # Simplified roadmap focus areas
        roadmap_areas = {
            "The Merge": 0.0,
            "The Surge": 0.0,
            "The Scourge": 0.0,
            "The Verge": 0.0,
            "The Purge": 0.0,
            "The Splurge": 0.0
        }
        
        # Analyze proposal against roadmap areas
        for change in proposal_changes:
            description = change.get('description', '').lower()
            
            # The Merge (transition to PoS)
            if 'consensus' in description or 'proof of stake' in description:
                roadmap_areas["The Merge"] += 0.5
                
            # The Surge (sharding, rollups, scalability)
            if 'shard' in description or 'rollup' in description or 'scalability' in description:
                roadmap_areas["The Surge"] += 0.5
                
            # The Scourge (MEV, centralization resistance)
            if 'mev' in description or 'centralization' in description or 'censorship' in description:
                roadmap_areas["The Scourge"] += 0.5
                
            # The Verge (statelessness, state proofs)
            if 'stateless' in description or 'verkle' in description or 'witness' in description:
                roadmap_areas["The Verge"] += 0.5
                
            # The Purge (state expiry, history pruning)
            if 'expiry' in description or 'pruning' in description or 'state size' in description:
                roadmap_areas["The Purge"] += 0.5
                
            # The Splurge (misc improvements)
            if 'improvement' in description and not any(area in description for area in 
                                                      ['consensus', 'shard', 'mev', 'stateless', 'expiry']):
                roadmap_areas["The Splurge"] += 0.5
        
        # Normalize scores
        for area in roadmap_areas:
            roadmap_areas[area] = min(1.0, roadmap_areas[area])
            
        # Determine primary alignment area
        primary_area = max(roadmap_areas.items(), key=lambda x: x[1])
        
        # Calculate overall alignment score (weighted average)
        alignment_score = sum(roadmap_areas.values()) / len(roadmap_areas)
        
        return {
            "primary_alignment": primary_area[0],
            "alignment_score": round(alignment_score, 2),
            "area_scores": {k: round(v, 2) for k, v in roadmap_areas.items()}
        }
    
    def _assess_implementation_complexity(self, proposal_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the implementation complexity of a proposal."""
        complexity_score = 0.0
        risk_level = "Low"
        
        # Complexity factors
        factors = []
        
        for change in proposal_changes:
            change_type = change.get('type', '').lower()
            description = change.get('description', '').lower()
            
            # Core protocol changes are complex
            if 'core' in change_type:
                complexity_score += 0.3
                factors.append("Requires core protocol modification")
                
            # Consensus changes are very complex
            if 'consensus' in change_type or 'consensus' in description:
                complexity_score += 0.5
                factors.append("Modifies consensus mechanisms")
                
            # Backward compatibility issues increase complexity
            if 'backward' in description and 'compatibility' in description:
                complexity_score += 0.2
                factors.append("Addresses backward compatibility concerns")
                
            # Security-critical changes increase complexity
            if 'security' in description and 'critical' in description:
                complexity_score += 0.3
                factors.append("Involves security-critical components")
        
        # Normalize complexity score
        complexity_score = min(1.0, complexity_score)
        
        # Determine risk level
        if complexity_score > 0.7:
            risk_level = "High"
        elif complexity_score > 0.4:
            risk_level = "Medium"
            
        # Estimate implementation timeline
        if complexity_score > 0.7:
            timeline = "Long-term (6+ months)"
        elif complexity_score > 0.4:
            timeline = "Medium-term (3-6 months)"
        else:
            timeline = "Short-term (1-3 months)"
        
        return {
            "complexity_score": round(complexity_score, 2),
            "risk_level": risk_level,
            "timeline": timeline,
            "complexity_factors": factors
        }
    
    def _generate_proposal_recommendation(self, impact_scores: Dict[str, float]) -> Dict[str, Any]:
        """Generate a recommendation for a proposal based on impact scores."""
        overall_score = impact_scores['overall']
        
        if overall_score > 0.7:
            recommendation = "Strong support"
            reasoning = "High positive impact across multiple dimensions"
        elif overall_score > 0.5:
            recommendation = "Support with considerations"
            reasoning = "Positive impact with some trade-offs to consider"
        elif overall_score > 0.3:
            recommendation = "Needs revision"
            reasoning = "Limited positive impact or significant trade-offs"
        else:
            recommendation = "Do not support in current form"
            reasoning = "Minimal positive impact or fundamental issues"
            
        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
            "confidence": min(1.0, 0.5 + overall_score / 2)  # Scale confidence with overall score
        } 