"""
Ethereum Protocol Metrics Collector.

This module collects real-time metrics from Ethereum nodes to track
protocol performance, network health, and identify bottlenecks.
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple

import aiohttp
from web3 import Web3, AsyncWeb3
from web3.exceptions import Web3Exception

from src.config.settings import settings

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and analyzes protocol metrics from the Ethereum network.
    
    This class connects to Ethereum nodes and gathers data about gas usage,
    transaction throughput, block production, and other key metrics to help
    identify protocol bottlenecks and optimization opportunities.
    """
    
    def __init__(
        self, 
        node_url: Optional[str] = None,
        archive_node_url: Optional[str] = None,
        use_mock: bool = False,
        cache_duration: int = 300  # 5 minutes
    ):
        """
        Initialize the metrics collector.
        
        Args:
            node_url: URL of the Ethereum node to connect to
            archive_node_url: URL of an archive node for historical data
            use_mock: Whether to use mock data instead of real node connections
            cache_duration: How long to cache results in seconds
        """
        self.node_url = node_url or settings.eth_node_url
        self.archive_node_url = archive_node_url
        self.use_mock = use_mock or not self.node_url
        self.cache_duration = cache_duration
        self.cache = {}
        self.last_block = None
        
        # Create web3 instances if not using mock data
        if not self.use_mock and self.node_url:
            self.w3 = Web3(Web3.HTTPProvider(self.node_url))
            self.async_w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(self.node_url))
        else:
            self.w3 = None
            self.async_w3 = None
            logger.warning("Using mock data for protocol metrics")
        
        logger.info("Initialized MetricsCollector")
    
    async def collect_basic_metrics(self) -> Dict[str, Any]:
        """
        Collect basic node and network metrics.
        
        Returns:
            Dictionary of basic metrics
        """
        cache_key = "basic_metrics"
        if cache_key in self.cache and time.time() - self.cache[cache_key]["timestamp"] < self.cache_duration:
            return self.cache[cache_key]["data"]
        
        if self.use_mock:
            metrics = self._generate_mock_basic_metrics()
        else:
            try:
                # Collect real metrics
                metrics = {}
                
                # Get node info
                metrics["node_info"] = {
                    "is_syncing": await self.async_w3.eth.is_syncing(),
                    "chain_id": await self.async_w3.eth.chain_id,
                    "gas_price": await self.async_w3.eth.gas_price,
                    "max_priority_fee": await self.async_w3.eth.max_priority_fee,
                }
                
                # Get latest block
                latest_block_number = await self.async_w3.eth.block_number
                latest_block = await self.async_w3.eth.get_block(latest_block_number)
                self.last_block = latest_block
                
                # Extract block metrics
                metrics["latest_block"] = {
                    "number": latest_block.number,
                    "timestamp": latest_block.timestamp,
                    "gas_used": latest_block.gasUsed,
                    "gas_limit": latest_block.gasLimit,
                    "transaction_count": len(latest_block.transactions),
                    "base_fee_per_gas": latest_block.baseFeePerGas if hasattr(latest_block, "baseFeePerGas") else None
                }
                
                # Get network stats
                metrics["network"] = {
                    "peer_count": await self.async_w3.net.peer_count,
                    "is_listening": await self.async_w3.net.listening
                }
                
            except (Web3Exception, aiohttp.ClientError) as e:
                logger.error(f"Error collecting metrics: {str(e)}")
                metrics = self._generate_mock_basic_metrics()
        
        # Cache the results
        self.cache[cache_key] = {
            "timestamp": time.time(),
            "data": metrics
        }
        
        return metrics
    
    async def analyze_gas_usage(self, num_blocks: int = 100) -> Dict[str, Any]:
        """
        Analyze gas usage patterns across recent blocks.
        
        Args:
            num_blocks: Number of recent blocks to analyze
            
        Returns:
            Gas usage statistics and trends
        """
        cache_key = f"gas_usage_{num_blocks}"
        if cache_key in self.cache and time.time() - self.cache[cache_key]["timestamp"] < self.cache_duration:
            return self.cache[cache_key]["data"]
        
        if self.use_mock:
            results = self._generate_mock_gas_usage(num_blocks)
        else:
            try:
                # Get the latest block number
                latest_block_number = await self.async_w3.eth.block_number
                
                # Collect gas data from recent blocks
                gas_used_values = []
                gas_limit_values = []
                base_fee_values = []
                priority_fee_values = []
                block_times = []
                tx_counts = []
                
                prev_timestamp = None
                
                # Process blocks
                for i in range(min(num_blocks, 50)):  # Limit to 50 blocks max for performance
                    block_number = latest_block_number - i
                    block = await self.async_w3.eth.get_block(block_number)
                    
                    gas_used_values.append(block.gasUsed)
                    gas_limit_values.append(block.gasLimit)
                    
                    if hasattr(block, "baseFeePerGas"):
                        base_fee_values.append(block.baseFeePerGas)
                    
                    # Calculate block time
                    if prev_timestamp is not None:
                        block_times.append(prev_timestamp - block.timestamp)
                    prev_timestamp = block.timestamp
                    
                    # Count transactions
                    tx_counts.append(len(block.transactions))
                
                # Analyze transaction receipts for a sample of transactions
                priority_fees = []
                latest_block = await self.async_w3.eth.get_block(latest_block_number, full_transactions=True)
                
                for i, tx_hash in enumerate(latest_block.transactions[:5]):  # Sample first 5 txs
                    if hasattr(tx_hash, "maxPriorityFeePerGas"):
                        priority_fees.append(tx_hash.maxPriorityFeePerGas)
                
                # Calculate statistics
                avg_gas_used = sum(gas_used_values) / len(gas_used_values) if gas_used_values else 0
                avg_gas_limit = sum(gas_limit_values) / len(gas_limit_values) if gas_limit_values else 0
                avg_utilization = avg_gas_used / avg_gas_limit if avg_gas_limit > 0 else 0
                avg_block_time = sum(block_times) / len(block_times) if block_times else 0
                avg_tx_count = sum(tx_counts) / len(tx_counts) if tx_counts else 0
                
                results = {
                    "avg_gas_used": avg_gas_used,
                    "avg_gas_limit": avg_gas_limit,
                    "gas_utilization": avg_utilization,
                    "avg_block_time": avg_block_time,
                    "avg_transactions": avg_tx_count,
                    "gas_trend": self._calculate_trend(gas_used_values),
                    "base_fee_trend": self._calculate_trend(base_fee_values) if base_fee_values else "unknown",
                    "max_gas_used": max(gas_used_values) if gas_used_values else 0,
                    "min_gas_used": min(gas_used_values) if gas_used_values else 0,
                }
                
            except (Web3Exception, aiohttp.ClientError) as e:
                logger.error(f"Error analyzing gas usage: {str(e)}")
                results = self._generate_mock_gas_usage(num_blocks)
        
        # Cache the results
        self.cache[cache_key] = {
            "timestamp": time.time(),
            "data": results
        }
        
        return results
    
    async def analyze_transaction_types(self, num_blocks: int = 10) -> Dict[str, Any]:
        """
        Analyze transaction types in recent blocks.
        
        Args:
            num_blocks: Number of recent blocks to analyze
            
        Returns:
            Transaction type statistics
        """
        cache_key = f"tx_types_{num_blocks}"
        if cache_key in self.cache and time.time() - self.cache[cache_key]["timestamp"] < self.cache_duration:
            return self.cache[cache_key]["data"]
        
        if self.use_mock:
            results = self._generate_mock_transaction_types()
        else:
            try:
                # Get the latest block number
                latest_block_number = await self.async_w3.eth.block_number
                
                # Transaction type counters
                tx_types = {
                    "legacy": 0,
                    "eip1559": 0,
                    "eip2930": 0,
                    "contract_creation": 0,
                    "contract_interaction": 0,
                    "token_transfer": 0,
                    "simple_transfer": 0
                }
                
                # ERC-20 Transfer event signature
                transfer_signature = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                
                # Process blocks
                for i in range(min(num_blocks, 10)):  # Limit for performance
                    block_number = latest_block_number - i
                    block = await self.async_w3.eth.get_block(block_number, full_transactions=True)
                    
                    for tx in block.transactions:
                        # Check transaction type
                        if hasattr(tx, "type"):
                            if tx.type == 2:  # EIP-1559
                                tx_types["eip1559"] += 1
                            elif tx.type == 1:  # EIP-2930
                                tx_types["eip2930"] += 1
                            else:  # Legacy
                                tx_types["legacy"] += 1
                        else:
                            tx_types["legacy"] += 1
                        
                        # Check if contract creation
                        if tx.to is None:
                            tx_types["contract_creation"] += 1
                            continue
                        
                        # Get receipt to check for logs
                        try:
                            receipt = await self.async_w3.eth.get_transaction_receipt(tx.hash)
                            
                            # Check for token transfers
                            if any(log.topics and log.topics[0].hex() == transfer_signature for log in receipt.logs):
                                tx_types["token_transfer"] += 1
                            # If contract interaction
                            elif receipt.contractAddress or tx.input != "0x":
                                tx_types["contract_interaction"] += 1
                            # Must be a simple ETH transfer
                            else:
                                tx_types["simple_transfer"] += 1
                                
                        except Exception as e:
                            logger.warning(f"Error processing tx {tx.hash.hex()}: {str(e)}")
                
                total_txs = tx_types["legacy"] + tx_types["eip1559"] + tx_types["eip2930"]
                
                results = {
                    "transaction_types": tx_types,
                    "type_percentages": {
                        "legacy": tx_types["legacy"] / total_txs if total_txs else 0,
                        "eip1559": tx_types["eip1559"] / total_txs if total_txs else 0,
                        "eip2930": tx_types["eip2930"] / total_txs if total_txs else 0
                    },
                    "activity_percentages": {
                        "contract_creation": tx_types["contract_creation"] / total_txs if total_txs else 0,
                        "contract_interaction": tx_types["contract_interaction"] / total_txs if total_txs else 0,
                        "token_transfer": tx_types["token_transfer"] / total_txs if total_txs else 0,
                        "simple_transfer": tx_types["simple_transfer"] / total_txs if total_txs else 0
                    },
                    "total_transactions": total_txs
                }
                
            except (Web3Exception, aiohttp.ClientError) as e:
                logger.error(f"Error analyzing transaction types: {str(e)}")
                results = self._generate_mock_transaction_types()
        
        # Cache the results
        self.cache[cache_key] = {
            "timestamp": time.time(),
            "data": results
        }
        
        return results
    
    async def identify_bottlenecks(self) -> Dict[str, Any]:
        """
        Identify potential protocol bottlenecks based on collected metrics.
        
        Returns:
            Analysis of potential bottlenecks and suggested improvements
        """
        # Collect necessary metrics
        basic_metrics = await self.collect_basic_metrics()
        gas_usage = await self.analyze_gas_usage(100)
        tx_types = await self.analyze_transaction_types(10)
        
        # Identify potential bottlenecks
        bottlenecks = []
        
        # Gas utilization near limit
        if gas_usage["gas_utilization"] > 0.8:
            bottlenecks.append({
                "name": "High gas utilization",
                "severity": "medium",
                "description": "Blocks are consistently using >80% of available gas, indicating high demand",
                "suggested_improvements": [
                    "Consider EIP to increase gas limit per block",
                    "Optimize gas costs of commonly used operations"
                ]
            })
        
        # Priority fee volatility
        if gas_usage.get("priority_fee_volatility", 0) > 0.5:
            bottlenecks.append({
                "name": "Priority fee volatility",
                "severity": "low",
                "description": "Priority fees are fluctuating significantly, indicating potential fee market inefficiency",
                "suggested_improvements": [
                    "Research improvements to EIP-1559 fee mechanism",
                    "Consider more predictable fee estimation mechanisms"
                ]
            })
        
        # High contract interaction ratio
        contract_interaction_pct = tx_types["activity_percentages"]["contract_interaction"]
        if contract_interaction_pct > 0.7:
            bottlenecks.append({
                "name": "High smart contract usage",
                "severity": "medium",
                "description": f"{contract_interaction_pct:.1%} of transactions involve contract interactions, which are gas-intensive",
                "suggested_improvements": [
                    "Optimize EVM for common contract patterns",
                    "Consider EVM upgrades for more efficient contract execution",
                    "Research layer-2 solutions for contract-heavy applications"
                ]
            })
        
        # Add more bottleneck identification logic
        
        return {
            "bottlenecks": bottlenecks,
            "gas_metrics": gas_usage,
            "transaction_metrics": tx_types,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate a simple trend from a series of values."""
        if not values or len(values) < 2:
            return "stable"
        
        # Calculate simple linear regression slope
        n = len(values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Convert slope to trend
        if abs(slope) < 0.01 * y_mean:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def _generate_mock_basic_metrics(self) -> Dict[str, Any]:
        """Generate mock basic metrics for testing."""
        return {
            "node_info": {
                "is_syncing": False,
                "chain_id": 1,
                "gas_price": 20000000000,  # 20 gwei
                "max_priority_fee": 1500000000,  # 1.5 gwei
            },
            "latest_block": {
                "number": 17500000,
                "timestamp": int(time.time()),
                "gas_used": 12500000,
                "gas_limit": 15000000,
                "transaction_count": 120,
                "base_fee_per_gas": 15000000000  # 15 gwei
            },
            "network": {
                "peer_count": 35,
                "is_listening": True
            }
        }
    
    def _generate_mock_gas_usage(self, num_blocks: int) -> Dict[str, Any]:
        """Generate mock gas usage data for testing."""
        return {
            "avg_gas_used": 12000000,
            "avg_gas_limit": 15000000,
            "gas_utilization": 0.8,
            "avg_block_time": 12.2,
            "avg_transactions": 115,
            "gas_trend": "increasing",
            "base_fee_trend": "stable",
            "max_gas_used": 14500000,
            "min_gas_used": 8900000,
            "priority_fee_volatility": 0.4
        }
    
    def _generate_mock_transaction_types(self) -> Dict[str, Any]:
        """Generate mock transaction type data for testing."""
        return {
            "transaction_types": {
                "legacy": 50,
                "eip1559": 450,
                "eip2930": 0,
                "contract_creation": 20,
                "contract_interaction": 380,
                "token_transfer": 250,
                "simple_transfer": 100
            },
            "type_percentages": {
                "legacy": 0.1,
                "eip1559": 0.9,
                "eip2930": 0.0
            },
            "activity_percentages": {
                "contract_creation": 0.04,
                "contract_interaction": 0.76,
                "token_transfer": 0.5,
                "simple_transfer": 0.2
            },
            "total_transactions": 500
        } 