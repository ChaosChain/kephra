#!/usr/bin/env python3
"""
MCP Server for Ethereum Improvement Proposals (EIPs)

This server provides MCP tools and resources for accessing and querying
Ethereum Improvement Proposals. It allows agents to search for EIPs,
retrieve specific proposals, and access related resources.
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
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
logger = logging.getLogger("eip_repository_server")

# Directory structure
DEFAULT_EIPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eips")
EIPS_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eips_cache.json")


class EIPRepositoryServer:
    """MCP Server for Ethereum Improvement Proposals."""

    def __init__(self, eips_dir: str = DEFAULT_EIPS_DIR):
        """
        Initialize the EIP Repository Server.
        
        Args:
            eips_dir: Directory containing EIP files
        """
        self.eips_dir = eips_dir
        self.eips_cache = {}
        self.server = None
        
        # Ensure the EIPs directory exists
        os.makedirs(self.eips_dir, exist_ok=True)
        
        # Load or create EIPs cache
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load the EIPs cache from disk or create a new one."""
        if os.path.exists(EIPS_CACHE_FILE):
            try:
                with open(EIPS_CACHE_FILE, "r") as f:
                    self.eips_cache = json.load(f)
                logger.info(f"Loaded {len(self.eips_cache)} EIPs from cache")
            except Exception as e:
                logger.error(f"Error loading EIPs cache: {e}")
                self.eips_cache = {}
        
        # If cache is empty, scan the directory
        if not self.eips_cache:
            self._scan_eips_directory()
    
    def _save_cache(self) -> None:
        """Save the EIPs cache to disk."""
        try:
            with open(EIPS_CACHE_FILE, "w") as f:
                json.dump(self.eips_cache, f, indent=2)
            logger.info(f"Saved {len(self.eips_cache)} EIPs to cache")
        except Exception as e:
            logger.error(f"Error saving EIPs cache: {e}")
    
    def _scan_eips_directory(self) -> None:
        """Scan the EIPs directory and update the cache."""
        eip_files = []
        for root, _, files in os.walk(self.eips_dir):
            for file in files:
                if file.endswith(".md") and file.lower().startswith("eip-"):
                    eip_files.append(os.path.join(root, file))
        
        logger.info(f"Found {len(eip_files)} EIP files")
        
        # Parse each EIP file and update the cache
        for file_path in eip_files:
            self._parse_eip_file(file_path)
        
        # Save the updated cache
        self._save_cache()
    
    def _parse_eip_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse an EIP file and extract its metadata.
        
        Args:
            file_path: Path to the EIP file
            
        Returns:
            EIP metadata or None if parsing failed
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract EIP number from filename
            filename = os.path.basename(file_path)
            eip_match = re.search(r"eip-(\d+)", filename, re.IGNORECASE)
            if not eip_match:
                eip_match = re.search(r"eip[:\s-]*(\d+)", content, re.IGNORECASE)
            
            if not eip_match:
                logger.warning(f"Could not determine EIP number for file: {file_path}")
                return None
            
            eip_number = eip_match.group(1)
            eip_id = f"EIP-{eip_number}"
            
            # Extract metadata using regex
            title_match = re.search(r"title:\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            author_match = re.search(r"author:\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            status_match = re.search(r"status:\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            type_match = re.search(r"type:\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            created_match = re.search(r"created:\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            
            # Extract abstract/summary
            abstract_match = re.search(r"## Abstract\s+(.+?)(?=##|\Z)", content, re.DOTALL | re.IGNORECASE)
            if not abstract_match:
                abstract_match = re.search(r"## Simple Summary\s+(.+?)(?=##|\Z)", content, re.DOTALL | re.IGNORECASE)
            
            # Create EIP metadata
            eip_data = {
                "id": eip_id,
                "number": int(eip_number),
                "title": title_match.group(1).strip() if title_match else "Unknown",
                "author": author_match.group(1).strip() if author_match else "Unknown",
                "status": status_match.group(1).strip() if status_match else "Unknown",
                "type": type_match.group(1).strip() if type_match else "Unknown",
                "created": created_match.group(1).strip() if created_match else "",
                "description": abstract_match.group(1).strip() if abstract_match else "",
                "file_path": file_path,
                "content_hash": hash(content),  # Simple content hash for change detection
            }
            
            # Update the cache
            self.eips_cache[eip_id] = eip_data
            
            return eip_data
        
        except Exception as e:
            logger.error(f"Error parsing EIP file {file_path}: {e}")
            return None
    
    async def search_eips(self, query: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for EIPs matching the query.
        
        Args:
            query: Search query (can match title, description, or ID)
            status: Optional status filter
            
        Returns:
            List of matching EIPs metadata
        """
        results = []
        
        # Ensure we have the latest EIPs data
        if not self.eips_cache:
            self._scan_eips_directory()
        
        # If query is numeric, try to match EIP number directly
        if query.isdigit():
            eip_id = f"EIP-{query}"
            if eip_id in self.eips_cache:
                eip_data = self.eips_cache[eip_id]
                if not status or eip_data.get("status", "").lower() == status.lower():
                    results.append(eip_data)
        
        # Search by text matching
        query = query.lower()
        for eip_id, eip_data in self.eips_cache.items():
            # Skip if already matched by ID
            if results and results[0]["id"] == eip_id:
                continue
            
            # Filter by status if provided
            if status and eip_data.get("status", "").lower() != status.lower():
                continue
            
            # Match against title, description, or ID
            if (query in eip_id.lower() or
                query in eip_data.get("title", "").lower() or
                query in eip_data.get("description", "").lower()):
                results.append(eip_data)
        
        # Sort results by relevance (exact ID matches first, then title matches)
        results.sort(key=lambda eip: (
            0 if query in eip["id"].lower() else 
            1 if query in eip.get("title", "").lower() else 
            2
        ))
        
        return results
    
    async def get_eip_content(self, eip_id: str) -> Optional[str]:
        """
        Get the full content of an EIP.
        
        Args:
            eip_id: ID of the EIP to retrieve (e.g., 'EIP-1559')
            
        Returns:
            Full content of the EIP or None if not found
        """
        # Normalize EIP ID
        eip_id = eip_id.upper() if eip_id.startswith("EIP-") else f"EIP-{eip_id}"
        
        # Check if EIP exists in cache
        if eip_id not in self.eips_cache:
            logger.warning(f"EIP not found in cache: {eip_id}")
            return None
        
        # Get file path from cache
        file_path = self.eips_cache[eip_id].get("file_path")
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"EIP file not found: {file_path}")
            return None
        
        # Read and return the content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading EIP file {file_path}: {e}")
            return None
    
    async def download_eip(self, eip_id: str, url: Optional[str] = None) -> bool:
        """
        Download an EIP from Ethereum's GitHub repository or a specified URL.
        
        Args:
            eip_id: ID of the EIP to download (e.g., '1559')
            url: Optional URL to download from
            
        Returns:
            Success status
        """
        import requests
        
        # Normalize EIP ID
        eip_id = eip_id.replace("EIP-", "").replace("eip-", "")
        
        # Construct URL if not provided
        if not url:
            url = f"https://raw.githubusercontent.com/ethereum/EIPs/master/EIPS/eip-{eip_id}.md"
        
        try:
            # Download the EIP
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Save the file
            file_path = os.path.join(self.eips_dir, f"eip-{eip_id}.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # Parse and cache the EIP
            self._parse_eip_file(file_path)
            self._save_cache()
            
            logger.info(f"Successfully downloaded EIP-{eip_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error downloading EIP-{eip_id}: {e}")
            return False
    
    async def start_server(self) -> None:
        """Start the MCP server."""
        # Define tool definitions
        tools = [
            ToolDefinition(
                name="search_eips",
                description="Search for Ethereum Improvement Proposals (EIPs) by keyword, title, or ID",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query (keyword, title, or EIP number)"},
                        "status": {"type": "string", "description": "Filter by EIP status (e.g., Draft, Final, Active)"}
                    },
                    "required": ["query"]
                },
                handler=self.search_eips
            ),
            ToolDefinition(
                name="get_eip_content",
                description="Get the full content of a specific EIP by ID",
                parameters={
                    "type": "object",
                    "properties": {
                        "eip_id": {"type": "string", "description": "EIP ID (e.g., 'EIP-1559' or '1559')"}
                    },
                    "required": ["eip_id"]
                },
                handler=self.get_eip_content
            ),
            ToolDefinition(
                name="download_eip",
                description="Download an EIP from Ethereum's GitHub repository or a specified URL",
                parameters={
                    "type": "object",
                    "properties": {
                        "eip_id": {"type": "string", "description": "EIP ID (e.g., '1559')"},
                        "url": {"type": "string", "description": "Optional URL to download from"}
                    },
                    "required": ["eip_id"]
                },
                handler=self.download_eip
            )
        ]
        
        # Define resource definitions (we'll create resources for each EIP)
        resources = {}
        for eip_id, eip_data in self.eips_cache.items():
            resource_id = f"eip:{eip_data['number']}"
            resources[resource_id] = ResourceDefinition(
                uri=resource_id,
                name=f"{eip_id}: {eip_data.get('title', 'Unknown')}",
                type="text/markdown",
                handler=lambda eip_id=eip_id: self.get_eip_content(eip_id)
            )
        
        # Create and start the server
        self.server = Server(
            capabilities=ServerCapabilities(
                tools={"listChanged": True},
                resources={"subscribe": True, "listChanged": True}
            ),
            tools=tools,
            resources=resources,
            transport=StdioTransport()
        )
        
        logger.info(f"Starting EIP Repository Server with {len(tools)} tools and {len(resources)} resources")
        
        # Start the server
        await self.server.start()


async def main() -> None:
    """Run the EIP Repository MCP server."""
    parser = argparse.ArgumentParser(description="EIP Repository MCP Server")
    parser.add_argument("--eips-dir", type=str, default=DEFAULT_EIPS_DIR,
                        help=f"Directory containing EIP files (default: {DEFAULT_EIPS_DIR})")
    args = parser.parse_args()
    
    # Create and start the server
    server = EIPRepositoryServer(eips_dir=args.eips_dir)
    await server.start_server()


if __name__ == "__main__":
    asyncio.run(main()) 