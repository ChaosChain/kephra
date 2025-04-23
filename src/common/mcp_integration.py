"""
Model Context Protocol (MCP) integration for Kephra agents.

This module provides utilities for connecting agents to external tools and data sources
using Anthropic's Model Context Protocol (MCP). This enables agents to access real-world
data and perform actions beyond their training data.
"""

import logging
import json
import os
import subprocess
import signal
import sys
import time
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable, Set

from src.config.settings import settings

# Import MCP client if available, otherwise use mock
try:
    # Use the real MCP implementation from the official Python SDK
    from modelcontextprotocol.client import Client as MCPClient
    from modelcontextprotocol.client import ClientCapabilities
    from modelcontextprotocol.server import ServerCapabilities, ToolDefinition, ResourceDefinition
    from modelcontextprotocol.transport import StdioTransport, HttpTransport
    
    # Flag that we're using the actual MCP implementation
    USING_REAL_MCP = True
    logger = logging.getLogger(__name__)
    logger.info("Using real MCP implementation from the modelcontextprotocol package")
    
except ImportError:
    # If actual MCP package is unavailable, use mock implementation
    logger = logging.getLogger(__name__)
    logger.warning("MCP package not found. Using mock implementation.")
    USING_REAL_MCP = False
    
    class MockMCPClient:
        """Mock MCP client for development when actual MCP package is unavailable."""
        
        def __init__(self, host: str = None, port: int = None, transport_type: str = "stdio"):
            self.host = host
            self.port = port
            self.transport_type = transport_type
            self.connected = False
            self.available_tools = {}
            self.available_servers = []
            self.capabilities = {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "sampling": True
            }
        
        async def connect(self) -> bool:
            """Simulate connecting to MCP servers."""
            self.connected = True
            return True
        
        async def initialize(self) -> Dict[str, Any]:
            """Initialize connection with server."""
            return {"capabilities": self.capabilities}
        
        async def discover_servers(self) -> List[Dict[str, Any]]:
            """Simulate discovering available MCP servers."""
            # This would return a list of available servers in a real implementation
            self.available_servers = [
                {"name": "ethereum_node", "url": f"http://{self.host}:{self.port}/ethereum"},
                {"name": "eip_database", "url": f"http://{self.host}:{self.port}/eips"},
                {"name": "code_analyzer", "url": f"http://{self.host}:{self.port}/code"}
            ]
            return self.available_servers
        
        async def get_tools(self) -> Dict[str, Dict[str, Any]]:
            """Simulate getting available tools from connected servers."""
            # This would return available tools in a real implementation
            self.available_tools = {
                "ethereum_query": {
                    "name": "ethereum_query",
                    "description": "Query Ethereum blockchain data",
                    "server": "ethereum_node",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "method": {"type": "string", "description": "The RPC method to call"},
                            "params": {"type": "array", "description": "Parameters for the RPC call"}
                        },
                        "required": ["method"]
                    }
                },
                "eip_search": {
                    "name": "eip_search",
                    "description": "Search for EIPs",
                    "server": "eip_database",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "status": {"type": "string", "description": "Filter by EIP status"}
                        },
                        "required": ["query"]
                    }
                },
                "code_analysis": {
                    "name": "code_analysis",
                    "description": "Analyze code for issues",
                    "server": "code_analyzer",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Code to analyze"},
                            "language": {"type": "string", "description": "Programming language"}
                        },
                        "required": ["code"]
                    }
                }
            }
            return self.available_tools
        
        async def get_resources(self) -> Dict[str, Dict[str, Any]]:
            """Simulate getting available resources."""
            return {
                "eip_1559": {
                    "uri": "eip:1559",
                    "name": "EIP-1559",
                    "type": "text/markdown",
                    "content": "# EIP-1559: Fee Market Change"
                }
            }
        
        async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
            """Simulate calling a tool via MCP."""
            # This would actually call the tool in a real implementation
            # For now, return mock responses
            if tool_name == "ethereum_query":
                return {"status": "success", "data": {"block_number": 18000000, "gas_price": 20}}
            elif tool_name == "eip_search":
                return {"status": "success", "data": [{"id": "EIP-1559", "title": "Fee market change"}]}
            elif tool_name == "code_analysis":
                return {"status": "success", "data": {"issues": [], "complexity": "low"}}
            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}
        
        def disconnect(self) -> None:
            """Close the connection."""
            self.connected = False


class MCPServerManager:
    """
    Manager for MCP servers.
    
    This class handles starting, stopping, and managing MCP servers from
    the modelcontextprotocol/servers repository or custom local implementations.
    """
    
    def __init__(self):
        """Initialize the MCP Server Manager."""
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.server_processes: Dict[str, subprocess.Popen] = {}
        self.ports_in_use: Set[int] = set()
        self.base_port = settings.mcp_port
        self._load_server_configs()
    
    def _load_server_configs(self) -> None:
        """Load server configurations from settings."""
        # Define standard MCP servers needed for autonomous workflow
        self.servers = {
            "github": {
                "type": "npm",
                "package": "@modelcontextprotocol/server-github",
                "port": self.base_port,
                "args": [],
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": settings.github_token or os.environ.get("GITHUB_TOKEN", "")
                }
            },
            "filesystem": {
                "type": "npm",
                "package": "@modelcontextprotocol/server-filesystem",
                "port": self.base_port + 1,
                "args": [settings.filesystem_path or "."],
                "env": {}
            },
            "git": {
                "type": "pip",
                "package": "mcp-server-git",
                "port": self.base_port + 2,
                "args": ["--repository", settings.eip_repository_path or "./eip"],
                "env": {}
            },
            "eip_repository": {
                "type": "custom",  # Custom server implemented in the project
                "module": "src.servers.eip_repository_server",
                "port": self.base_port + 3,
                "args": [],
                "env": {}
            },
            "ethereum_validator": {
                "type": "custom",  # Custom server implemented in the project
                "module": "src.servers.ethereum_validator_server",
                "port": self.base_port + 4,
                "args": [],
                "env": {}
            }
        }
        
        # Override with custom configurations from settings
        if hasattr(settings, "mcp_server_configs") and settings.mcp_server_configs:
            for server_name, config in settings.mcp_server_configs.items():
                if server_name in self.servers:
                    self.servers[server_name].update(config)
                else:
                    self.servers[server_name] = config
    
    def get_server_url(self, server_name: str) -> Optional[str]:
        """
        Get the URL for a server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            URL of the server or None if server not found
        """
        if server_name not in self.servers:
            return None
        
        port = self.servers[server_name].get("port", self.base_port)
        return f"http://localhost:{port}"
    
    async def start_server(self, server_name: str) -> bool:
        """
        Start an MCP server.
        
        Args:
            server_name: Name of the server to start
            
        Returns:
            True if server started successfully, False otherwise
        """
        if server_name not in self.servers:
            logger.error(f"Server {server_name} not found in configuration")
            return False
        
        # Check if server is already running
        if server_name in self.server_processes:
            logger.info(f"Server {server_name} is already running")
            return True
        
        server_config = self.servers[server_name]
        port = server_config.get("port", self.base_port)
        
        # Check if port is already in use
        if port in self.ports_in_use:
            logger.error(f"Port {port} is already in use")
            return False
        
        # Start the server based on its type
        try:
            if server_config["type"] == "npm":
                # Start an npm package via npx
                cmd = ["npx", "-y", server_config["package"]]
                cmd.extend(server_config.get("args", []))
                
                # Add environment variables
                env = os.environ.copy()
                env.update(server_config.get("env", {}))
                env["PORT"] = str(port)
                
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
            elif server_config["type"] == "pip":
                # Start a Python package via module
                module_name = server_config["package"].replace("-", "_")
                cmd = [sys.executable, "-m", module_name]
                cmd.extend(server_config.get("args", []))
                
                # Add environment variables
                env = os.environ.copy()
                env.update(server_config.get("env", {}))
                env["PORT"] = str(port)
                
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
            elif server_config["type"] == "custom":
                # Start a custom module
                module_name = server_config["module"]
                cmd = [sys.executable, "-m", module_name]
                cmd.extend(server_config.get("args", []))
                
                # Add environment variables
                env = os.environ.copy()
                env.update(server_config.get("env", {}))
                env["PORT"] = str(port)
                
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            else:
                logger.error(f"Unknown server type: {server_config['type']}")
                return False
            
            # Store the process
            self.server_processes[server_name] = process
            self.ports_in_use.add(port)
            
            # Wait a short time to see if server crashes immediately
            await asyncio.sleep(2)
            
            if process.poll() is not None:
                # Process already exited
                stderr = process.stderr.read() if process.stderr else ""
                logger.error(f"Server {server_name} failed to start: {stderr}")
                self.server_processes.pop(server_name, None)
                self.ports_in_use.remove(port)
                return False
            
            logger.info(f"Started MCP server: {server_name} on port {port}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting server {server_name}: {str(e)}")
            return False
    
    async def start_all_servers(self) -> Dict[str, bool]:
        """
        Start all configured servers.
        
        Returns:
            Dictionary of server names and status (True if started successfully)
        """
        results = {}
        
        for server_name in self.servers:
            results[server_name] = await self.start_server(server_name)
        
        return results
    
    def stop_server(self, server_name: str) -> bool:
        """
        Stop an MCP server.
        
        Args:
            server_name: Name of the server to stop
            
        Returns:
            True if server stopped successfully, False otherwise
        """
        if server_name not in self.server_processes:
            logger.error(f"Server {server_name} is not running")
            return False
        
        try:
            process = self.server_processes[server_name]
            port = self.servers[server_name].get("port", self.base_port)
            
            # Try to terminate gracefully first
            process.terminate()
            
            # Wait a bit for graceful shutdown
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't exit
                process.kill()
            
            # Remove from tracking
            self.server_processes.pop(server_name, None)
            self.ports_in_use.remove(port)
            
            logger.info(f"Stopped MCP server: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping server {server_name}: {str(e)}")
            return False
    
    def stop_all_servers(self) -> None:
        """Stop all running MCP servers."""
        for server_name in list(self.server_processes.keys()):
            self.stop_server(server_name)
    
    def check_server_status(self, server_name: str) -> Dict[str, Any]:
        """
        Check the status of a server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            Dictionary with server status
        """
        if server_name not in self.servers:
            return {"status": "not_found", "message": f"Server {server_name} not found in configuration"}
        
        if server_name not in self.server_processes:
            return {"status": "stopped", "message": f"Server {server_name} is not running"}
        
        process = self.server_processes[server_name]
        returncode = process.poll()
        
        if returncode is not None:
            # Process has exited
            stderr = process.stderr.read() if process.stderr else ""
            return {
                "status": "crashed",
                "returncode": returncode,
                "message": f"Server {server_name} has crashed with code {returncode}",
                "stderr": stderr
            }
        
        return {
            "status": "running",
            "message": f"Server {server_name} is running",
            "port": self.servers[server_name].get("port", self.base_port)
        }
    
    def get_all_server_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the status of all servers.
        
        Returns:
            Dictionary of server names and status information
        """
        return {server_name: self.check_server_status(server_name) for server_name in self.servers}


class MCPToolRegistry:
    """
    Registry for MCP tools and servers.
    
    This class manages the connection to MCP servers and provides
    a unified interface for discovering and calling tools.
    """
    
    def __init__(self):
        """Initialize the MCP Tool Registry."""
        self.client = None
        self.connected = False
        self.available_tools = {}
        self.available_resources = {}
        self.available_servers = []
        self.tool_handlers = {}
        self.using_real_mcp = USING_REAL_MCP
        self.server_manager = MCPServerManager()
        
        # Initialize if enabled in settings
        if settings.mcp_enabled:
            self.initialize()
    
    async def initialize(self) -> bool:
        """Initialize connection to MCP servers."""
        try:
            if self.using_real_mcp:
                # Create client with appropriate transport based on configuration
                if settings.mcp_transport_type == "http":
                    transport = HttpTransport(settings.mcp_host, settings.mcp_port)
                else:  # Default to stdio for local process communication
                    # Check if a server path is specified
                    if settings.mcp_server_path and os.path.exists(settings.mcp_server_path):
                        transport = StdioTransport(settings.mcp_server_path)
                    else:
                        logger.error(f"MCP server path not found: {settings.mcp_server_path}")
                        return False
                
                # Create real MCP client
                self.client = MCPClient(
                    transport=transport,
                    capabilities=ClientCapabilities(
                        sampling=True,  # Enable LLM sampling capability
                        tools={"listChanged": True},
                        resources={"subscribe": True, "listChanged": True}
                    )
                )
                
                # Initialize and connect
                await self.client.initialize()
                self.connected = True
                
                # Get available tools and resources
                self.available_tools = await self.client.get_tools()
                self.available_resources = await self.client.get_resources()
                
                logger.info(f"Connected to MCP. Found {len(self.available_tools)} tools and {len(self.available_resources)} resources.")
                return True
            else:
                # Use mock implementation
                self.client = MockMCPClient(
                    host=settings.mcp_host,
                    port=settings.mcp_port,
                    transport_type=settings.mcp_transport_type
                )
                
                # Initialize and connect
                await self.client.initialize()
                self.connected = await self.client.connect()
                
                if self.connected:
                    self.available_servers = await self.client.discover_servers()
                    self.available_tools = await self.client.get_tools()
                    self.available_resources = await self.client.get_resources()
                    
                    logger.info(f"Connected to mock MCP. Found {len(self.available_servers)} servers, {len(self.available_tools)} tools, and {len(self.available_resources)} resources.")
                    return True
                else:
                    logger.error("Failed to connect to mock MCP.")
                    return False
        
        except Exception as e:
            logger.error(f"Error initializing MCP: {str(e)}")
            return False
    
    def register_tool_handler(self, tool_name: str, handler: Callable) -> None:
        """
        Register a handler function for a specific tool.
        
        This allows for custom processing of tool results.
        
        Args:
            tool_name: Name of the tool
            handler: Function to handle tool results
        """
        self.tool_handlers[tool_name] = handler
        logger.info(f"Registered handler for tool: {tool_name}")
    
    async def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get available MCP tools."""
        if not self.connected:
            if not await self.initialize():
                return {}
        
        # If using real MCP, refresh the tools list
        if self.using_real_mcp:
            try:
                self.available_tools = await self.client.get_tools()
            except Exception as e:
                logger.error(f"Error getting tools: {str(e)}")
        
        return self.available_tools
    
    async def get_available_resources(self) -> Dict[str, Dict[str, Any]]:
        """Get available MCP resources."""
        if not self.connected:
            if not await self.initialize():
                return {}
        
        # If using real MCP, refresh the resources list
        if self.using_real_mcp:
            try:
                self.available_resources = await self.client.get_resources()
            except Exception as e:
                logger.error(f"Error getting resources: {str(e)}")
        
        return self.available_resources
    
    def get_tool_details(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get details about a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool details or None if not found
        """
        return self.available_tools.get(tool_name)
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool via MCP.
        
        Args:
            tool_name: Name of the tool to call
            params: Parameters to pass to the tool
            
        Returns:
            Tool results
        """
        if not self.connected:
            if not await self.initialize():
                return {"status": "error", "message": "Not connected to MCP"}
        
        try:
            # Call the tool
            result = await self.client.call_tool(tool_name, params)
            
            # Apply custom handler if registered
            if tool_name in self.tool_handlers:
                result = self.tool_handlers[tool_name](result)
            
            return result
        
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_resource(self, resource_uri: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific resource by URI.
        
        Args:
            resource_uri: URI of the resource to retrieve
            
        Returns:
            Resource data or None if not found
        """
        if not self.connected:
            if not await self.initialize():
                return None
        
        try:
            if self.using_real_mcp:
                return await self.client.get_resource(resource_uri)
            else:
                # Mock implementation for resources
                if resource_uri == "eip:1559":
                    return self.available_resources.get("eip_1559")
                return None
        except Exception as e:
            logger.error(f"Error getting resource {resource_uri}: {str(e)}")
            return None
    
    async def subscribe_to_resource(self, resource_uri: str, callback: Callable) -> bool:
        """
        Subscribe to changes in a resource.
        
        Args:
            resource_uri: URI of the resource to subscribe to
            callback: Function to call when the resource changes
            
        Returns:
            Success status
        """
        if not self.connected or not self.using_real_mcp:
            logger.error("Resource subscription not available in current MCP setup")
            return False
        
        try:
            # This is a simplified implementation - in a real system, 
            # we would set up an actual subscription with the callback
            await self.client.subscribe_resource(resource_uri)
            logger.info(f"Subscribed to resource: {resource_uri}")
            return True
        except Exception as e:
            logger.error(f"Error subscribing to resource {resource_uri}: {str(e)}")
            return False
    
    async def request_llm_sampling(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Request LLM sampling from a client via MCP.
        
        Args:
            prompt: The prompt to send to the language model
            options: Additional options for sampling
            
        Returns:
            The LLM sampling result
        """
        if not self.connected:
            if not await self.initialize():
                return {"status": "error", "message": "Not connected to MCP"}
        
        try:
            if self.using_real_mcp:
                # Call the actual sampling method
                return await self.client.request_sampling(prompt, options or {})
            else:
                # Mock sampling response
                return {
                    "status": "success",
                    "text": f"Mock response to: {prompt[:30]}...",
                    "model": "mock-model"
                }
        except Exception as e:
            logger.error(f"Error requesting LLM sampling: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self.connected and self.client:
            try:
                if self.using_real_mcp:
                    await self.client.shutdown()
                else:
                    self.client.disconnect()
                self.connected = False
                logger.info("Disconnected from MCP server")
            except Exception as e:
                logger.error(f"Error disconnecting from MCP server: {str(e)}")


async def get_mcp_registry() -> MCPToolRegistry:
    """
    Get or create the MCP Tool Registry.
    
    This is a factory function that returns a singleton instance
    of the MCP Tool Registry, ensuring that there is only one
    connection to MCP servers in the application.
    
    Returns:
        MCPToolRegistry instance
    """
    if not hasattr(get_mcp_registry, "_instance"):
        get_mcp_registry._instance = MCPToolRegistry()
        
        # Make sure the registry is initialized
        if not get_mcp_registry._instance.connected:
            await get_mcp_registry._instance.initialize()
        
        # Start all required MCP servers for autonomous workflow
        if settings.mcp_enabled and settings.auto_start_mcp_servers:
            await get_mcp_registry._instance.server_manager.start_all_servers()
    
    return get_mcp_registry._instance


# Synchronous version for compatibility
def get_mcp_registry_sync() -> MCPToolRegistry:
    """Synchronous version of get_mcp_registry for compatibility."""
    if not hasattr(get_mcp_registry_sync, "_instance"):
        get_mcp_registry_sync._instance = MCPToolRegistry()
    
    return get_mcp_registry_sync._instance 