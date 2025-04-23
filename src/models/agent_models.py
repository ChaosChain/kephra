"""
Pydantic models for agent configuration and data structures.

This module defines the data models used throughout the Kephra agent system,
including configuration models and data structures for evaluation and consensus.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Types of agents in the Kephra system."""

    PROPOSER = "proposer"
    REVIEWER = "reviewer"
    SIMULATOR = "simulator"
    CONSENSUS = "consensus"


class DecisionType(str, Enum):
    """Decision types for proposal evaluation."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ABSTAIN = "ABSTAIN"


class ReputationScore(BaseModel):
    """Model for an agent's reputation score."""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    score: float = Field(
        default=1.0,
        ge=0.01,
        le=10.0,
        description="Reputation score (0.01 to 10.0)"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="When the score was last updated"
    )


class AgentConfig(BaseModel):
    """Configuration for a Kephra agent."""

    name: str = Field(..., description="Agent name")
    role: str = Field(..., description="Agent role description")
    goal: str = Field(..., description="Agent goal")
    agent_type: AgentType = Field(..., description="Type of agent")
    model: str = Field(..., description="LLM model to use")
    temperature: float = Field(0.2, description="Temperature setting for the model")
    tools: List[str] = Field(default_factory=list, description="Tool IDs the agent can use")
    reputation_score: float = Field(1.0, description="Initial reputation score")
    verbose: bool = Field(False, description="Whether to enable verbose logging")
    additional_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional agent-specific configuration"
    )


class ProposalEvaluation(BaseModel):
    """Evaluation of a proposal by an agent."""

    proposal_id: str = Field(..., description="Unique identifier for the proposal")
    agent_id: str = Field(..., description="ID of the agent providing the evaluation")
    agent_type: str = Field(..., description="Type of the agent")
    decision: DecisionType = Field(..., description="Decision on the proposal")
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence in the decision (0.0 to 1.0)"
    )
    reasoning: str = Field(..., description="Reasoning behind the decision")
    reputation_weight: float = Field(
        1.0, description="Reputation weight of the agent at evaluation time"
    )
    evaluation_time: datetime = Field(
        default_factory=datetime.now, 
        description="When the evaluation was performed"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metrics from the evaluation (e.g., test results, performance impact)"
    )


class ConsensusResult(BaseModel):
    """Result of a consensus process on a proposal."""

    proposal_id: str = Field(..., description="Unique identifier for the proposal")
    decision: DecisionType = Field(..., description="Final consensus decision")
    approval_weight: float = Field(
        0.0, description="Total weighted approval (reputation-weighted)"
    )
    rejection_weight: float = Field(
        0.0, description="Total weighted rejection (reputation-weighted)"
    )
    abstain_weight: float = Field(
        0.0, description="Total weighted abstention (reputation-weighted)"
    )
    total_weight: float = Field(
        0.0, description="Total weight of all votes"
    )
    approval_percentage: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of weighted approval"
    )
    evaluations: List[ProposalEvaluation] = Field(
        default_factory=list,
        description="List of all agent evaluations"
    )
    consensus_time: datetime = Field(
        default_factory=datetime.now,
        description="When consensus was reached"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the consensus process"
    )


class EthereumProposal(BaseModel):
    """Model representing an Ethereum protocol upgrade proposal (EIP)."""

    proposal_id: str = Field(..., description="Unique identifier for the proposal (e.g., EIP-1559)")
    title: str = Field(..., description="Title of the proposal")
    author: str = Field(..., description="Author(s) of the proposal")
    status: str = Field(..., description="Current status of the proposal")
    type: str = Field(..., description="Type of EIP (Core, Networking, Interface, etc.)")
    category: Optional[str] = Field(None, description="Category of EIP if applicable")
    created: datetime = Field(..., description="Creation date")
    description: str = Field(..., description="Short description of the proposal")
    specification: str = Field(..., description="Full specification text")
    code_changes: Optional[Dict[str, Any]] = Field(
        None, description="Code changes associated with the proposal"
    )
    requires: List[str] = Field(
        default_factory=list, 
        description="IDs of proposals this one depends on"
    )
    implementations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Implementations of the proposal in different clients"
    )
    tests: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Test cases for the proposal"
    ) 