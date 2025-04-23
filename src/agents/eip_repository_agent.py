"""
EIP Repository MCP Agent for Kephra.
Uses the EIPRepositoryServer via MCP to list available EIPs and fetch content.
"""

import asyncio
import logging
from typing import Any, Dict, List

from src.agents.base_agent import KephraAgent
from src.models.agent_models import AgentType

# import MCP client
try:
    from modelcontextprotocol.client import Client as MCPClient
    from modelcontextprotocol.transport import StdioTransport
except ImportError:
    MCPClient = None

logger = logging.getLogger(__name__)

class EIPRepositoryAgent(KephraAgent):
    """
    Agent to list available EIPs and fetch their content via MCP.
    """
    def __init__(
        self,
        name: str = "EIP Repository Agent",
        role: str = "Access EIP Repository via MCP",
        goal: str = "List and fetch EIPs from the MCP EIP repository server",
        verbose: bool = False
    ):
        super().__init__(
            name=name,
            role=role,
            goal=goal,
            agent_type=AgentType.PROPOSER,
            model=None,
            temperature=0.0,
            verbose=verbose
        )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and either list EIPs or fetch specific EIP content.
        
        Args:
            input_data: A dictionary containing command parameters
                If 'eip_id' is present, fetch that specific EIP
                Otherwise, list all EIPs
                
        Returns:
            Dict containing either a list of EIPs or a specific EIP's content
        """
        logger.info(f"Processing repository request: {input_data}")
        
        if 'eip_id' in input_data:
            # Fetch specific EIP
            eip_id = input_data['eip_id']
            logger.info(f"Fetching EIP: {eip_id}")
            try:
                result = self.fetch_eip(eip_id)
                return {"status": "success", "data": result}
            except Exception as e:
                logger.error(f"Error fetching EIP {eip_id}: {str(e)}")
                return {"status": "error", "message": str(e)}
        else:
            # List all EIPs
            try:
                eips = self.list_eips()
                return {"status": "success", "data": eips}
            except Exception as e:
                logger.error(f"Error listing EIPs: {str(e)}")
                return {"status": "error", "message": str(e)}
    
    def list_eips(self) -> List[Dict[str, Any]]:
        """Synchronous wrapper to list all EIPs."""
        return asyncio.run(self.list_eips_async())

    async def list_eips_async(self) -> List[Dict[str, Any]]:
        if MCPClient is None:
            raise RuntimeError("ModelContextProtocol package not installed")
        client = MCPClient(transport=StdioTransport())
        await client.initialize()
        resp = await client.call_tool("search_eips", {"query": ""})
        return resp.get("data", [])

    def fetch_eip(self, eip_id: str) -> Dict[str, Any]:
        """Synchronous wrapper to fetch a specific EIP's content."""
        return asyncio.run(self.fetch_eip_async(eip_id))

    async def fetch_eip_async(self, eip_id: str) -> Dict[str, Any]:
        if MCPClient is None:
            raise RuntimeError("ModelContextProtocol package not installed")
        client = MCPClient(transport=StdioTransport())
        await client.initialize()
        # get metadata
        meta = await client.call_tool("search_eips", {"query": eip_id})
        items = meta.get("data", [])
        if not items:
            raise ValueError(f"EIP not found: {eip_id}")
        # fetch full content
        content_resp = await client.call_tool("get_eip_content", {"eip_id": eip_id})
        return {"metadata": items[0], "content": content_resp.get("data")} 