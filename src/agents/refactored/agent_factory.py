"""
Agent Factory for Kephra.

This module provides a unified factory for creating and managing agents
in the Kephra system. It centralizes all agent initialization and configuration
logic to simplify agent creation and ensure consistency.
"""

import logging
from typing import Any, Dict, List, Optional, Type, Union

from src.agents.base_agent import KephraAgent
from src.agents.proposer_agent import ProposerAgent
from src.agents.reviewer_agent import ReviewerAgent
from src.agents.simulator_agent import SimulatorAgent
from src.agents.consensus_agent import ConsensusAgent
from src.agents.github_agent import IssueTriageAgent
from src.agents.eip_repository_agent import EIPRepositoryAgent
from src.agents.ethereum_core_dev_agent import EthereumCoreDevAgent
from src.agents.validator_agent import ValidatorAgent
from src.models.agent_models import AgentConfig, AgentType
from src.config.settings import settings

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating and managing Kephra agents.
    
    This class centralizes the creation of agent instances, ensuring
    consistent initialization and configuration. It provides methods
    for creating individual agents as well as predefined agent groups.
    """
    
    # Registry of agent types to their implementation classes
    _agent_registry = {
        AgentType.PROPOSER: ProposerAgent,
        AgentType.REVIEWER: ReviewerAgent,
        AgentType.SIMULATOR: SimulatorAgent,
        AgentType.CONSENSUS: ConsensusAgent,
        AgentType.GITHUB: IssueTriageAgent,
        AgentType.REPOSITORY: EIPRepositoryAgent,
        AgentType.CORE_DEV: EthereumCoreDevAgent,
        AgentType.VALIDATOR: ValidatorAgent,
    }
    
    @classmethod
    def create_agent(cls, 
                    agent_type: Union[str, AgentType], 
                    config: Optional[Union[Dict[str, Any], AgentConfig]] = None, 
                    **kwargs) -> KephraAgent:
        """
        Create an agent of the specified type.
        
        Args:
            agent_type: Type of agent to create, either as AgentType enum or string
            config: Optional configuration for the agent
            **kwargs: Additional arguments to pass to the agent constructor
            
        Returns:
            A new agent instance
            
        Raises:
            ValueError: If the agent type is not supported
        """
        # Convert string to enum if necessary
        if isinstance(agent_type, str):
            try:
                agent_type = AgentType[agent_type.upper()]
            except KeyError:
                raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Get the agent class
        if agent_type not in cls._agent_registry:
            raise ValueError(f"Unsupported agent type: {agent_type}")
            
        agent_class = cls._agent_registry[agent_type]
        
        # Create agent configuration if not provided
        if config is None:
            config = {}
        
        # Convert dict to AgentConfig if necessary
        if isinstance(config, dict):
            # Extract base config items
            name = config.pop("name", f"{agent_type.value}-agent")
            role = config.pop("role", None)
            goal = config.pop("goal", None)
            model = config.pop("model", settings.default_agent_model)
            temperature = config.pop("temperature", settings.temperature)
            reputation_score = config.pop("reputation_score", 1.0)
            verbose = config.pop("verbose", False)
            
            # Create the config object
            agent_config = AgentConfig(
                name=name,
                role=role,
                goal=goal,
                agent_type=agent_type,
                model=model,
                temperature=temperature,
                reputation_score=reputation_score,
                verbose=verbose,
                additional_config=config  # All remaining items go in additional_config
            )
        else:
            agent_config = config
            
        # Update with any provided kwargs
        for key, value in kwargs.items():
            setattr(agent_config, key, value)
            
        # Create and return the agent
        logger.info(f"Creating agent of type {agent_type}: {agent_config.name}")
        return agent_class.from_config(agent_config)
    
    @classmethod
    def create_agent_group(cls, group_name: str, 
                          num_agents: Optional[int] = None, 
                          config: Optional[Dict[str, Any]] = None) -> Dict[str, KephraAgent]:
        """
        Create a group of agents based on a predefined configuration.
        
        Args:
            group_name: Name of the agent group (e.g., 'ethereum_core', 'l2_builders')
            num_agents: Optional override for number of agents to create
            config: Optional configuration overrides
            
        Returns:
            Dictionary of created agents with their IDs as keys
        """
        agents = {}
        
        if group_name == "ethereum_core":
            # Create a group of Ethereum Core development agents
            num_core_devs = num_agents or settings.ethereum["num_core_devs"]
            num_reviewers = num_agents or settings.ethereum["num_reviewers"]
            
            # Create core developers
            for i in range(num_core_devs):
                agent_id = f"core_dev_{i+1}"
                expertise = ["consensus", "evm", "networking"][i % 3]  # Simple rotation
                
                core_dev = cls.create_agent(
                    AgentType.CORE_DEV,
                    name=f"Core Dev {i+1}",
                    role="Ethereum Protocol Developer",
                    goal="Improve the Ethereum protocol through careful design and implementation",
                    expertise_areas=[expertise],
                    is_champion=(i == 0),  # First agent is a champion
                    verbose=(i == 0)  # Only log details for first agent
                )
                agents[agent_id] = core_dev
            
            # Create reviewers
            for i in range(num_reviewers):
                agent_id = f"reviewer_{i+1}"
                
                # Alternate between protocol and security reviewers
                if i % 2 == 0:
                    expertise_areas = ["Protocol", "Consensus", "Networking"]
                    role = "Protocol Reviewer"
                else:
                    expertise_areas = ["Security", "Cryptography", "Smart Contracts"]
                    role = "Security Reviewer"
                
                reviewer = cls.create_agent(
                    AgentType.REVIEWER,
                    name=f"{role} {i+1}",
                    role=role,
                    goal="Critically evaluate proposals for correctness and alignment with Ethereum values",
                    expertise_areas=expertise_areas,
                    verbose=(i == 0)  # Only log details for first reviewer
                )
                agents[agent_id] = reviewer
                
            # Create supporting agents (one of each)
            agents["issue_triage"] = cls.create_agent(
                AgentType.GITHUB,
                name="Issue Triage Agent",
                role="GitHub Issue Analyzer",
                goal="Identify and prioritize issues that require EIPs"
            )
            
            agents["eip_repo"] = cls.create_agent(
                AgentType.REPOSITORY,
                name="EIP Repository Manager",
                role="Manage EIP submissions and updates",
                goal="Keep the EIP repository organized and up-to-date"
            )
            
            agents["consensus"] = cls.create_agent(
                AgentType.CONSENSUS,
                name="EIP Consensus",
                role="Aggregate evaluations and reach final decision",
                goal="Determine final proposal verdict based on reviews and simulations"
            )
            
        elif group_name == "dao_governance":
            # DAO governance-focused agent group
            # (Implementation details would go here)
            pass
            
        elif group_name == "l2_developers":
            # L2-specific agent group
            # (Implementation details would go here)
            pass
            
        else:
            raise ValueError(f"Unknown agent group: {group_name}")
            
        logger.info(f"Created agent group '{group_name}' with {len(agents)} agents")
        return agents
    
    @classmethod
    def register_agent_type(cls, agent_type: AgentType, agent_class: Type[KephraAgent]) -> None:
        """
        Register a new agent type with the factory.
        
        Args:
            agent_type: The agent type enum value
            agent_class: The agent implementation class
        """
        cls._agent_registry[agent_type] = agent_class
        logger.info(f"Registered new agent type: {agent_type}") 