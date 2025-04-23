"""
Protocol Simulation Engine.

This module provides tools for simulating the impact of protocol changes
and evaluating their effects on performance, security, and usability.
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    Simulates protocol changes to evaluate their impact.
    
    This engine can test potential protocol changes (EIPs) against
    various metrics and scenarios to predict their effects.
    """
    
    def __init__(
        self,
        metrics_collector: Optional[MetricsCollector] = None,
        simulation_depth: str = "medium",
        max_simulation_time: int = 300  # 5 minutes
    ):
        """
        Initialize the simulation engine.
        
        Args:
            metrics_collector: An initialized metrics collector
            simulation_depth: Depth of simulations ("light", "medium", "deep")
            max_simulation_time: Maximum time to run a simulation (seconds)
        """
        self.metrics_collector = metrics_collector or MetricsCollector(use_mock=True)
        self.simulation_depth = simulation_depth
        self.max_simulation_time = max_simulation_time
        
        # Store simulation results
        self.simulation_history = {}
        
        # Parameters for different simulation depths
        self.depth_params = {
            "light": {
                "num_blocks": 10,
                "num_transactions": 100,
                "scenarios": ["normal", "congested"]
            },
            "medium": {
                "num_blocks": 50,
                "num_transactions": 500,
                "scenarios": ["normal", "congested", "attack"]
            },
            "deep": {
                "num_blocks": 200,
                "num_transactions": 2000,
                "scenarios": ["normal", "congested", "attack", "edge_cases"]
            }
        }
        
        logger.info(f"Initialized SimulationEngine with {simulation_depth} simulation depth")
    
    async def simulate_eip(self, eip_id: str, eip_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Simulate the impact of an EIP on protocol metrics.
        
        Args:
            eip_id: The EIP identifier (e.g., "EIP-1559")
            eip_details: Optional details about the EIP for simulation
            
        Returns:
            Simulation results
        """
        logger.info(f"Simulating impact of {eip_id}")
        
        # Get baseline metrics for comparison
        baseline_metrics = await self._collect_baseline_metrics()
        
        # Choose the appropriate simulation method based on EIP type
        if eip_id.startswith("EIP-"):
            eip_number = eip_id.replace("EIP-", "")
            
            # Map known EIPs to specialized simulation methods
            if eip_number == "1559":
                simulation_results = await self._simulate_eip1559(baseline_metrics)
            elif eip_number == "4844":
                simulation_results = await self._simulate_eip4844(baseline_metrics)
            else:
                # For unknown EIPs, use generic simulation with provided details
                simulation_results = await self._simulate_generic_eip(eip_id, eip_details, baseline_metrics)
        else:
            # Handle non-standard EIP identifiers
            simulation_results = await self._simulate_generic_eip(eip_id, eip_details, baseline_metrics)
        
        # Store simulation results
        self.simulation_history[eip_id] = {
            "timestamp": datetime.now().isoformat(),
            "results": simulation_results
        }
        
        return {
            "eip_id": eip_id,
            "baseline_metrics": baseline_metrics,
            "simulation_results": simulation_results,
            "simulation_timestamp": datetime.now().isoformat(),
            "simulation_depth": self.simulation_depth
        }
    
    async def simulate_custom_change(self, 
                                    name: str, 
                                    description: str, 
                                    parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a custom protocol change not associated with a specific EIP.
        
        Args:
            name: Name of the custom change
            description: Description of the change
            parameters: Parameters defining the change
            
        Returns:
            Simulation results
        """
        logger.info(f"Simulating custom change: {name}")
        
        # Get baseline metrics for comparison
        baseline_metrics = await self._collect_baseline_metrics()
        
        # Determine simulation approach based on parameters
        if "gas_limit_change" in parameters:
            simulation_results = await self._simulate_gas_limit_change(
                parameters["gas_limit_change"], 
                baseline_metrics
            )
        elif "opcode_gas_changes" in parameters:
            simulation_results = await self._simulate_opcode_gas_changes(
                parameters["opcode_gas_changes"], 
                baseline_metrics
            )
        elif "new_precompile" in parameters:
            simulation_results = await self._simulate_new_precompile(
                parameters["new_precompile"], 
                baseline_metrics
            )
        else:
            # Generic simulation for unknown parameter types
            simulation_results = await self._simulate_generic_custom_change(
                name, 
                description, 
                parameters, 
                baseline_metrics
            )
        
        # Store simulation results
        self.simulation_history[name] = {
            "timestamp": datetime.now().isoformat(),
            "results": simulation_results
        }
        
        return {
            "change_name": name,
            "description": description,
            "parameters": parameters,
            "baseline_metrics": baseline_metrics,
            "simulation_results": simulation_results,
            "simulation_timestamp": datetime.now().isoformat(),
            "simulation_depth": self.simulation_depth
        }
    
    async def compare_simulation_results(self, simulation_ids: List[str]) -> Dict[str, Any]:
        """
        Compare results from multiple simulations.
        
        Args:
            simulation_ids: List of EIP IDs or custom change names to compare
            
        Returns:
            Comparative analysis of the simulations
        """
        # Collect results for the specified simulations
        simulations = {}
        for sim_id in simulation_ids:
            if sim_id in self.simulation_history:
                simulations[sim_id] = self.simulation_history[sim_id]["results"]
            else:
                logger.warning(f"No simulation results found for {sim_id}")
        
        if not simulations:
            return {
                "status": "error",
                "message": "No valid simulation results found for comparison"
            }
        
        # Compare key metrics across simulations
        comparison = {
            "gas_efficiency": {},
            "transaction_throughput": {},
            "security_implications": {},
            "implementation_complexity": {},
            "user_experience": {}
        }
        
        # Extract and compare gas efficiency
        for sim_id, results in simulations.items():
            comparison["gas_efficiency"][sim_id] = results.get("gas_efficiency", {})
            comparison["transaction_throughput"][sim_id] = results.get("transaction_throughput", {})
            comparison["security_implications"][sim_id] = results.get("security_implications", {})
            comparison["implementation_complexity"][sim_id] = results.get("implementation_complexity", {})
            comparison["user_experience"][sim_id] = results.get("user_experience", {})
        
        # Determine relative rankings
        rankings = {}
        for category in comparison:
            if all(sim_id in comparison[category] for sim_id in simulation_ids):
                # Get metric to sort by
                if category == "gas_efficiency":
                    metric = "avg_gas_saved_percent"
                elif category == "transaction_throughput":
                    metric = "throughput_improvement_percent"
                elif category == "security_implications":
                    metric = "security_score"
                elif category == "implementation_complexity":
                    # Lower is better for complexity
                    metric = "complexity_score"
                    reverse_sort = True
                else:
                    metric = "overall_score"
                    reverse_sort = False
                
                # Check if we can sort
                if all(metric in comparison[category][sim_id] for sim_id in simulation_ids):
                    ranked = sorted(
                        simulation_ids,
                        key=lambda x: comparison[category][x].get(metric, 0),
                        reverse=not reverse_sort
                    )
                    rankings[category] = {sim_id: i+1 for i, sim_id in enumerate(ranked)}
        
        return {
            "simulations": simulation_ids,
            "comparison": comparison,
            "rankings": rankings,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    async def _collect_baseline_metrics(self) -> Dict[str, Any]:
        """Collect baseline metrics for comparison."""
        # Get metrics from the metrics collector
        basic_metrics = await self.metrics_collector.collect_basic_metrics()
        gas_usage = await self.metrics_collector.analyze_gas_usage(
            self.depth_params[self.simulation_depth]["num_blocks"]
        )
        tx_types = await self.metrics_collector.analyze_transaction_types(
            min(10, self.depth_params[self.simulation_depth]["num_blocks"])
        )
        
        return {
            "basic_metrics": basic_metrics,
            "gas_usage": gas_usage,
            "transaction_types": tx_types,
            "collection_timestamp": datetime.now().isoformat()
        }
    
    async def _simulate_eip1559(self, baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate EIP-1559 (Fee market change) effects."""
        # In a real implementation, this would use more sophisticated simulation
        # Here we use a simplified model based on known effects
        
        # Simulate gas usage effects
        baseline_gas_util = baseline_metrics["gas_usage"]["gas_utilization"]
        
        # EIP-1559 typically leads to more efficient block space usage
        simulated_gas_util = baseline_gas_util * 0.9  # 10% more efficient
        
        # Calculate effects on fee predictability
        fee_predictability_improvement = 0.7  # 70% improvement in fee predictability
        
        # Simulate effects on different transaction types
        tx_type_effects = {
            "legacy": -0.3,  # 30% reduction in legacy transactions
            "eip1559": 0.3,  # 30% increase in EIP-1559 transactions
            "eip2930": 0.0   # No change in EIP-2930 transactions
        }
        
        # Simulate security implications
        security_implications = [
            {
                "aspect": "MEV extraction",
                "impact": "moderate increase",
                "description": "May lead to increased MEV extraction opportunities through more sophisticated block building"
            },
            {
                "aspect": "Front-running",
                "impact": "slight decrease",
                "description": "More predictable fees may reduce some types of front-running"
            }
        ]
        
        # Generate comprehensive results
        return {
            "gas_efficiency": {
                "baseline_utilization": baseline_gas_util,
                "simulated_utilization": simulated_gas_util,
                "utilization_change_percent": (simulated_gas_util - baseline_gas_util) / baseline_gas_util * 100,
                "avg_gas_saved_percent": 5.0  # Estimated gas savings
            },
            "transaction_throughput": {
                "baseline_throughput": baseline_metrics["gas_usage"]["avg_transactions"],
                "simulated_throughput": baseline_metrics["gas_usage"]["avg_transactions"] * 1.05,
                "throughput_improvement_percent": 5.0
            },
            "fee_market": {
                "fee_predictability_improvement": fee_predictability_improvement,
                "fee_volatility_reduction": 0.65,  # 65% reduction in volatility
                "empty_block_reduction": 0.8  # 80% reduction in empty blocks
            },
            "transaction_type_effects": tx_type_effects,
            "security_implications": {
                "security_score": 0.75,  # Moderate security improvement
                "implications": security_implications
            },
            "implementation_complexity": {
                "complexity_score": 0.8,  # High complexity (0-1 scale)
                "client_implementation_effort": "high",
                "downstream_effects": "significant"
            },
            "user_experience": {
                "overall_score": 0.85,  # Significant UX improvement
                "fee_estimation_improvement": "high",
                "wallet_compatibility_issues": "moderate"
            }
        }
    
    async def _simulate_eip4844(self, baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate EIP-4844 (Blob transactions) effects."""
        # In a real implementation, this would use more sophisticated simulation
        
        # Simulate L2 data posting cost reduction
        l2_data_cost_reduction = 0.9  # 90% reduction in data posting costs
        
        # Impact on base chain metrics
        baseline_gas_util = baseline_metrics["gas_usage"]["gas_utilization"]
        simulated_gas_util = baseline_gas_util * 0.95  # 5% more efficient for data transactions
        
        # Simulate security implications
        security_implications = [
            {
                "aspect": "Data availability",
                "impact": "significant improvement",
                "description": "Improves data availability for L2s without permanent state bloat"
            },
            {
                "aspect": "Network overhead",
                "impact": "moderate increase",
                "description": "Larger blocks that include blobs require more network bandwidth"
            }
        ]
        
        # Generate comprehensive results
        return {
            "gas_efficiency": {
                "baseline_utilization": baseline_gas_util,
                "simulated_utilization": simulated_gas_util,
                "utilization_change_percent": (simulated_gas_util - baseline_gas_util) / baseline_gas_util * 100,
                "avg_gas_saved_percent": 2.0  # Modest L1 gas savings
            },
            "transaction_throughput": {
                "baseline_throughput": baseline_metrics["gas_usage"]["avg_transactions"],
                "simulated_throughput": baseline_metrics["gas_usage"]["avg_transactions"] * 1.02,
                "throughput_improvement_percent": 2.0
            },
            "l2_scaling": {
                "data_posting_cost_reduction": l2_data_cost_reduction,
                "l2_throughput_improvement": 8.5,  # 8.5x improvement for specific L2s
                "l2_cost_reduction": 0.9  # 90% cost reduction
            },
            "security_implications": {
                "security_score": 0.8,  # Good security improvement
                "implications": security_implications
            },
            "implementation_complexity": {
                "complexity_score": 0.9,  # Very high complexity (0-1 scale)
                "client_implementation_effort": "very high",
                "downstream_effects": "significant"
            },
            "user_experience": {
                "overall_score": 0.7,  # Moderate UX improvement
                "l2_fee_reduction": "high",
                "l1_user_impact": "low"
            }
        }
    
    async def _simulate_generic_eip(self, 
                                  eip_id: str, 
                                  eip_details: Optional[Dict[str, Any]], 
                                  baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a generic EIP's effects based on provided details."""
        # This is a placeholder for generic EIP simulation
        # In a real implementation, this would use the EIP details to perform a more accurate simulation
        
        # Default simulated metrics based on baseline
        simulated_metrics = {
            "gas_efficiency": {
                "baseline_utilization": baseline_metrics["gas_usage"]["gas_utilization"],
                "simulated_utilization": baseline_metrics["gas_usage"]["gas_utilization"],
                "utilization_change_percent": 0.0,
                "avg_gas_saved_percent": 0.0
            },
            "transaction_throughput": {
                "baseline_throughput": baseline_metrics["gas_usage"]["avg_transactions"],
                "simulated_throughput": baseline_metrics["gas_usage"]["avg_transactions"],
                "throughput_improvement_percent": 0.0
            },
            "security_implications": {
                "security_score": 0.5,  # Neutral impact
                "implications": []
            },
            "implementation_complexity": {
                "complexity_score": 0.5,  # Medium complexity
                "client_implementation_effort": "medium",
                "downstream_effects": "moderate"
            },
            "user_experience": {
                "overall_score": 0.5,  # Neutral impact
            }
        }
        
        # Adjust simulation based on EIP details if provided
        if eip_details:
            # Extract category or type
            if "category" in eip_details:
                category = eip_details["category"].lower()
                
                # Adjust based on category
                if "core" in category:
                    # Core EIPs typically affect gas efficiency and throughput
                    simulated_metrics["gas_efficiency"]["avg_gas_saved_percent"] = 3.0
                    simulated_metrics["transaction_throughput"]["throughput_improvement_percent"] = 2.0
                    simulated_metrics["implementation_complexity"]["complexity_score"] = 0.7
                elif "erc" in category:
                    # ERCs typically affect standards and interactions
                    simulated_metrics["user_experience"]["overall_score"] = 0.7
                    simulated_metrics["implementation_complexity"]["client_implementation_effort"] = "low"
            
            # Extract abstract or description
            description = eip_details.get("abstract", "") or eip_details.get("description", "")
            if description:
                # Scan for keywords to adjust simulation
                lower_desc = description.lower()
                
                if "gas" in lower_desc or "efficiency" in lower_desc:
                    simulated_metrics["gas_efficiency"]["avg_gas_saved_percent"] += 2.0
                
                if "security" in lower_desc:
                    simulated_metrics["security_implications"]["security_score"] += 0.1
                    simulated_metrics["security_implications"]["implications"].append({
                        "aspect": "General security",
                        "impact": "slight improvement",
                        "description": "EIP mentions security considerations"
                    })
                
                if "user" in lower_desc or "experience" in lower_desc:
                    simulated_metrics["user_experience"]["overall_score"] += 0.1
        
        return simulated_metrics
    
    async def _simulate_gas_limit_change(self, 
                                       gas_limit_change: float, 
                                       baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the effects of changing the gas limit."""
        # Calculate new gas limit
        baseline_gas_limit = baseline_metrics["basic_metrics"]["latest_block"]["gas_limit"]
        new_gas_limit = baseline_gas_limit * (1 + gas_limit_change)
        
        # Calculate effects on utilization
        baseline_gas_used = baseline_metrics["basic_metrics"]["latest_block"]["gas_used"]
        baseline_gas_util = baseline_metrics["gas_usage"]["gas_utilization"]
        
        new_gas_util = baseline_gas_used / new_gas_limit
        
        # Calculate effects on throughput
        baseline_throughput = baseline_metrics["gas_usage"]["avg_transactions"]
        # Assume linear relationship for simplicity
        estimated_new_throughput = baseline_throughput * (1 + gas_limit_change)
        
        # Calculate security implications
        if gas_limit_change > 0.2:
            security_score = 0.4  # Significant increase has security concerns
            security_implications = [
                {
                    "aspect": "Uncle rate",
                    "impact": "significant increase",
                    "description": "Higher gas limits may lead to more uncles due to propagation delays"
                },
                {
                    "aspect": "Centralization pressure",
                    "impact": "moderate increase",
                    "description": "Higher resource requirements may favor larger mining/validating operations"
                }
            ]
        elif gas_limit_change > 0:
            security_score = 0.6  # Modest increase has some security considerations
            security_implications = [
                {
                    "aspect": "Uncle rate",
                    "impact": "slight increase",
                    "description": "Modestly higher gas limits may slightly increase uncle rates"
                }
            ]
        else:
            security_score = 0.7  # Decreasing gas limits generally improves security
            security_implications = [
                {
                    "aspect": "Uncle rate",
                    "impact": "slight decrease",
                    "description": "Lower gas limits may decrease uncle rates"
                }
            ]
        
        return {
            "gas_efficiency": {
                "baseline_utilization": baseline_gas_util,
                "simulated_utilization": new_gas_util,
                "utilization_change_percent": (new_gas_util - baseline_gas_util) / baseline_gas_util * 100,
                "avg_gas_saved_percent": 0.0  # Gas limit changes don't save gas per operation
            },
            "transaction_throughput": {
                "baseline_throughput": baseline_throughput,
                "simulated_throughput": estimated_new_throughput,
                "throughput_improvement_percent": gas_limit_change * 100
            },
            "security_implications": {
                "security_score": security_score,
                "implications": security_implications
            },
            "implementation_complexity": {
                "complexity_score": 0.1,  # Very low complexity
                "client_implementation_effort": "very low",
                "downstream_effects": "minimal"
            },
            "user_experience": {
                "overall_score": 0.6 if gas_limit_change > 0 else 0.4,
                "fee_impact": "decrease" if gas_limit_change > 0 else "increase",
                "congestion_impact": "decrease" if gas_limit_change > 0 else "increase"
            }
        }
    
    async def _simulate_opcode_gas_changes(self, 
                                        opcode_gas_changes: Dict[str, float], 
                                        baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the effects of changing gas costs for specific opcodes."""
        # This would be a complex simulation in reality
        # Here we provide a simplified model
        
        # Calculate weighted average change
        total_change = sum(opcode_gas_changes.values())
        avg_change = total_change / len(opcode_gas_changes) if opcode_gas_changes else 0
        
        # Estimate gas efficiency impact
        # Negative changes mean gas reduction (improvement in efficiency)
        efficiency_impact = -avg_change * 0.01  # Scale factor
        
        # Estimate security impact based on which opcodes are changed
        security_score = 0.5  # Neutral by default
        security_implications = []
        
        storage_opcodes = ["SLOAD", "SSTORE"]
        compute_opcodes = ["MUL", "DIV", "EXP", "SHA3"]
        
        for opcode in opcode_gas_changes:
            if opcode in storage_opcodes and opcode_gas_changes[opcode] < 0:
                security_score -= 0.05  # Reducing storage opcode costs can be risky
                security_implications.append({
                    "aspect": f"{opcode} cost reduction",
                    "impact": "slight security risk",
                    "description": f"Reducing gas cost for {opcode} could enable state bloat attacks"
                })
            elif opcode in compute_opcodes and opcode_gas_changes[opcode] < 0:
                security_score -= 0.02  # Reducing compute opcode costs has lower risk
                security_implications.append({
                    "aspect": f"{opcode} cost reduction",
                    "impact": "minimal security risk",
                    "description": f"Reducing gas cost for {opcode} increases computation per block"
                })
        
        # Estimate implementation complexity
        complexity_score = 0.3  # Generally low complexity for gas cost changes
        if len(opcode_gas_changes) > 5:
            complexity_score += 0.1  # More opcodes means slightly higher complexity
        
        return {
            "gas_efficiency": {
                "baseline_utilization": baseline_metrics["gas_usage"]["gas_utilization"],
                "simulated_utilization": baseline_metrics["gas_usage"]["gas_utilization"] * (1 + efficiency_impact),
                "utilization_change_percent": efficiency_impact * 100,
                "avg_gas_saved_percent": -avg_change if avg_change < 0 else 0
            },
            "transaction_throughput": {
                "baseline_throughput": baseline_metrics["gas_usage"]["avg_transactions"],
                "simulated_throughput": baseline_metrics["gas_usage"]["avg_transactions"] * (1 + efficiency_impact * 0.5),
                "throughput_improvement_percent": efficiency_impact * 50  # Scale factor
            },
            "opcode_specific_effects": {
                "opcodes_modified": list(opcode_gas_changes.keys()),
                "average_change_percent": avg_change * 100
            },
            "security_implications": {
                "security_score": max(0.1, min(0.9, security_score)),  # Clamp between 0.1 and 0.9
                "implications": security_implications
            },
            "implementation_complexity": {
                "complexity_score": complexity_score,
                "client_implementation_effort": "low",
                "downstream_effects": "moderate"
            },
            "user_experience": {
                "overall_score": 0.5 + (efficiency_impact * 0.5),  # Scale by efficiency impact
                "contract_efficiency_impact": "positive" if efficiency_impact > 0 else "negative"
            }
        }
    
    async def _simulate_new_precompile(self, 
                                     precompile_details: Dict[str, Any], 
                                     baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the effects of adding a new precompile."""
        # Extract precompile details
        precompile_name = precompile_details.get("name", "Unknown precompile")
        precompile_type = precompile_details.get("type", "").lower()
        gas_cost = precompile_details.get("gas_cost", 0)
        
        # Default efficiency improvement
        efficiency_improvement = 0.1  # 10% improvement for operations using this precompile
        
        # Adjust based on precompile type
        if "crypto" in precompile_type:
            # Cryptographic precompiles typically offer major efficiency gains
            efficiency_improvement = 0.7  # 70% improvement
            security_score = 0.7  # Generally good for security
            security_implications = [
                {
                    "aspect": "Cryptographic operations",
                    "impact": "significant improvement",
                    "description": "Native implementation of cryptographic primitives is more efficient and safer"
                }
            ]
            complexity_score = 0.8  # High implementation complexity
        
        elif "storage" in precompile_type:
            # Storage optimizations
            efficiency_improvement = 0.5  # 50% improvement
            security_score = 0.5  # Neutral security impact
            security_implications = [
                {
                    "aspect": "Storage operations",
                    "impact": "neutral",
                    "description": "More efficient storage operations, but must ensure safety"
                }
            ]
            complexity_score = 0.7  # Moderate-high complexity
        
        else:
            # Generic precompile
            security_score = 0.5  # Neutral security impact
            security_implications = [
                {
                    "aspect": "General operations",
                    "impact": "slight improvement",
                    "description": "More efficient execution of common operations"
                }
            ]
            complexity_score = 0.6  # Moderate complexity
        
        return {
            "gas_efficiency": {
                "baseline_utilization": baseline_metrics["gas_usage"]["gas_utilization"],
                "simulated_utilization": baseline_metrics["gas_usage"]["gas_utilization"] * (1 - efficiency_improvement * 0.1),
                "utilization_change_percent": -efficiency_improvement * 10,
                "avg_gas_saved_percent": efficiency_improvement * 100
            },
            "transaction_throughput": {
                "baseline_throughput": baseline_metrics["gas_usage"]["avg_transactions"],
                "simulated_throughput": baseline_metrics["gas_usage"]["avg_transactions"] * (1 + efficiency_improvement * 0.05),
                "throughput_improvement_percent": efficiency_improvement * 5
            },
            "precompile_details": {
                "name": precompile_name,
                "type": precompile_type,
                "gas_cost": gas_cost,
                "efficiency_improvement": efficiency_improvement
            },
            "security_implications": {
                "security_score": security_score,
                "implications": security_implications
            },
            "implementation_complexity": {
                "complexity_score": complexity_score,
                "client_implementation_effort": "high",
                "downstream_effects": "moderate"
            },
            "user_experience": {
                "overall_score": 0.5 + (efficiency_improvement * 0.5),
                "developer_experience_improvement": "significant"
            }
        }
    
    async def _simulate_generic_custom_change(self, 
                                           name: str, 
                                           description: str, 
                                           parameters: Dict[str, Any], 
                                           baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a generic custom change without specialized handling."""
        # This is a fallback for changes that don't have specific simulation methods
        
        # Try to infer the type of change from name and description
        combined_text = (name + " " + description).lower()
        
        # Detect broad category
        is_gas_related = any(term in combined_text for term in ["gas", "fee", "cost"])
        is_throughput_related = any(term in combined_text for term in ["throughput", "tps", "transactions per second"])
        is_security_related = any(term in combined_text for term in ["security", "attack", "vulnerability"])
        is_evm_related = any(term in combined_text for term in ["evm", "virtual machine", "opcode"])
        
        # Generate a generic simulation based on detected categories
        security_score = 0.5  # Neutral by default
        gas_efficiency_pct = 0.0
        throughput_improvement_pct = 0.0
        complexity_score = 0.5  # Medium by default
        
        if is_gas_related:
            gas_efficiency_pct = 5.0
            complexity_score = 0.4
        
        if is_throughput_related:
            throughput_improvement_pct = 10.0
            complexity_score = 0.6
        
        if is_security_related:
            security_score = 0.7
            complexity_score = 0.7
        
        if is_evm_related:
            gas_efficiency_pct = 3.0
            complexity_score = 0.8
        
        # Generate simulation results
        return {
            "gas_efficiency": {
                "baseline_utilization": baseline_metrics["gas_usage"]["gas_utilization"],
                "simulated_utilization": baseline_metrics["gas_usage"]["gas_utilization"] * (1 - gas_efficiency_pct/100),
                "utilization_change_percent": -gas_efficiency_pct,
                "avg_gas_saved_percent": gas_efficiency_pct
            },
            "transaction_throughput": {
                "baseline_throughput": baseline_metrics["gas_usage"]["avg_transactions"],
                "simulated_throughput": baseline_metrics["gas_usage"]["avg_transactions"] * (1 + throughput_improvement_pct/100),
                "throughput_improvement_percent": throughput_improvement_pct
            },
            "security_implications": {
                "security_score": security_score,
                "implications": [
                    {
                        "aspect": "General security",
                        "impact": "uncertain",
                        "description": "Detailed security analysis required for this custom change"
                    }
                ]
            },
            "implementation_complexity": {
                "complexity_score": complexity_score,
                "client_implementation_effort": "medium",
                "downstream_effects": "uncertain"
            },
            "user_experience": {
                "overall_score": 0.5 + (gas_efficiency_pct / 100),
                "notes": "Generic simulation based on limited information"
            }
        } 