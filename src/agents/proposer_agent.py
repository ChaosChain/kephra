"""
Proposer Agent for Kephra.

This agent is responsible for generating or formatting EIPs for evaluation.
It can either create new proposals or format existing ones for review.
"""

import logging
from typing import Any, Dict, List, Optional

from src.agents.base_agent import KephraAgent
from src.models.agent_models import AgentConfig, AgentType, ProposalEvaluation
from src.tools.ethereum_tools import EIPParser

logger = logging.getLogger(__name__)


class ProposerAgent(KephraAgent):
    """
    Agent specialized in generating or formatting Ethereum protocol proposals.
    
    The proposer can create new EIPs based on community needs or format
    existing proposals for standardized evaluation by other agents.
    """
    
    def __init__(
        self,
        name: str,
        role: str = "Ethereum Improvement Proposal Generator",
        goal: str = "Create well-structured and valuable EIPs based on community needs",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        reputation_score: float = 1.0,
        tools: Optional[List[Any]] = None,
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize a Proposer Agent.
        
        Args:
            name: The agent's name
            role: The agent's role description
            goal: The agent's goal
            model: The LLM model to use
            temperature: Temperature setting for the model
            reputation_score: Initial reputation score
            tools: List of tools the agent can use
            verbose: Whether to log detailed information
            kwargs: Additional keyword arguments
        """
        # Initialize standard tools for proposer if none provided
        if tools is None:
            tools = [
                EIPParser(),
                # Add more specialized tools as needed
            ]
        
        super().__init__(
            name=name,
            role=role,
            goal=goal,
            agent_type=AgentType.PROPOSER,
            model=model,
            temperature=temperature,
            reputation_score=reputation_score,
            tools=tools,
            verbose=verbose,
        )
        
        # Proposer-specific attributes
        self.proposal_templates = kwargs.get("proposal_templates", {})
        self.proposal_count = 0
        
        logger.info(f"Initialized ProposerAgent: {name}")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data to generate or format an EIP.
        
        Args:
            input_data: Input data for proposal generation or formatting
            
        Returns:
            Processed proposal data
        """
        logger.info(f"Proposer {self.name} processing input")
        
        # Extract operation type
        operation = input_data.get("operation", "format")
        
        if operation == "generate":
            # Generate a new proposal
            return self._generate_proposal(input_data)
        elif operation == "format":
            # Format an existing proposal
            return self._format_proposal(input_data)
        elif operation == "generate_from_issue":
            # Generate an EIP draft directly from GitHub issue data
            return self._generate_eip_from_issue(input_data)
        else:
            logger.error(f"Unknown operation: {operation}")
            return {"status": "error", "message": f"Unknown operation: {operation}"}
    
    def _generate_proposal(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a new EIP based on input requirements.
        
        Args:
            input_data: Requirements for the new proposal
            
        Returns:
            Generated proposal data
        """
        # This is a placeholder implementation
        # In a real system, this would use the LLM to generate an EIP
        
        # Extract requirements
        title = input_data.get("title", "Untitled Proposal")
        problem_statement = input_data.get("problem_statement", "")
        solution_outline = input_data.get("solution_outline", "")
        
        # Prepare prompt for the agent
        prompt = (
            f"You are a core developer proposing an improvement to Ethereum.\n"
            f"Generate a well-structured EIP with the following details:\n"
            f"Title: {title}\n"
            f"Problem Statement: {problem_statement}\n"
            f"Solution Outline: {solution_outline}\n"
            f"Follow standard EIP format and include all necessary sections."
        )
        
        # Generate proposal using the agent's LLM
        # In a real implementation, this would use the agent's LLM to generate the proposal
        # For now, just return a simple mock response
        
        self.proposal_count += 1
        proposal_id = f"EIP-DRAFT-{self.proposal_count}"
        
        # Mock response
        return {
            "status": "success",
            "proposal_id": proposal_id,
            "title": title,
            "content": f"# EIP-DRAFT: {title}\n\n## Abstract\n\nThis is a draft proposal addressing: {problem_statement}\n\n## Specification\n\nMock specification based on: {solution_outline}",
            "metadata": {
                "generated_by": self.name,
                "timestamp": None  # Would be set to current timestamp in a real implementation
            }
        }
    
    def _format_proposal(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format an existing proposal to conform to standard EIP format.
        
        Args:
            input_data: Original proposal data to format
            
        Returns:
            Formatted proposal data
        """
        # This is a placeholder implementation
        
        # Extract original content
        original_content = input_data.get("content", "")
        proposal_id = input_data.get("proposal_id", "Unknown")
        
        # In a real implementation, this would use the agent's LLM to format the proposal
        # For now, just return the original content with a note
        
        return {
            "status": "success",
            "proposal_id": proposal_id,
            "content": original_content,
            "metadata": {
                "formatted_by": self.name,
                "timestamp": None  # Would be set to current timestamp in a real implementation
            },
            "message": "Proposal formatting is not fully implemented in this version"
        }
    
    def _generate_eip_from_issue(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a new EIP draft based on GitHub issue information.
        input_data must contain 'title' and 'body' for the issue.
        """
        # Extract issue fields
        title = input_data.get("title", "Untitled Issue")
        problem_statement = input_data.get("body", "")
        # Ask LLM for a solution outline
        outline_prompt = (
            f"Given the Ethereum issue described below, provide a concise solution outline:\n\n"
            f"Title: {title}\n\nDescription: {problem_statement}"
        )
        outline_resp = self.agent.chat(outline_prompt)
        solution_outline = outline_resp.content.strip()
        # Delegate to existing EIP generator
        return self._generate_proposal({
            "operation": "generate",
            "title": title,
            "problem_statement": problem_statement,
            "solution_outline": solution_outline
        })
    
    @classmethod
    def from_config(cls, config: AgentConfig) -> "ProposerAgent":
        """
        Create a ProposerAgent from a configuration object.
        
        Args:
            config: Agent configuration
            
        Returns:
            An initialized ProposerAgent
        """
        return cls(
            name=config.name,
            role=config.role,
            goal=config.goal,
            model=config.model,
            temperature=config.temperature,
            reputation_score=config.reputation_score,
            verbose=config.verbose,
            **config.additional_config
        ) 