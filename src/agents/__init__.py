"""
Agent module for Kephra.

Defines various agent types that perform different roles in the protocol governance system:
- Proposer agents for generating or formatting EIPs
- Reviewer agents for scrutinizing EIPs for correctness and alignment
- Simulator agents for testing and simulating the impact of proposed changes
- Consensus agents for coordinating decision-making
"""

from .base_agent import KephraAgent
from .proposer_agent import ProposerAgent
from .reviewer_agent import ReviewerAgent
from .simulator_agent import SimulatorAgent
from .consensus_agent import ConsensusAgent
from .github_agent import IssueTriageAgent

__all__ = [
    "KephraAgent",
    "ProposerAgent",
    "ReviewerAgent", 
    "SimulatorAgent",
    "ConsensusAgent",
    "IssueTriageAgent"
] 