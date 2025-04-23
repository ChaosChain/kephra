"""
Main entry point for the Kephra agent system.

This module initializes and runs the Kephra agents for Ethereum protocol governance.
It sets up the agent ecosystem, connects to necessary services, and provides
a command-line interface for interaction.
"""

import argparse
import logging
import os
import sys
import asyncio
from typing import Dict, List, Optional
import json  # for output formatting
from datetime import datetime
from pathlib import Path

# Add the site-packages directory to the path to ensure all dependencies are found
site_packages = Path(sys.executable).parent.parent / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
if site_packages.exists():
    sys.path.insert(0, str(site_packages))

from src.agents import KephraAgent, ProposerAgent, ReviewerAgent, SimulatorAgent, ConsensusAgent, IssueTriageAgent
from src.agents.eip_repository_agent import EIPRepositoryAgent
from src.common.mcp_integration import get_mcp_registry, get_mcp_registry_sync, MCPServerManager
from src.config.settings import settings
from src.models.agent_models import AgentConfig, AgentType
from src.workflow.autonomous_workflow import get_workflow, start_workflow, stop_workflow

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("kephra.log")
    ]
)

logger = logging.getLogger(__name__)


# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class KephraSystem:
    """
    Main system class for Kephra agents.
    
    This class manages the initialization, configuration, and execution
    of the Kephra agent ecosystem.
    """
    
    def __init__(self):
        """Initialize the Kephra system."""
        self.agents: Dict[str, KephraAgent] = {}
        self.mcp_registry = get_mcp_registry_sync()
        logger.info("Initializing Kephra system")
    
    async def initialize_agents(self, config_path: Optional[str] = None) -> None:
        """
        Initialize agents from configuration.
        
        Args:
            config_path: Path to agent configuration file (optional)
        """
        # For now, create a default set of agents
        # In a real implementation, this would load from config
        self._create_default_agents()
        
        # Initialize MCP if enabled
        if settings.mcp_enabled:
            # Get the registry (this will initialize it if needed)
            registry = await get_mcp_registry()
            
            # Start required MCP servers
            if settings.auto_start_mcp_servers:
                logger.info("Starting MCP servers...")
                server_results = await registry.server_manager.start_all_servers()
                
                # Log results
                for server_name, success in server_results.items():
                    if success:
                        logger.info(f"MCP server {server_name} started successfully")
                    else:
                        logger.warning(f"Failed to start MCP server {server_name}")
        
        logger.info(f"Initialized {len(self.agents)} agents")
    
    def _create_default_agents(self) -> None:
        """Create a default set of agents for testing."""
        # Create agents with default configurations
        self.agents["proposer_1"] = ProposerAgent(
            name="EIP Proposer",
            role="Ethereum Improvement Proposal Generator",
            goal="Create well-structured and valuable EIPs based on community needs",
            model=settings.default_agent_model,
            verbose=True
        )
        
        self.agents["reviewer_1"] = ReviewerAgent(
            name="Protocol Reviewer",
            role="Ethereum Protocol Reviewer",
            goal="Critically evaluate EIPs for correctness and alignment with Ethereum values",
            model=settings.default_agent_model,
            verbose=True
        )
        
        self.agents["reviewer_2"] = ReviewerAgent(
            name="Security Reviewer",
            role="Protocol Security Specialist",
            goal="Identify security implications and vulnerabilities in EIPs",
            model=settings.default_agent_model,
            verbose=True,
            expertise_areas=["Security", "Cryptography", "Smart Contracts"]
        )
        
        # Add simulator and consensus agents
        self.agents["simulator_1"] = SimulatorAgent(
            name="Protocol Simulator",
            role="Ethereum Protocol Simulator",
            goal="Simulate EIP behavior via testnets",
            model=settings.default_agent_model,
            verbose=True
        )
        self.agents["consensus_1"] = ConsensusAgent(
            name="EIP Consensus",
            role="Aggregate evaluations and reach final decision",
            goal="Determine final proposal verdict based on reviews and simulations",
            verbose=True
        )
    
    async def evaluate_proposal(self, proposal_path: str) -> Dict:
        """
        Evaluate an Ethereum proposal using the agent network.
        
        Args:
            proposal_path: Path to the proposal file (EIP)
            
        Returns:
            Evaluation results from all agents
        """
        logger.info(f"Evaluating proposal: {proposal_path}")
        
        # Load the proposal
        try:
            with open(proposal_path, "r") as f:
                proposal_content = f.read()
        except Exception as e:
            logger.error(f"Error loading proposal: {str(e)}")
            return {"status": "error", "message": f"Could not load proposal: {str(e)}"}
        
        # Parse the proposal using tools
        from src.tools.ethereum_tools import EIPParser
        eip_parser = EIPParser()
        proposal_data = eip_parser._run(proposal_content)
        
        # Have all reviewer agents evaluate the proposal
        evaluations = {}
        for agent_id, agent in self.agents.items():
            if isinstance(agent, ReviewerAgent):
                logger.info(f"Agent {agent_id} ({agent.name}) evaluating proposal")
                evaluation = agent.evaluate_proposal(
                    proposal_data["proposal_id"], 
                    proposal_data
                )
                evaluations[agent_id] = evaluation.dict()
        
        # Run simulations with SimulatorAgents
        simulations = {}
        for agent_id, agent in self.agents.items():
            if isinstance(agent, SimulatorAgent):
                sim_eval = agent.evaluate_proposal(
                    proposal_data["proposal_id"], proposal_data
                )
                simulations[agent_id] = sim_eval.dict()
        
        # Run consensus
        consensus_input = {
            "proposal_id": proposal_data["proposal_id"],
            "evaluations": {**evaluations, **simulations}
        }
        consensus_agent = next(
            ag for ag in self.agents.values() if isinstance(ag, ConsensusAgent)
        )
        consensus_result = consensus_agent.process(consensus_input)
        
        # Return full pipeline results
        return {
            "status": "success",
            "proposal_id": proposal_data["proposal_id"],
            "reviews": evaluations,
            "simulations": simulations,
            "consensus": consensus_result
        }
    
    async def start_autonomous_mode(self):
        """Start the system in autonomous mode."""
        logger.info("Starting Kephra in autonomous mode")
        
        # Enable autonomous mode in settings
        settings.autonomous_mode = True
        
        # Start the autonomous workflow
        await start_workflow()
    
    async def run(self) -> None:
        """Run the Kephra system."""
        logger.info("Kephra system running")
        
        # If autonomous mode is enabled, start the workflow
        if settings.autonomous_mode:
            await self.start_autonomous_mode()
        else:
            # Otherwise, just log that it's running
            logger.info("Kephra is ready to evaluate proposals")
            logger.info("Use CLI commands to interact with the system")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Kephra - Autonomous Core Dev Agents")
    
    # Add command line arguments
    parser.add_argument(
        "--config", 
        type=str,
        help="Path to agent configuration file"
    )
    
    parser.add_argument(
        "--evaluate",
        type=str,
        help="Path to proposal file to evaluate"
    )
    
    parser.add_argument(
        "--triage",
        type=str,
        help="GitHub owner/repo to triage issues (e.g. 'org/repo')"
    )
    
    parser.add_argument(
        "--list-eips",
        action="store_true",
        help="List all EIPs available in the MCP repository"
    )
    
    parser.add_argument(
        "--fetch-eip",
        type=str,
        help="Fetch EIP content by EIP ID (e.g. 'EIP-1559')"
    )
    
    parser.add_argument(
        "--autonomous",
        action="store_true",
        help="Run in autonomous mode (monitor GitHub, generate EIPs, etc.)"
    )
    
    parser.add_argument(
        "--mcp-servers",
        action="store_true",
        help="List available MCP servers and their status"
    )
    
    parser.add_argument(
        "--start-mcp",
        type=str,
        help="Start a specific MCP server by name"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


async def main_async():
    """Async version of the main entry point for the Kephra application."""
    args = parse_args()
    
    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and initialize the system
    system = KephraSystem()
    await system.initialize_agents(args.config)
    
    # Enable autonomous mode if requested
    if args.autonomous:
        settings.autonomous_mode = True
    
    # Handle MCP server listing
    if args.mcp_servers:
        mcp_registry = await get_mcp_registry()
        server_statuses = mcp_registry.server_manager.get_all_server_statuses()
        print(json.dumps(server_statuses, indent=2, cls=DateTimeEncoder))
        return 0
    
    # Handle MCP server starting
    if args.start_mcp:
        mcp_registry = await get_mcp_registry()
        success = await mcp_registry.server_manager.start_server(args.start_mcp)
        
        if success:
            print(f"Successfully started MCP server: {args.start_mcp}")
        else:
            print(f"Failed to start MCP server: {args.start_mcp}")
            return 1
        
        return 0

    # Handle GitHub issue triage
    if args.triage:
        try:
            owner, repo = args.triage.split("/")
        except ValueError:
            logger.error("--triage expects 'owner/repo'")
            return 1
        triage_agent = IssueTriageAgent(verbose=args.verbose)
        triage_result = triage_agent.process({"owner": owner, "repo": repo})
        print(json.dumps(triage_result, indent=2, cls=DateTimeEncoder))
        return 0

    # Handle listing EIPs via MCP
    if args.list_eips:
        repo_agent = EIPRepositoryAgent(verbose=args.verbose)
        eips = repo_agent.list_eips()
        print(json.dumps(eips, indent=2, cls=DateTimeEncoder))
        return 0

    # Handle fetching an EIP via MCP
    if args.fetch_eip:
        repo_agent = EIPRepositoryAgent(verbose=args.verbose)
        fetched = repo_agent.fetch_eip(args.fetch_eip)
        print(json.dumps(fetched, indent=2, cls=DateTimeEncoder))
        return 0

    # If evaluating a proposal, run full EIP pipeline (review, simulate, consensus)
    if args.evaluate:
        if os.path.exists(args.evaluate):
            full_result = await system.evaluate_proposal(args.evaluate)
            print(json.dumps(full_result, indent=2, cls=DateTimeEncoder))
        else:
            logger.error(f"Proposal file not found: {args.evaluate}")
            return 1
        return 0

    # Otherwise, just run the system
    await system.run()
    
    # If in autonomous mode, keep the program running
    if settings.autonomous_mode:
        try:
            # Keep the program running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            # Handle keyboard interrupt to gracefully shut down
            logger.info("Keyboard interrupt received, shutting down")
            await stop_workflow()
    
    return 0


def main():
    """Main entry point for the Kephra application."""
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main()) 