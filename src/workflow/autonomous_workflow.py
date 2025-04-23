"""
Autonomous workflow system for Kephra.

This module implements a fully autonomous workflow for Ethereum governance,
integrating various MCP servers to handle the complete process from issue
discovery to consensus building and implementation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from src.agents import (
    KephraAgent, 
    ProposerAgent, 
    ReviewerAgent, 
    SimulatorAgent, 
    ConsensusAgent, 
    IssueTriageAgent
)
from src.agents.eip_repository_agent import EIPRepositoryAgent
from src.agents.mcp_enhanced_reviewer_agent import MCPEnhancedReviewerAgent
from src.common.mcp_integration import get_mcp_registry, get_mcp_registry_sync
from src.config.settings import settings
from src.models.agent_models import ProposalEvaluation, AgentType
from src.protocol_analyzer.metrics_analyzer import MetricsAnalyzer
from src.protocol_analyzer.protocol_data_manager import ProtocolDataManager

logger = logging.getLogger(__name__)


class AutonomousWorkflow:
    """
    Manages the autonomous workflow for Ethereum governance.
    
    This class integrates multiple agents and MCP servers to create a fully
    autonomous workflow that monitors GitHub issues, generates EIPs,
    implements and tests code, reviews proposals, and builds consensus.
    """
    
    def __init__(self):
        """Initialize the autonomous workflow."""
        self.running = False
        self.agents = {}
        self.mcp_registry = get_mcp_registry_sync()
        self.active_proposals = {}
        self.github_last_check = datetime.now() - timedelta(days=1)  # Force immediate check
        
        # Protocol analysis components
        self.data_manager = ProtocolDataManager()
        self.metrics_analyzer = MetricsAnalyzer(self.data_manager)
        
        # Initialize workflow state
        self.initialize()
    
    def initialize(self):
        """Initialize workflow state and agents."""
        logger.info("Initializing autonomous workflow")
        
        # Create agents
        self._create_agents()
        
        logger.info(f"Initialized {len(self.agents)} agents for autonomous workflow")
        
        # Generate initial protocol insights
        try:
            insights = self.metrics_analyzer.generate_insight_report()
            logger.info("Generated initial protocol insights")
            if insights.snapshot:
                logger.info(f"Protocol health scores - Network: {insights.snapshot.network_health_score:.2f}, "
                           f"Economic: {insights.snapshot.economic_health_score:.2f}, "
                           f"Security: {insights.snapshot.security_health_score or 0:.2f}")
        except Exception as e:
            logger.error(f"Error generating initial protocol insights: {str(e)}")
    
    def _create_agents(self):
        """Create the necessary agents for the workflow."""
        # Create a triage agent for GitHub issues
        self.agents["issue_triage"] = IssueTriageAgent(
            name="Issue Triage Agent",
            role="GitHub Issue Analyzer",
            goal="Identify and prioritize issues that require EIPs",
            model=settings.default_agent_model,
            verbose=True
        )
        
        # Create proposer agent for EIP generation
        self.agents["proposer"] = ProposerAgent(
            name="EIP Proposer",
            role="Ethereum Improvement Proposal Generator",
            goal="Create well-structured and valuable EIPs based on community needs",
            model=settings.default_agent_model,
            verbose=True
        )
        
        # Create MCPEnhancedReviewerAgent for protocol-aware reviews instead of standard ReviewerAgent
        self.agents["protocol_reviewer"] = MCPEnhancedReviewerAgent(
            name="Protocol Reviewer",
            role="Ethereum Protocol Reviewer with Protocol Metrics Integration",
            goal="Critically evaluate EIPs based on protocol metrics and Ethereum values",
            model=settings.default_agent_model,
            verbose=True,
            mcp_tools=[
                "search_eips",
                "check_eip_compatibility",
                "validate_solidity_code", 
                "analyze_gas_efficiency"
            ]
        )
        
        # Keep standard security reviewer
        self.agents["security_reviewer"] = ReviewerAgent(
            name="Security Reviewer",
            role="Protocol Security Specialist",
            goal="Identify security implications and vulnerabilities in EIPs",
            model=settings.default_agent_model,
            verbose=True,
            expertise_areas=["Security", "Cryptography", "Smart Contracts"]
        )
        
        # Create simulator agent for implementation and testing
        self.agents["simulator"] = SimulatorAgent(
            name="Protocol Simulator",
            role="Ethereum Protocol Simulator",
            goal="Simulate EIP behavior via testnets",
            model=settings.default_agent_model,
            verbose=True
        )
        
        # Create consensus agent for final decision making
        self.agents["consensus"] = ConsensusAgent(
            name="EIP Consensus",
            role="Aggregate evaluations and reach final decision",
            goal="Determine final proposal verdict based on reviews and simulations",
            verbose=True
        )
        
        # Create EIP repository agent for managing EIPs
        self.agents["eip_repository"] = EIPRepositoryAgent(
            name="EIP Repository Manager",
            role="Manage EIP submissions and updates",
            goal="Keep the EIP repository organized and up-to-date",
            verbose=True
        )
        
        logger.info("Created enhanced agents with protocol metrics integration")
    
    async def start(self):
        """Start the autonomous workflow."""
        if self.running:
            logger.warning("Autonomous workflow is already running")
            return
        
        logger.info("Starting autonomous workflow")
        self.running = True
        
        # Start MCP servers if not already running
        mcp_registry = await get_mcp_registry()
        server_statuses = mcp_registry.server_manager.get_all_server_statuses()
        
        # Check if required servers are running
        required_servers = ["github", "git", "filesystem"]
        missing_servers = [s for s in required_servers if server_statuses.get(s, {}).get("status") != "running"]
        
        if missing_servers:
            logger.info(f"Starting required MCP servers: {missing_servers}")
            await mcp_registry.server_manager.start_all_servers()
        
        # Start the main workflow loop
        try:
            await self._workflow_loop()
        except Exception as e:
            logger.error(f"Error in workflow loop: {str(e)}")
            self.running = False
            raise
    
    async def stop(self):
        """Stop the autonomous workflow."""
        logger.info("Stopping autonomous workflow")
        self.running = False
        
        # Stop MCP servers if needed
        if not settings.keep_servers_running:
            mcp_registry = await get_mcp_registry()
            mcp_registry.server_manager.stop_all_servers()
    
    async def _workflow_loop(self):
        """Main workflow loop."""
        while self.running:
            try:
                # 1. Check for new issues in GitHub
                if self._should_check_github():
                    await self._check_github_issues()
                
                # 2. Process pending proposals
                await self._process_pending_proposals()
                
                # 3. Wait for next cycle
                await asyncio.sleep(10)  # Short sleep between checks
                
            except Exception as e:
                logger.error(f"Error in workflow cycle: {str(e)}")
                await asyncio.sleep(30)  # Longer sleep after error
    
    def _should_check_github(self) -> bool:
        """Determine if it's time to check GitHub."""
        if not settings.autonomous_mode:
            return False
            
        time_since_last_check = datetime.now() - self.github_last_check
        return time_since_last_check.total_seconds() >= settings.issue_polling_interval
    
    async def _check_github_issues(self):
        """Check for new issues in GitHub that need EIPs."""
        logger.info("Checking GitHub for new issues")
        self.github_last_check = datetime.now()
        
        try:
            # Get the triage agent
            triage_agent = self.agents.get("issue_triage")
            
            if not triage_agent:
                logger.warning("Issue triage agent not found in agents dictionary")
                return
                
            # Check each configured repository
            for repo in settings.github_repos:
                repo_path = f"{settings.github_owner}/{repo}"
                logger.info(f"Checking repository: {repo_path}")
                
                # Process issues with the triage agent - use process_sync for synchronous calls
                # or await process_async for async calls
                if hasattr(triage_agent, 'process_sync'):
                    # Use the safe synchronous version that won't try to use asyncio.run
                    triage_results = triage_agent.process_sync({
                        "owner": settings.github_owner,
                        "repo": repo
                    })
                else:
                    # For compatibility - try to use the async method directly
                    try:
                        triage_results = await triage_agent.process_async({
                            "owner": settings.github_owner,
                            "repo": repo
                        })
                    except AttributeError:
                        # Fallback to regular process as a last resort
                        logger.warning("Using fallback to process method - this may cause asyncio errors")
                        triage_results = triage_agent.process({
                            "owner": settings.github_owner,
                            "repo": repo
                        })
                                
                # Filter for issues that need EIPs
                eip_needed_issues = [
                    issue for issue in triage_results.get("issues", [])
                    if issue.get("needs_eip", False)
                ]
                
                logger.info(f"Found {len(eip_needed_issues)} issues that need EIPs")
                
                # Queue issues for EIP generation if auto-generation is enabled
                if settings.auto_eip_generation and eip_needed_issues:
                    for issue in eip_needed_issues:
                        await self._generate_eip_for_issue(issue)
                
        except Exception as e:
            logger.error(f"Error checking GitHub issues: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def _generate_eip_for_issue(self, issue: Dict[str, Any]):
        """Generate an EIP for a GitHub issue."""
        logger.info(f"Generating EIP for issue #{issue.get('number')}: {issue.get('title')}")
        
        try:
            # Get the proposer agent
            proposer_agent = self.agents["proposer"]
            
            # Generate EIP
            eip_data = proposer_agent.process({
                "issue": issue,
                "github_url": f"https://github.com/{settings.github_owner}/{issue.get('repo')}/issues/{issue.get('number')}"
            })
            
            # Generate a unique ID with issue number and random string
            import random
            import string
            random_suffix = ''.join(random.choices(string.ascii_uppercase, k=6))
            issue_number = issue.get('number', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Store the generated EIP with a unique ID
            eip_id = eip_data.get("eip_id", f"EIP-DRAFT-{issue_number}-{timestamp}-{random_suffix}")
            
            # Create full EIP content in markdown format
            full_content = f"""---
eip: draft
title: {issue.get('title', 'Untitled Issue')}
author: Kephra Agent (Auto-generated)
status: Draft
type: Standards Track
category: Core
created: {datetime.now().isoformat()}
---

## Abstract

This EIP was automatically generated in response to GitHub issue #{issue.get('number')}: {issue.get('title')}. 
The full specification is being developed.

## Motivation

This EIP aims to address the issues raised in GitHub issue #{issue.get('number')}.
{issue.get('body', 'No additional details provided.')}

## Specification

The proposed solution builds upon the Ethereum protocol to ensure backward compatibility
while addressing the identified needs.

## Rationale

This approach was chosen to balance technical constraints with the needs expressed in the issue.

## Implementation

A reference implementation will be provided once the specification is finalized.
"""
            
            # Ensure the EIP data includes the full content
            if "full_content" not in eip_data:
                eip_data["full_content"] = full_content
            
            # Add to active proposals for processing
            self.active_proposals[eip_id] = {
                "eip_data": eip_data,
                "issue": issue,
                "status": "draft",
                "created_at": datetime.now(),
                "reviews": {},
                "simulations": {},
                "consensus": None
            }
            
            logger.info(f"Generated EIP {eip_id} for issue #{issue.get('number')}")
            
            # Submit to EIP repository if configured
            if settings.auto_submit_eips:
                await self._submit_eip_to_repository(eip_id)
            
        except Exception as e:
            logger.error(f"Error generating EIP for issue #{issue.get('number')}: {str(e)}")
    
    async def _submit_eip_to_repository(self, eip_id: str):
        """Submit an EIP to the repository."""
        logger.info(f"Submitting EIP {eip_id} to repository")
        
        try:
            # Get the EIP repository agent
            repo_agent = self.agents["eip_repository"]
            
            # Get the EIP data
            eip_data = self.active_proposals[eip_id]["eip_data"]
            
            # Submit to repository
            result = repo_agent.submit_eip(eip_data)
            
            # Update status
            if result.get("status") == "success":
                self.active_proposals[eip_id]["status"] = "submitted"
                logger.info(f"Successfully submitted EIP {eip_id} to repository")
            else:
                logger.error(f"Failed to submit EIP {eip_id}: {result.get('message')}")
            
        except Exception as e:
            logger.error(f"Error submitting EIP {eip_id} to repository: {str(e)}")
    
    async def _process_pending_proposals(self):
        """Process pending proposals through the review and consensus pipeline."""
        # Get proposals that need processing
        pending_proposals = [
            eip_id for eip_id, data in self.active_proposals.items()
            if data["status"] in ["draft", "submitted", "reviewed"] and 
            "consensus" not in data
        ]
        
        for eip_id in pending_proposals:
            proposal_data = self.active_proposals[eip_id]
            
            # Update status based on current state
            if proposal_data["status"] == "draft" or proposal_data["status"] == "submitted":
                if not proposal_data.get("reviews"):
                    # Send for review
                    await self._review_proposal(eip_id)
                
                # Check if all reviews are complete
                if self._are_reviews_complete(eip_id) and not proposal_data.get("simulations"):
                    # Send for simulation
                    await self._simulate_proposal(eip_id)
                
                # If reviews and simulations are complete, update status
                if self._are_reviews_complete(eip_id) and self._are_simulations_complete(eip_id):
                    self.active_proposals[eip_id]["status"] = "reviewed"
            
            # If fully reviewed, build consensus
            if proposal_data["status"] == "reviewed" and not proposal_data.get("consensus"):
                await self._build_consensus(eip_id)
    
    async def _review_proposal(self, eip_id: str):
        """Send a proposal for review by reviewer agents."""
        logger.info(f"Sending EIP {eip_id} for review")
        
        try:
            # Get reviewer agents
            reviewer_agents = [
                agent for agent_id, agent in self.agents.items()
                if isinstance(agent, ReviewerAgent)
            ]
            
            # Get the proposal data
            proposal_data = self.active_proposals[eip_id]["eip_data"]
            
            # Have each reviewer evaluate the proposal
            for reviewer in reviewer_agents:
                agent_id = reviewer.name
                
                # Skip if already reviewed
                if agent_id in self.active_proposals[eip_id].get("reviews", {}):
                    continue
                
                # Perform review
                evaluation = reviewer.evaluate_proposal(eip_id, proposal_data)
                
                # Store review
                if "reviews" not in self.active_proposals[eip_id]:
                    self.active_proposals[eip_id]["reviews"] = {}
                
                self.active_proposals[eip_id]["reviews"][agent_id] = evaluation.dict()
                
                logger.info(f"Reviewer {agent_id} evaluated EIP {eip_id}: {evaluation.decision}")
            
        except Exception as e:
            logger.error(f"Error reviewing EIP {eip_id}: {str(e)}")
    
    async def _simulate_proposal(self, eip_id: str):
        """Simulate a proposal using simulator agents."""
        logger.info(f"Simulating EIP {eip_id}")
        
        try:
            # Get simulator agents
            simulator_agents = [
                agent for agent_id, agent in self.agents.items()
                if isinstance(agent, SimulatorAgent)
            ]
            
            # Get the proposal data
            proposal_data = self.active_proposals[eip_id]["eip_data"]
            
            # Have each simulator evaluate the proposal
            for simulator in simulator_agents:
                agent_id = simulator.name
                
                # Skip if already simulated
                if agent_id in self.active_proposals[eip_id].get("simulations", {}):
                    continue
                
                # Perform simulation
                evaluation = simulator.evaluate_proposal(eip_id, proposal_data)
                
                # Store simulation results
                if "simulations" not in self.active_proposals[eip_id]:
                    self.active_proposals[eip_id]["simulations"] = {}
                
                self.active_proposals[eip_id]["simulations"][agent_id] = evaluation.dict()
                
                logger.info(f"Simulator {agent_id} evaluated EIP {eip_id}: {evaluation.decision}")
            
            # If auto implementation is enabled and implementation is needed
            if settings.auto_implementation and any(
                sim["decision"] == "APPROVE" for sim in 
                self.active_proposals[eip_id].get("simulations", {}).values()
            ):
                await self._implement_proposal(eip_id)
            
        except Exception as e:
            logger.error(f"Error simulating EIP {eip_id}: {str(e)}")
    
    async def _implement_proposal(self, eip_id: str):
        """Implement a proposal using the simulator agent."""
        logger.info(f"Implementing EIP {eip_id}")
        
        try:
            # Get simulator agent
            simulator = next(
                agent for agent_id, agent in self.agents.items()
                if isinstance(agent, SimulatorAgent)
            )
            
            # Get the proposal data
            proposal_data = self.active_proposals[eip_id]["eip_data"]
            
            # Implement the proposal
            implementation_result = simulator.implement_proposal(eip_id, proposal_data)
            
            # Store implementation results
            self.active_proposals[eip_id]["implementation"] = implementation_result
            
            logger.info(f"Implemented EIP {eip_id}: {implementation_result.get('status')}")
            
        except Exception as e:
            logger.error(f"Error implementing EIP {eip_id}: {str(e)}")
    
    async def _build_consensus(self, eip_id: str):
        """Build consensus for a reviewed proposal."""
        logger.info(f"Building consensus for EIP {eip_id}")
        
        try:
            # Get consensus agent
            consensus_agent = next(
                agent for agent_id, agent in self.agents.items()
                if isinstance(agent, ConsensusAgent)
            )
            
            # Prepare input for consensus
            consensus_input = {
                "proposal_id": eip_id,
                "evaluations": {
                    **self.active_proposals[eip_id].get("reviews", {}),
                    **self.active_proposals[eip_id].get("simulations", {})
                }
            }
            
            # Build consensus
            consensus_result = consensus_agent.process(consensus_input)
            
            # Store consensus results
            self.active_proposals[eip_id]["consensus"] = consensus_result
            self.active_proposals[eip_id]["status"] = "completed"
            
            logger.info(f"Consensus for EIP {eip_id}: {consensus_result.get('decision')}")
            
            # If approved, submit implementation
            if (consensus_result.get("decision") == "APPROVE" and
                settings.auto_implementation and
                "implementation" in self.active_proposals[eip_id]):
                await self._submit_implementation(eip_id)
            
        except Exception as e:
            logger.error(f"Error building consensus for EIP {eip_id}: {str(e)}")
    
    async def _submit_implementation(self, eip_id: str):
        """Submit implementation for an approved proposal."""
        logger.info(f"Submitting implementation for EIP {eip_id}")
        
        try:
            # Get the EIP repository agent
            repo_agent = self.agents["eip_repository"]
            
            # Get the implementation data
            implementation = self.active_proposals[eip_id]["implementation"]
            
            # Submit implementation
            result = repo_agent.submit_implementation(eip_id, implementation)
            
            # Update status
            if result.get("status") == "success":
                self.active_proposals[eip_id]["implementation_submitted"] = True
                logger.info(f"Successfully submitted implementation for EIP {eip_id}")
            else:
                logger.error(f"Failed to submit implementation for EIP {eip_id}: {result.get('message')}")
            
        except Exception as e:
            logger.error(f"Error submitting implementation for EIP {eip_id}: {str(e)}")
    
    def _are_reviews_complete(self, eip_id: str) -> bool:
        """Check if all reviews are complete for a proposal."""
        proposal_data = self.active_proposals[eip_id]
        
        # Get reviewer agents
        reviewer_agents = [
            agent_id for agent_id, agent in self.agents.items()
            if isinstance(agent, ReviewerAgent)
        ]
        
        # Check if all reviewers have submitted evaluations
        return all(
            reviewer_id in proposal_data.get("reviews", {})
            for reviewer_id in reviewer_agents
        )
    
    def _are_simulations_complete(self, eip_id: str) -> bool:
        """Check if all simulations are complete for a proposal."""
        proposal_data = self.active_proposals[eip_id]
        
        # Get simulator agents
        simulator_agents = [
            agent_id for agent_id, agent in self.agents.items()
            if isinstance(agent, SimulatorAgent)
        ]
        
        # Check if all simulators have submitted evaluations
        return all(
            simulator_id in proposal_data.get("simulations", {})
            for simulator_id in simulator_agents
        )


# Singleton instance
_workflow_instance = None


def get_workflow() -> AutonomousWorkflow:
    """Get the singleton workflow instance."""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = AutonomousWorkflow()
    return _workflow_instance


async def start_workflow():
    """Start the autonomous workflow."""
    workflow = get_workflow()
    await workflow.start()


async def stop_workflow():
    """Stop the autonomous workflow."""
    workflow = get_workflow()
    await workflow.stop() 