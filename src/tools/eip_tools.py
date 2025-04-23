"""
Tools for working with Ethereum Improvement Proposals (EIPs).

This module provides tools for checking EIP standards compliance and other
EIP-related functionality.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from src.tools.base_tool import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Import MCP client if available
try:
    from modelcontextprotocol.client import Client as MCPClient
    from modelcontextprotocol.transport import StdioTransport
except ImportError:
    MCPClient = None


class EIPStandardsCheckerInput(BaseModel):
    """Input schema for the EIP Standards Checker tool."""
    
    eip_content: str = Field(..., description="Raw content of the EIP (typically markdown)")
    eip_id: Optional[str] = Field(None, description="EIP ID if known (e.g., 'EIP-1559')")


class EIPStandardsChecker(BaseTool):
    """
    Tool for checking EIP standards compliance.
    
    This tool analyzes EIP documents for compliance with the EIP-1 standard
    and other Ethereum governance requirements.
    """
    
    name: str = "EIP Standards Checker"
    description: str = "Checks EIP documents for compliance with standards"
    args_schema: type[BaseModel] = EIPStandardsCheckerInput
    
    def _run(self, eip_content: str, eip_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check an EIP for standards compliance.
        
        Args:
            eip_content: Raw content of the EIP
            eip_id: EIP ID if known
            
        Returns:
            Dictionary with compliance results
        """
        logger.info(f"Checking standards compliance for EIP {eip_id or 'unknown'}")
        
        try:
            # First, check locally for basic compliance
            local_results = self._check_local_compliance(eip_content, eip_id)
            
            # Then, if MCP is available, use the ethereum_validator_server for more checks
            mcp_results = {}
            if MCPClient is not None:
                try:
                    # Try to get MCP results asynchronously
                    import asyncio
                    mcp_results = asyncio.run(self._check_mcp_compliance(eip_content, eip_id))
                except Exception as e:
                    logger.warning(f"Failed to get MCP compliance results: {e}")
            
            # Combine results
            combined_results = {
                **local_results,
                "mcp_compatibility": mcp_results.get("compatibility", {}),
                "consensus_info": mcp_results.get("consensus_info", {})
            }
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Error checking EIP standards: {str(e)}")
            return {
                "error": str(e),
                "is_compliant": False,
                "issues": [{"severity": "error", "message": f"Error checking compliance: {str(e)}"}]
            }
    
    def _check_local_compliance(self, eip_content: str, eip_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check EIP compliance using local rules.
        
        Args:
            eip_content: Raw content of the EIP
            eip_id: EIP ID if known
            
        Returns:
            Dictionary with compliance results
        """
        issues = []
        
        # Check for required sections
        required_sections = ["Abstract", "Motivation", "Specification", "Rationale"]
        missing_sections = []
        
        for section in required_sections:
            pattern = rf"## {section}"
            if not re.search(pattern, eip_content, re.IGNORECASE):
                missing_sections.append(section)
                issues.append({
                    "severity": "high",
                    "message": f"Missing required section: {section}"
                })
        
        # Check for required metadata
        required_metadata = ["title", "author", "status", "type"]
        missing_metadata = []
        
        for field in required_metadata:
            pattern = rf"{field}:\s*(.+?)(?:\n|$)"
            if not re.search(pattern, eip_content, re.IGNORECASE):
                missing_metadata.append(field)
                issues.append({
                    "severity": "medium",
                    "message": f"Missing required metadata: {field}"
                })
        
        # Check for EIP number
        if not eip_id:
            eip_match = re.search(r'EIP[:\s-]*(\d+)', eip_content, re.IGNORECASE)
            if not eip_match:
                issues.append({
                    "severity": "high",
                    "message": "EIP number not found in document"
                })
        
        # Determine overall compliance
        is_compliant = len(issues) == 0
        
        return {
            "is_compliant": is_compliant,
            "issues": issues,
            "missing_sections": missing_sections,
            "missing_metadata": missing_metadata
        }
    
    async def _check_mcp_compliance(self, eip_content: str, eip_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check EIP compliance using the MCP ethereum_validator_server.
        
        Args:
            eip_content: Raw content of the EIP
            eip_id: EIP ID if known
            
        Returns:
            Dictionary with compliance results from MCP
        """
        if not MCPClient:
            return {"error": "MCP client not available"}
        
        # Extract EIP number if not provided
        if not eip_id:
            eip_match = re.search(r'EIP[:\s-]*(\d+)', eip_content, re.IGNORECASE)
            if eip_match:
                eip_id = f"EIP-{eip_match.group(1)}"
            else:
                return {"error": "Could not determine EIP number"}
        
        # Clean up EIP ID format
        eip_number = eip_id.replace("EIP-", "").replace("eip-", "")
        
        # Connect to MCP and call the validator tool
        transport = StdioTransport()
        client = MCPClient(transport=transport)
        await client.initialize()
        
        # Check EIP compatibility
        response = await client.call_tool("check_eip_compatibility", {
            "eip_number": eip_number
        })
        
        return response 