"""
Base agent class for the Kephra system.

This module defines the abstract base class for all Kephra agents, providing
common functionality and interfaces.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from src.config.settings import settings
from src.common.mcp_integration import get_mcp_registry
from src.models.agent_models import AgentConfig, ProposalEvaluation

# Define a custom Agent class instead of importing from crewai/framework
# This provides the same interface expected by our code
class Agent:
    """Custom Agent implementation to match the expected interface."""
    
    def __init__(
        self,
        name: str, 
        role: str,
        goal: str,
        backstory: str = "",
        verbose: bool = False,
        allow_delegation: bool = False,
        tools: Optional[List[Any]] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.verbose = verbose
        self.allow_delegation = allow_delegation
        self.tools = tools or []
        self.llm_config = llm_config or {}
        
    def __str__(self):
        return f"{self.name} ({self.role})"

logger = logging.getLogger(__name__)


class KephraAgent(ABC):
    """
    Abstract base class for all Kephra agents.
    
    This class provides common functionality for all agents in the system,
    including integration with MCP for external tools and resources.
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        agent_type: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        reputation_score: float = 1.0, 
        tools: Optional[List[Any]] = None,
        verbose: bool = False,
        mcp_tools: Optional[List[str]] = None,
        mcp_resources: Optional[List[str]] = None,
    ):
        """
        Initialize a Kephra agent.
        
        Args:
            name: The agent's name
            role: The agent's role description
            goal: The agent's goal
            agent_type: Type of agent (enum or string)
            model: Name of the LLM model to use
            temperature: Temperature setting for the model
            reputation_score: Initial reputation score
            tools: List of tools available to this agent
            verbose: Whether to log detailed information
            mcp_tools: List of MCP tool names this agent can use
            mcp_resources: List of MCP resource URIs this agent can access
        """
        self.name = name
        self.role = role
        self.goal = goal
        self.agent_type = agent_type
        self.reputation_score = reputation_score
        self.model = model or settings.default_agent_model
        self.temperature = temperature or settings.temperature
        self.verbose = verbose
        
        # Tool-related attributes
        self.tools = tools or []
        self.mcp_tools = mcp_tools or []
        self.mcp_resources = mcp_resources or []
        
        # MCP related attributes
        self.mcp_registry = None
        self.mcp_initialized = False
        self.mcp_available_tools = {}
        self.mcp_available_resources = {}
        
        # Create the underlying agent using CrewAI
        self.agent = self._create_agent()
        
        # Initialize MCP connections if enabled - this now returns an async task
        # to be awaited when the agent is actually used
        self.mcp_init_task = None
        if settings.mcp_enabled:
            self.mcp_init_task = self._initialize_mcp_async()
        
        logger.info(f"Initialized {agent_type} agent: {name}")
    
    def _create_agent(self) -> Agent:
        """Create the underlying CrewAI agent."""
        return Agent(
            name=self.name,
            role=self.role,
            goal=self.goal,
            backstory=f"I am a specialized AI agent designed to {self.role.lower()}. "
                      f"I focus on {self.goal.lower()}",
            verbose=self.verbose,
            allow_delegation=False,
            tools=self.tools,
            # Configure agent with appropriate model
            llm_config={
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": settings.max_tokens,
            }
        )
    
    def _initialize_mcp(self) -> None:
        """
        Initialize MCP client synchronously.
        
        This method creates an event loop if one doesn't exist and uses it
        to run the async initialization.
        """
        if not settings.mcp_enabled:
            return
        
        try:
            # Get or create an event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async initialization
            loop.run_until_complete(self._initialize_mcp_async())
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP client for {self.name}: {e}")
    
    async def _initialize_mcp_async(self) -> None:
        """
        Initialize Model Context Protocol client for tool integration asynchronously.
        
        This method connects to the MCP registry and initializes the available
        tools and resources that this agent can use.
        """
        if not settings.mcp_enabled:
            return
        
        try:
            # Get the MCP registry singleton
            self.mcp_registry = await get_mcp_registry()
            
            # Get available tools and resources
            self.mcp_available_tools = await self.mcp_registry.get_available_tools()
            self.mcp_available_resources = await self.mcp_registry.get_available_resources()
            
            logger.info(f"MCP initialized for agent {self.name} with "
                        f"{len(self.mcp_available_tools)} tools and "
                        f"{len(self.mcp_available_resources)} resources")
            
            self.mcp_initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize MCP client for {self.name}: {e}")
    
    async def ensure_mcp_initialized(self) -> bool:
        """
        Ensure MCP is initialized before using it.
        
        Returns:
            Whether MCP is successfully initialized
        """
        if not settings.mcp_enabled:
            return False
        
        if not self.mcp_initialized:
            if self.mcp_init_task:
                await self.mcp_init_task
            else:
                await self._initialize_mcp_async()
                
        return self.mcp_initialized
    
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """
        Process input data according to the agent's role.
        
        This method must be implemented by each specific agent type.
        
        Args:
            input_data: The data to process (EIP, code, simulation results, etc.)
            
        Returns:
            Processed output data
        """
        pass
    
    async def process_async(self, input_data: Any) -> Any:
        """
        Process input data according to the agent's role asynchronously.
        
        This method provides an asynchronous wrapper around the process method.
        Subclasses can override this for fully asynchronous processing.
        
        Args:
            input_data: The data to process (EIP, code, simulation results, etc.)
            
        Returns:
            Processed output data
        """
        # Ensure MCP is initialized if enabled
        if settings.mcp_enabled:
            await self.ensure_mcp_initialized()
        
        # Default implementation just calls the synchronous process method
        return self.process(input_data)
    
    async def call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool with the given parameters.
        
        Args:
            tool_name: Name of the tool to call
            params: Parameters to pass to the tool
            
        Returns:
            Tool results
        """
        if not await self.ensure_mcp_initialized():
            logger.error(f"MCP not initialized for agent {self.name}, cannot call tool: {tool_name}")
            return {"status": "error", "message": "MCP not initialized"}
        
        # Check if the agent has access to this tool
        if self.mcp_tools and tool_name not in self.mcp_tools:
            logger.warning(f"Agent {self.name} attempting to use unauthorized tool: {tool_name}")
            return {"status": "error", "message": f"Agent not authorized to use tool: {tool_name}"}
        
        # Call the tool through the MCP registry
        return await self.mcp_registry.call_tool(tool_name, params)
    
    async def get_mcp_resource(self, resource_uri: str) -> Optional[Dict[str, Any]]:
        """
        Get an MCP resource by URI.
        
        Args:
            resource_uri: URI of the resource to retrieve
            
        Returns:
            Resource data or None if not found
        """
        if not await self.ensure_mcp_initialized():
            logger.error(f"MCP not initialized for agent {self.name}, cannot get resource: {resource_uri}")
            return None
        
        # Check if the agent has access to this resource
        if self.mcp_resources and resource_uri not in self.mcp_resources:
            logger.warning(f"Agent {self.name} attempting to access unauthorized resource: {resource_uri}")
            return None
        
        # Get the resource through the MCP registry
        return await self.mcp_registry.get_resource(resource_uri)
    
    async def request_llm_sampling(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Request LLM sampling via MCP.
        
        This allows MCP servers to request sampling from the client's LLM.
        
        Args:
            prompt: The prompt to send to the language model
            options: Additional options for sampling
            
        Returns:
            The LLM sampling result
        """
        if not await self.ensure_mcp_initialized():
            logger.error(f"MCP not initialized for agent {self.name}, cannot request LLM sampling")
            return {"status": "error", "message": "MCP not initialized"}
        
        return await self.mcp_registry.request_llm_sampling(prompt, options)
    
    def update_reputation(self, delta: float) -> None:
        """
        Update the agent's reputation score based on performance.
        
        Args:
            delta: The change in reputation (positive or negative)
        """
        old_score = self.reputation_score
        self.reputation_score = max(0.01, min(10.0, self.reputation_score + delta))
        logger.info(f"Updated {self.name}'s reputation: {old_score:.2f} -> {self.reputation_score:.2f}")
    
    def evaluate_proposal(self, proposal_id: str, proposal_data: Dict[str, Any]) -> ProposalEvaluation:
        """
        Evaluate a proposal and return a structured evaluation.
        
        Args:
            proposal_id: Unique identifier of the proposal
            proposal_data: The proposal data to evaluate
            
        Returns:
            A structured evaluation of the proposal
        """
        # This is a base implementation - each agent type would override this
        # with its specialized evaluation logic
        return ProposalEvaluation(
            proposal_id=proposal_id,
            agent_id=self.name,
            agent_type=self.agent_type,
            decision="ABSTAIN",
            confidence=0.0,
            reasoning="Base agent cannot evaluate proposals.",
            reputation_weight=self.reputation_score
        )
    
    async def evaluate_proposal_async(self, proposal_id: str, proposal_data: Dict[str, Any]) -> ProposalEvaluation:
        """
        Evaluate a proposal asynchronously and return a structured evaluation.
        
        This method provides an asynchronous wrapper around the evaluate_proposal method.
        Subclasses can override this for fully asynchronous evaluation.
        
        Args:
            proposal_id: Unique identifier of the proposal
            proposal_data: The proposal data to evaluate
            
        Returns:
            A structured evaluation of the proposal
        """
        # Ensure MCP is initialized if enabled
        if settings.mcp_enabled:
            await self.ensure_mcp_initialized()
        
        # Default implementation just calls the synchronous evaluate_proposal method
        return self.evaluate_proposal(proposal_id, proposal_data)
    
    def vote(self, proposal_id: str, decision: str, confidence: float, reasoning: str) -> Dict[str, Any]:
        """
        Cast a vote on a proposal with reasoning.
        
        Args:
            proposal_id: The ID of the proposal being voted on
            decision: The decision ("APPROVE", "REJECT", "ABSTAIN")
            confidence: Confidence level (0.0 to 1.0)
            reasoning: Reasoning behind the decision
            
        Returns:
            Vote result information
        """
        vote_data = {
            "proposal_id": proposal_id,
            "agent_id": self.name,
            "agent_type": self.agent_type,
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "reputation_weight": self.reputation_score,
            "timestamp": None  # Would be set to current timestamp in a real implementation
        }
        
        logger.info(f"{self.name} voted {decision} on proposal {proposal_id}")
        
        return vote_data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation for serialization."""
        return {
            "name": self.name,
            "role": self.role,
            "goal": self.goal,
            "agent_type": self.agent_type, 
            "model": self.model,
            "temperature": self.temperature,
            "reputation_score": self.reputation_score,
            "tools": [tool.__class__.__name__ for tool in self.tools],
            "mcp_tools": self.mcp_tools,
            "mcp_resources": self.mcp_resources
        }
    
    @classmethod
    def from_config(cls, config: AgentConfig) -> "KephraAgent":
        """
        Create an agent from a configuration object.
        
        This is a factory method that needs to be implemented by subclasses.
        
        Args:
            config: Agent configuration
            
        Returns:
            An initialized agent
        """
        raise NotImplementedError("Subclasses must implement from_config")
    
    async def cleanup(self) -> None:
        """
        Clean up resources used by the agent.
        
        This method should be called when the agent is no longer needed.
        """
        # For now, just disconnect from MCP if initialized
        if self.mcp_initialized and self.mcp_registry:
            await self.mcp_registry.disconnect() 