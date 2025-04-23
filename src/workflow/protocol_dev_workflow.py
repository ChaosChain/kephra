"""
Protocol Development Workflow for Kephra.

This module provides a complete workflow for Ethereum protocol development,
from GitHub issue analysis to EIP creation, review, and finalization.
Can be adapted for L2s and DAOs by modifying the configuration.
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import json

from src.agents.ethereum_core_dev_agent import EthereumCoreDevAgent
from src.agents.github_agent import IssueTriageAgent 
from src.agents.reviewer_agent import ReviewerAgent
from src.agents.consensus_agent import ConsensusAgent
from src.agents.simulator_agent import SimulatorAgent
from src.config.settings import settings
from src.models.agent_models import AgentConfig, AgentType, DecisionType
from src.common.mcp_integration import get_mcp_registry, MCPServerManager

logger = logging.getLogger(__name__)

class ProtocolDevWorkflow:
    """
    Complete workflow for Ethereum protocol development.
    
    This class orchestrates the entire process of protocol development:
    1. Monitoring GitHub issues for potential EIPs
    2. Creating EIP drafts using core developer agents
    3. Reviewing EIPs for technical correctness and standards compliance
    4. Simulating the impact of proposed changes
    5. Building consensus among multiple agents
    6. Submitting the EIP to the repository
    
    It can be adapted for different chains and governance models by
    adjusting the configuration settings.
    """
    
    def __init__(
        self,
        protocol_name: str = "Ethereum",
        chain_id: int = 1,
        num_core_devs: int = 3,
        num_reviewers: int = 2,
        governance_model: str = "eip",  # Options: eip, dao, l2
        mcp_servers: Optional[List[str]] = None,
        github_repo: str = "ethereum/EIPs",
        auto_submit: bool = False,
        verbose: bool = False
    ):
        """
        Initialize the Protocol Development Workflow.
        
        Args:
            protocol_name: Name of the protocol (Ethereum, Optimism, etc.)
            chain_id: Chain ID (1 for Ethereum mainnet)
            num_core_devs: Number of core developer agents to create
            num_reviewers: Number of reviewer agents to create
            governance_model: Type of governance model to use
            mcp_servers: List of MCP servers to use
            github_repo: GitHub repository to monitor for issues
            auto_submit: Whether to automatically submit EIPs
            verbose: Whether to log detailed information
        """
        self.protocol_name = protocol_name
        self.chain_id = chain_id
        self.num_core_devs = num_core_devs
        self.num_reviewers = num_reviewers
        self.governance_model = governance_model
        self.github_repo = github_repo
        self.auto_submit = auto_submit
        self.verbose = verbose
        
        # Set default MCP servers if none provided
        self.mcp_servers = mcp_servers or [
            "github",
            "eip_repository",
            "ethereum_validator",
            "ethereum_client",
        ]
        
        # Components
        self.server_manager = MCPServerManager()
        self.agents = {}
        self.proposals = {}
        self.issues = {}
        self.reviews = {}
        self.decisions = {}
        
        # Parse GitHub repo into owner/repo
        self.github_owner, self.github_repo_name = self._parse_github_repo(github_repo)
        
        # Create the agent configuration for this workflow
        self._setup_agents()
        
        logger.info(f"Initialized {protocol_name} Protocol Development Workflow with {num_core_devs} core devs and {num_reviewers} reviewers")
    
    async def initialize(self) -> bool:
        """Initialize the workflow by starting required MCP servers and initializing agents."""
        # Start required MCP servers
        logger.info(f"Starting required MCP servers: {self.mcp_servers}")
        results = await self.server_manager.start_all_servers()
        
        # Check if all servers started successfully
        missing_servers = [name for name, success in results.items() if not success]
        if missing_servers:
            logger.warning(f"Failed to start some MCP servers: {missing_servers}")
        
        # Initialize agents
        for agent_id, agent in self.agents.items():
            if hasattr(agent, "mcp_init_task") and agent.mcp_init_task is not None:
                await agent.mcp_init_task
        
        logger.info("Protocol development workflow initialized")
        return True
    
    async def run(self, continuous: bool = False, interval: int = 3600) -> None:
        """
        Run the protocol development workflow.
        
        Args:
            continuous: Whether to run continuously or just once
            interval: Seconds between runs when running continuously
        """
        while True:
            try:
                # Run the complete workflow
                await self._process_github_issues()
                await self._create_eip_proposals()
                await self._review_proposals()
                await self._simulate_proposals()
                await self._build_consensus()
                await self._finalize_proposals()
                
                if not continuous:
                    logger.info("Workflow completed successfully")
                    break
                
                logger.info(f"Waiting {interval} seconds before next run...")
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in protocol development workflow: {str(e)}")
                if not continuous:
                    raise
                
                logger.info(f"Waiting {interval} seconds before retry...")
                await asyncio.sleep(interval)
    
    async def _process_github_issues(self) -> Dict[str, Any]:
        """
        Process GitHub issues to identify potential EIPs.
        
        Returns:
            Dictionary with triaged issues
        """
        # Get the GitHub issue triage agent
        issue_agent = next((agent for agent in self.agents.values() 
                         if isinstance(agent, IssueTriageAgent)), None)
        
        if not issue_agent:
            logger.warning("No GitHub issue triage agent found")
            return {}
        
        logger.info(f"Processing GitHub issues from {self.github_owner}/{self.github_repo_name}")
        
        # Use the sync version for compatibility with both sync and async contexts
        result = issue_agent.process_sync({
            "owner": self.github_owner,
            "repo": self.github_repo_name,
            "state": "open"
        })
        
        # Store issues for later use
        if "triaged_issues" in result:
            triaged_issues = result["triaged_issues"]
            for issue in triaged_issues:
                issue_id = f"issue-{issue.get('number')}"
                self.issues[issue_id] = issue
            
            logger.info(f"Found {len(triaged_issues)} issues that need protocol improvements")
        
        return result
    
    async def _create_eip_proposals(self) -> Dict[str, Any]:
        """
        Create EIP proposals from triaged issues.
        
        Returns:
            Dictionary with created proposals
        """
        # Get core developer agents
        core_devs = [agent for agent in self.agents.values() 
                    if isinstance(agent, EthereumCoreDevAgent)]
        
        if not core_devs:
            logger.warning("No core developer agents found")
            return {}
        
        # Process each issue with a core developer agent
        created_proposals = {}
        
        for issue_id, issue in self.issues.items():
            # Skip issues that have already been processed
            if issue_id in self.proposals:
                continue
            
            # Select a core developer agent to create the proposal
            # In a more sophisticated implementation, we would match based on expertise
            core_dev = core_devs[hash(issue_id) % len(core_devs)]
            
            logger.info(f"Creating proposal for {issue_id} with core developer {core_dev.name}")
            
            # Create the proposal
            result = core_dev.process({
                "action": "create_eip",
                "issue_data": issue
            })
            
            if result.get("status") == "success":
                proposal_id = f"EIP-{issue_id.replace('issue-', '')}"
                self.proposals[proposal_id] = {
                    "issue_id": issue_id,
                    "proposal_id": proposal_id,
                    "eip_data": result.get("eip_data", {}),
                    "author": result.get("author"),
                    "created_at": None,  # Will be set after finalization
                    "status": "draft",
                    "reviews": {},
                    "simulation_results": {},
                    "consensus_result": None
                }
                
                created_proposals[proposal_id] = self.proposals[proposal_id]
                logger.info(f"Created proposal {proposal_id}")
            else:
                logger.warning(f"Failed to create proposal for {issue_id}: {result.get('message', 'Unknown error')}")
        
        logger.info(f"Created {len(created_proposals)} new proposals")
        return created_proposals
    
    async def _review_proposals(self) -> Dict[str, Dict[str, Any]]:
        """
        Review draft proposals with reviewer agents.
        
        Returns:
            Dictionary with review results
        """
        # Get reviewer agents
        reviewers = [agent for agent in self.agents.values() 
                   if isinstance(agent, ReviewerAgent)]
        
        if not reviewers:
            logger.warning("No reviewer agents found")
            return {}
        
        review_results = {}
        
        # Process each draft proposal with reviewers
        for proposal_id, proposal in self.proposals.items():
            # Skip proposals that are not in draft state
            if proposal.get("status") != "draft":
                continue
            
            # Skip proposals that have already been reviewed by all reviewers
            if len(proposal.get("reviews", {})) >= len(reviewers):
                continue
            
            logger.info(f"Reviewing proposal {proposal_id}")
            
            # Get each reviewer to review the proposal
            for reviewer in reviewers:
                # Skip if this reviewer has already reviewed this proposal
                if reviewer.name in proposal.get("reviews", {}):
                    continue
                
                logger.info(f"Reviewer {reviewer.name} evaluating {proposal_id}")
                
                # Perform the review
                review_result = reviewer.process({
                    "action": "review",
                    "proposal_id": proposal_id,
                    "proposal_data": proposal.get("eip_data", {})
                })
                
                # Store the review
                if review_result:
                    if "reviews" not in proposal:
                        proposal["reviews"] = {}
                    
                    proposal["reviews"][reviewer.name] = review_result
                    
                    if proposal_id not in review_results:
                        review_results[proposal_id] = {}
                    
                    review_results[proposal_id][reviewer.name] = review_result
                    
                    logger.info(f"Reviewer {reviewer.name} completed review of {proposal_id}")
        
        logger.info(f"Completed {sum(len(reviews) for reviews in review_results.values())} reviews for {len(review_results)} proposals")
        return review_results
    
    async def _simulate_proposals(self) -> Dict[str, Dict[str, Any]]:
        """
        Simulate the effects of proposals using simulator agents.
        
        Returns:
            Dictionary with simulation results
        """
        # Get simulator agents
        simulators = [agent for agent in self.agents.values() 
                    if isinstance(agent, SimulatorAgent)]
        
        if not simulators:
            logger.warning("No simulator agents found")
            return {}
        
        simulation_results = {}
        
        # Process each reviewed proposal with simulators
        for proposal_id, proposal in self.proposals.items():
            # Skip proposals that haven't been reviewed
            if not proposal.get("reviews", {}):
                continue
            
            # Skip proposals that have already been simulated
            if proposal.get("simulation_results", {}):
                continue
            
            logger.info(f"Simulating proposal {proposal_id}")
            
            # Use the first simulator for now
            # In a more sophisticated implementation, we would use multiple simulators
            simulator = simulators[0]
            
            # Perform the simulation
            simulation_result = simulator.process({
                "action": "simulate",
                "proposal_id": proposal_id,
                "proposal_data": proposal.get("eip_data", {})
            })
            
            # Store the simulation result
            if simulation_result:
                proposal["simulation_results"] = simulation_result
                simulation_results[proposal_id] = simulation_result
                
                logger.info(f"Completed simulation of {proposal_id}")
        
        logger.info(f"Completed simulations for {len(simulation_results)} proposals")
        return simulation_results
    
    async def _build_consensus(self) -> Dict[str, Dict[str, Any]]:
        """
        Build consensus among agents for reviewed and simulated proposals.
        
        Returns:
            Dictionary with consensus results
        """
        # Get consensus agents
        consensus_agents = [agent for agent in self.agents.values() 
                          if isinstance(agent, ConsensusAgent)]
        
        if not consensus_agents:
            logger.warning("No consensus agents found")
            return {}
        
        consensus_results = {}
        
        # Process each reviewed and simulated proposal with consensus agents
        for proposal_id, proposal in self.proposals.items():
            # Skip proposals that haven't been reviewed or simulated
            if not proposal.get("reviews", {}) or not proposal.get("simulation_results", {}):
                continue
            
            # Skip proposals that already have consensus
            if proposal.get("consensus_result") is not None:
                continue
            
            logger.info(f"Building consensus for proposal {proposal_id}")
            
            # Use the first consensus agent for now
            consensus_agent = consensus_agents[0]
            
            # Build consensus
            consensus_result = consensus_agent.process({
                "action": "build_consensus",
                "proposal_id": proposal_id,
                "proposal_data": proposal.get("eip_data", {}),
                "reviews": proposal.get("reviews", {}),
                "simulation_results": proposal.get("simulation_results", {})
            })
            
            # Store the consensus result
            if consensus_result:
                proposal["consensus_result"] = consensus_result
                consensus_results[proposal_id] = consensus_result
                
                # Update the proposal status based on consensus
                decision = consensus_result.get("decision")
                if decision == DecisionType.APPROVE:
                    proposal["status"] = "accepted"
                elif decision == DecisionType.REJECT:
                    proposal["status"] = "rejected"
                else:
                    proposal["status"] = "needs_revision"
                
                logger.info(f"Built consensus for {proposal_id}: {proposal['status']}")
        
        logger.info(f"Built consensus for {len(consensus_results)} proposals")
        return consensus_results
    
    async def _finalize_proposals(self) -> Dict[str, Dict[str, Any]]:
        """
        Finalize proposals by submitting accepted ones to the EIP repository.
        
        Returns:
            Dictionary with finalization results
        """
        # Skip if auto-submit is disabled
        if not self.auto_submit:
            logger.info("Auto-submit is disabled, skipping finalization")
            return {}
        
        finalization_results = {}
        
        # Get MCP registry for EIP repository access
        mcp_registry = await get_mcp_registry()
        
        # Process each accepted proposal
        for proposal_id, proposal in self.proposals.items():
            # Skip proposals that haven't been accepted
            if proposal.get("status") != "accepted":
                continue
            
            # Skip proposals that have already been finalized
            if proposal.get("created_at") is not None:
                continue
            
            logger.info(f"Finalizing proposal {proposal_id}")
            
            # Call the EIP repository MCP tool to create the EIP
            try:
                result = await mcp_registry.call_tool("create_eip", {
                    "eip_id": proposal_id,
                    "title": proposal.get("eip_data", {}).get("title", ""),
                    "author": proposal.get("eip_data", {}).get("author", ""),
                    "status": "Draft",
                    "type": proposal.get("eip_data", {}).get("type", "Standards Track"),
                    "category": proposal.get("eip_data", {}).get("category", "Core"),
                    "created": None,  # Let the server set the date
                    "abstract": proposal.get("eip_data", {}).get("abstract", ""),
                    "motivation": proposal.get("eip_data", {}).get("motivation", ""),
                    "specification": proposal.get("eip_data", {}).get("specification", ""),
                    "rationale": proposal.get("eip_data", {}).get("rationale", ""),
                    "implementation": proposal.get("eip_data", {}).get("implementation", "")
                })
                
                # Store the result
                if result.get("status") == "success":
                    proposal["created_at"] = result.get("created_at")
                    proposal["file_path"] = result.get("file_path")
                    proposal["status"] = "finalized"
                    
                    finalization_results[proposal_id] = result
                    
                    logger.info(f"Finalized proposal {proposal_id}: {result.get('file_path')}")
                else:
                    logger.warning(f"Failed to finalize proposal {proposal_id}: {result.get('message', 'Unknown error')}")
            
            except Exception as e:
                logger.error(f"Error finalizing proposal {proposal_id}: {str(e)}")
        
        logger.info(f"Finalized {len(finalization_results)} proposals")
        return finalization_results
    
    def _setup_agents(self) -> None:
        """Create and configure the agents needed for this workflow."""
        # Create GitHub issue triage agent
        self.agents["github_issue_triage"] = IssueTriageAgent(
            name="GitHub Issue Triage Agent",
            verbose=self.verbose
        )
        
        # Create core developer agents with different expertise areas
        core_dev_specialties = [
            ["consensus", "fork", "protocol"],
            ["evm", "gas", "performance"],
            ["networking", "p2p", "devp2p"],
            ["state", "storage", "trie"],
            ["security", "cryptography", "zero-knowledge"]
        ]
        
        for i in range(self.num_core_devs):
            idx = i % len(core_dev_specialties)
            expertise = core_dev_specialties[idx]
            is_champion = i == 0  # First core dev is designated as champion
            
            agent_id = f"core_dev_{i+1}"
            self.agents[agent_id] = EthereumCoreDevAgent(
                name=f"{self.protocol_name} Core Dev {i+1}",
                expertise_areas=expertise,
                is_champion=is_champion,
                chain_id=self.chain_id,
                verbose=self.verbose
            )
        
        # Create reviewer agents with different focus areas
        review_specialties = [
            ("Technical Reviewer", "Evaluate technical correctness and implementation feasibility"),
            ("Standards Reviewer", "Ensure compliance with protocol standards and conventions"),
            ("Security Reviewer", "Identify potential security implications and vulnerabilities"),
            ("Ecosystem Reviewer", "Assess impact on the broader ecosystem and existing applications")
        ]
        
        for i in range(self.num_reviewers):
            idx = i % len(review_specialties)
            role, goal = review_specialties[idx]
            
            agent_id = f"reviewer_{i+1}"
            self.agents[agent_id] = ReviewerAgent(
                name=f"{self.protocol_name} {role} {i+1}",
                role=role,
                goal=goal,
                verbose=self.verbose
            )
        
        # Create simulator agent
        self.agents["simulator"] = SimulatorAgent(
            name=f"{self.protocol_name} Protocol Simulator",
            verbose=self.verbose
        )
        
        # Create consensus agent
        self.agents["consensus"] = ConsensusAgent(
            name=f"{self.protocol_name} Consensus Builder",
            verbose=self.verbose
        )
        
        logger.info(f"Created {len(self.agents)} agents for the protocol development workflow")
    
    def _parse_github_repo(self, repo: str) -> Tuple[str, str]:
        """Parse GitHub repository string into owner and repo name."""
        parts = repo.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid GitHub repository format: {repo}. Expected format: owner/repo")
        
        return parts[0], parts[1]
    
    async def cleanup(self) -> None:
        """Clean up resources used by the workflow."""
        # Stop MCP servers
        await self.server_manager.stop_all_servers()
        
        # Clean up agents
        for agent in self.agents.values():
            if hasattr(agent, "cleanup"):
                await agent.cleanup()
        
        logger.info("Protocol development workflow cleaned up")
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "ProtocolDevWorkflow":
        """
        Create a ProtocolDevWorkflow from a configuration dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            An initialized ProtocolDevWorkflow
        """
        return cls(
            protocol_name=config.get("protocol_name", "Ethereum"),
            chain_id=config.get("chain_id", 1),
            num_core_devs=config.get("num_core_devs", 3),
            num_reviewers=config.get("num_reviewers", 2),
            governance_model=config.get("governance_model", "eip"),
            mcp_servers=config.get("mcp_servers"),
            github_repo=config.get("github_repo", "ethereum/EIPs"),
            auto_submit=config.get("auto_submit", False),
            verbose=config.get("verbose", False)
        )
    
    @classmethod
    def create_l2_workflow(cls, 
                          l2_name: str, 
                          chain_id: int,
                          governance_model: str = "dao",
                          **kwargs) -> "ProtocolDevWorkflow":
        """
        Create a workflow configured for an L2 chain.
        
        Args:
            l2_name: Name of the L2 (Optimism, Arbitrum, etc.)
            chain_id: Chain ID of the L2
            governance_model: Governance model to use (dao, multisig, etc.)
            kwargs: Additional keyword arguments for the workflow
            
        Returns:
            An initialized ProtocolDevWorkflow for the L2
        """
        return cls(
            protocol_name=l2_name,
            chain_id=chain_id,
            governance_model=governance_model,
            github_repo=kwargs.get("github_repo", f"{l2_name.lower()}/governance"),
            **kwargs
        )
    
    @classmethod
    def create_dao_workflow(cls,
                           dao_name: str,
                           chain_id: int = 1,  # Default to Ethereum mainnet
                           framework: str = "aragon",
                           **kwargs) -> "ProtocolDevWorkflow":
        """
        Create a workflow configured for a DAO.
        
        Args:
            dao_name: Name of the DAO
            chain_id: Chain ID where the DAO is deployed
            framework: DAO framework (aragon, daohaus, etc.)
            kwargs: Additional keyword arguments for the workflow
            
        Returns:
            An initialized ProtocolDevWorkflow for the DAO
        """
        return cls(
            protocol_name=dao_name,
            chain_id=chain_id,
            governance_model="dao",
            github_repo=kwargs.get("github_repo", f"{dao_name.lower()}/governance"),
            **{**{"dao_framework": framework}, **kwargs}
        ) 