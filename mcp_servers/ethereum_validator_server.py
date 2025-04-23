#!/usr/bin/env python3
"""
MCP Server for Ethereum Validation

This server provides MCP tools for validating Ethereum-related code,
simulating transactions, and checking compatibility with the Ethereum
consensus and execution layers.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import tempfile
from typing import Dict, List, Optional, Any, Union

# Import MCP server library
try:
    from modelcontextprotocol.server import (
        Server,
        ServerCapabilities,
        ToolDefinition,
        ResourceDefinition,
    )
    from modelcontextprotocol.transport import StdioTransport
except ImportError:
    print("Error: modelcontextprotocol package not found. Please install with 'pip install modelcontextprotocol'.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ethereum_validator_server")

# Temp directory for code and transaction validation
TEMP_DIR = tempfile.mkdtemp(prefix="ethereum_validator_")


class EthereumValidatorServer:
    """MCP Server for Ethereum Validation."""

    def __init__(self):
        """Initialize the Ethereum Validator Server."""
        self.server = None
        
        # Create a temporary directory for validation files if it doesn't exist
        os.makedirs(TEMP_DIR, exist_ok=True)
        logger.info(f"Using temporary directory: {TEMP_DIR}")
    
    async def validate_solidity_code(self, code: str, compiler_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate Solidity code for errors and warnings.
        
        Args:
            code: Solidity code to validate
            compiler_version: Optional Solidity compiler version
            
        Returns:
            Validation results with errors, warnings, and gas estimates
        """
        try:
            # Save code to a temporary file
            temp_file = os.path.join(TEMP_DIR, "validate_code.sol")
            with open(temp_file, "w") as f:
                f.write(code)
            
            # In a real implementation, we would use solc to compile the code
            # For this example, we'll do a basic analysis
            
            # Check for common issues
            issues = []
            
            # Check for potential reentrancy
            if "call.value" in code or "call{value:" in code:
                if "ReentrancyGuard" not in code and "nonReentrant" not in code:
                    issues.append({
                        "severity": "high",
                        "type": "security",
                        "message": "Potential reentrancy vulnerability detected. Consider using ReentrancyGuard."
                    })
            
            # Check for proper visibility
            if "function " in code:
                # Very simplified check, a real implementation would use AST analysis
                if "function " in code and not any(vis in code for vis in ["public", "private", "internal", "external"]):
                    issues.append({
                        "severity": "medium",
                        "type": "best practice",
                        "message": "Functions should have explicit visibility specified"
                    })
            
            # Check for unsafe math
            if "pragma solidity <0.8" in code:
                if "SafeMath" not in code:
                    issues.append({
                        "severity": "medium",
                        "type": "security",
                        "message": "Using Solidity <0.8.0 without SafeMath. Consider upgrading or using SafeMath."
                    })
            
            # Simulate gas estimates (in a real system, this would use proper estimation)
            functions = []
            import re
            for match in re.finditer(r"function\s+(\w+)\s*\([^)]*\)", code):
                func_name = match.group(1)
                functions.append({
                    "name": func_name,
                    "estimated_gas": 50000  # Mock value for demonstration
                })
            
            return {
                "status": "success",
                "issues": issues,
                "functions": functions,
                "compiler_version": compiler_version or "0.8.19",
                "valid": len([i for i in issues if i["severity"] == "high"]) == 0
            }
        
        except Exception as e:
            logger.error(f"Error validating Solidity code: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def simulate_transaction(
        self, 
        contract_address: str, 
        function_signature: str, 
        function_args: List[Any],
        sender_address: Optional[str] = None,
        value: Optional[int] = 0,
        network: Optional[str] = "mainnet-fork"
    ) -> Dict[str, Any]:
        """
        Simulate an Ethereum transaction and estimate its effects.
        
        Args:
            contract_address: Address of the contract to call
            function_signature: Function signature (e.g., "transfer(address,uint256)")
            function_args: Arguments to pass to the function
            sender_address: Optional sender address
            value: Optional ETH value to send (in wei)
            network: Network to simulate on (mainnet-fork, goerli, sepolia, etc.)
            
        Returns:
            Simulation results including gas used, return value, and state changes
        """
        # This is a mock implementation for demonstration
        # In a real system, this would connect to an Ethereum node or fork
        # to simulate the transaction
        
        try:
            # Normalize addresses
            contract_address = contract_address.lower()
            if sender_address:
                sender_address = sender_address.lower()
            else:
                sender_address = "0x0000000000000000000000000000000000000000"
            
            # Parse function signature to extract function name
            function_name = function_signature.split("(")[0]
            
            # Get a deterministic but realistic gas estimate based on inputs
            gas_used = 21000 + len(function_signature) * 100 + len(str(function_args)) * 50
            if value > 0:
                gas_used += 10000
            
            # Generate a mock return value
            return_value = "0x" + "0" * 64  # Default zero bytes32
            
            # Simulate state changes based on function name
            state_changes = []
            if "transfer" in function_name.lower():
                if len(function_args) >= 2:
                    recipient = function_args[0]
                    amount = function_args[1]
                    state_changes = [
                        {
                            "type": "balanceChange",
                            "address": sender_address,
                            "before": str(amount + 1000),
                            "after": "1000"
                        },
                        {
                            "type": "balanceChange",
                            "address": recipient,
                            "before": "0",
                            "after": str(amount)
                        }
                    ]
                    return_value = "0x0000000000000000000000000000000000000000000000000000000000000001"  # true
            elif "approve" in function_name.lower():
                if len(function_args) >= 2:
                    spender = function_args[0]
                    amount = function_args[1]
                    state_changes = [
                        {
                            "type": "approvalChange",
                            "owner": sender_address,
                            "spender": spender,
                            "before": "0",
                            "after": str(amount)
                        }
                    ]
                    return_value = "0x0000000000000000000000000000000000000000000000000000000000000001"  # true
            
            return {
                "status": "success",
                "transaction_data": {
                    "from": sender_address,
                    "to": contract_address,
                    "value": str(value),
                    "function": function_name,
                    "args": function_args
                },
                "simulation_result": {
                    "success": True,
                    "gas_used": gas_used,
                    "return_value": return_value,
                    "state_changes": state_changes
                },
                "network": network
            }
        
        except Exception as e:
            logger.error(f"Error simulating transaction: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def check_eip_compatibility(self, eip_number: str, target_client: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if a specific EIP is compatible with various Ethereum clients.
        
        Args:
            eip_number: EIP number to check (e.g., "1559")
            target_client: Optional specific client to check
            
        Returns:
            Compatibility matrix for different clients
        """
        # Remove "EIP-" prefix if present
        eip_number = eip_number.replace("EIP-", "").replace("eip-", "")
        
        # This is a mock implementation with hardcoded compatibility data
        # In a real system, this would query client repositories or APIs
        
        # Define some known EIP compatibility data
        compatibility_data = {
            "1559": {
                "geth": {"compatible": True, "version": "v1.10.0", "notes": "Full support"},
                "nethermind": {"compatible": True, "version": "v1.10.42", "notes": "Full support"},
                "besu": {"compatible": True, "version": "21.1.0", "notes": "Full support"},
                "erigon": {"compatible": True, "version": "2021.08.01", "notes": "Full support"},
                "consensus": {"layer": "execution", "fork": "London"}
            },
            "2930": {
                "geth": {"compatible": True, "version": "v1.9.25", "notes": "Full support"},
                "nethermind": {"compatible": True, "version": "v1.9.42", "notes": "Full support"},
                "besu": {"compatible": True, "version": "20.10.0", "notes": "Full support"},
                "erigon": {"compatible": True, "version": "2021.01.01", "notes": "Full support"},
                "consensus": {"layer": "execution", "fork": "Berlin"}
            },
            "4844": {
                "geth": {"compatible": True, "version": "v1.13.5", "notes": "Full support"},
                "nethermind": {"compatible": True, "version": "v1.20.0", "notes": "Full support"},
                "besu": {"compatible": True, "version": "23.10.0", "notes": "Full support"},
                "erigon": {"compatible": True, "version": "2.52.0", "notes": "Full support"},
                "consensus": {"layer": "both", "fork": "Dencun"}
            }
        }
        
        if eip_number in compatibility_data:
            eip_compatibility = compatibility_data[eip_number]
            
            # If a specific client is requested, filter the results
            if target_client:
                target_client = target_client.lower()
                if target_client in eip_compatibility:
                    return {
                        "status": "success",
                        "eip": f"EIP-{eip_number}",
                        "client": target_client,
                        "compatibility": eip_compatibility[target_client],
                        "consensus_info": eip_compatibility.get("consensus", {})
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Client {target_client} not found in compatibility data"
                    }
            
            return {
                "status": "success",
                "eip": f"EIP-{eip_number}",
                "compatibility": {k: v for k, v in eip_compatibility.items() if k != "consensus"},
                "consensus_info": eip_compatibility.get("consensus", {})
            }
        
        return {
            "status": "error",
            "message": f"No compatibility data found for EIP-{eip_number}"
        }
    
    async def analyze_gas_efficiency(self, code: str, optimization_level: int = 1) -> Dict[str, Any]:
        """
        Analyze Solidity code for gas efficiency and suggest optimizations.
        
        Args:
            code: Solidity code to analyze
            optimization_level: Optimization level (0-3)
            
        Returns:
            Gas analysis and optimization suggestions
        """
        try:
            # Save code to a temporary file
            temp_file = os.path.join(TEMP_DIR, "gas_analysis.sol")
            with open(temp_file, "w") as f:
                f.write(code)
            
            # In a real implementation, this would use solc with different optimization
            # levels and compare the results, or use specialized gas optimization tools
            
            # Check for common gas optimizations
            optimizations = []
            
            # Check for storage vs memory usage
            if "storage" in code and "memory" not in code:
                optimizations.append({
                    "type": "storage_to_memory",
                    "description": "Consider using memory instead of storage for function parameters and local variables",
                    "estimated_savings": "20%",
                    "priority": "high"
                })
            
            # Check for uint256 vs smaller types
            if "uint256" in code and not any(smaller in code for smaller in ["uint8", "uint16", "uint32", "uint64", "uint128"]):
                optimizations.append({
                    "type": "smaller_uints",
                    "description": "Consider using smaller uint types where appropriate",
                    "estimated_savings": "5-10%",
                    "priority": "medium"
                })
            
            # Check for costly operations in loops
            if "for" in code and any(op in code for op in ["storage", ".length", "memory new"]):
                optimizations.append({
                    "type": "loop_optimization",
                    "description": "Avoid expensive operations inside loops",
                    "estimated_savings": "15-30%",
                    "priority": "high"
                })
            
            # Estimate gas costs (mock implementation)
            baseline_gas = 500000
            optimized_gas = baseline_gas
            for opt in optimizations:
                if opt["priority"] == "high":
                    optimized_gas = int(optimized_gas * 0.8)  # 20% reduction
                elif opt["priority"] == "medium":
                    optimized_gas = int(optimized_gas * 0.9)  # 10% reduction
                else:
                    optimized_gas = int(optimized_gas * 0.95)  # 5% reduction
            
            return {
                "status": "success",
                "gas_analysis": {
                    "baseline_gas_estimate": baseline_gas,
                    "optimized_gas_estimate": optimized_gas,
                    "potential_savings": baseline_gas - optimized_gas,
                    "percentage_savings": round((baseline_gas - optimized_gas) / baseline_gas * 100, 2)
                },
                "optimizations": optimizations,
                "optimization_level_applied": optimization_level
            }
        
        except Exception as e:
            logger.error(f"Error analyzing gas efficiency: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def start_server(self) -> None:
        """Start the MCP server."""
        # Define tool definitions
        tools = [
            ToolDefinition(
                name="validate_solidity_code",
                description="Validate Solidity code for errors, security issues, and best practices",
                parameters={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Solidity code to validate"},
                        "compiler_version": {"type": "string", "description": "Optional Solidity compiler version"}
                    },
                    "required": ["code"]
                },
                handler=self.validate_solidity_code
            ),
            ToolDefinition(
                name="simulate_transaction",
                description="Simulate an Ethereum transaction and estimate its effects",
                parameters={
                    "type": "object",
                    "properties": {
                        "contract_address": {"type": "string", "description": "Address of the contract to call"},
                        "function_signature": {"type": "string", "description": "Function signature (e.g., 'transfer(address,uint256)')"},
                        "function_args": {"type": "array", "description": "Arguments to pass to the function"},
                        "sender_address": {"type": "string", "description": "Optional sender address"},
                        "value": {"type": "integer", "description": "Optional ETH value to send (in wei)"},
                        "network": {"type": "string", "description": "Network to simulate on (mainnet-fork, goerli, etc.)"}
                    },
                    "required": ["contract_address", "function_signature", "function_args"]
                },
                handler=self.simulate_transaction
            ),
            ToolDefinition(
                name="check_eip_compatibility",
                description="Check if a specific EIP is compatible with various Ethereum clients",
                parameters={
                    "type": "object",
                    "properties": {
                        "eip_number": {"type": "string", "description": "EIP number to check (e.g., '1559')"},
                        "target_client": {"type": "string", "description": "Optional specific client to check"}
                    },
                    "required": ["eip_number"]
                },
                handler=self.check_eip_compatibility
            ),
            ToolDefinition(
                name="analyze_gas_efficiency",
                description="Analyze Solidity code for gas efficiency and suggest optimizations",
                parameters={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Solidity code to analyze"},
                        "optimization_level": {"type": "integer", "description": "Optimization level (0-3)"}
                    },
                    "required": ["code"]
                },
                handler=self.analyze_gas_efficiency
            )
        ]
        
        # Create and start the server
        self.server = Server(
            capabilities=ServerCapabilities(
                tools={"listChanged": True}
            ),
            tools=tools,
            transport=StdioTransport()
        )
        
        logger.info(f"Starting Ethereum Validator Server with {len(tools)} tools")
        
        # Start the server
        await self.server.start()


async def main() -> None:
    """Run the Ethereum Validator MCP server."""
    parser = argparse.ArgumentParser(description="Ethereum Validator MCP Server")
    args = parser.parse_args()
    
    # Create and start the server
    server = EthereumValidatorServer()
    await server.start_server()


if __name__ == "__main__":
    asyncio.run(main()) 