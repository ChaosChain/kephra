"""
Consensus Agent for Kephra.
Aggregates evaluations from Reviewer and Simulator agents to decide on a proposal.
"""

import logging
from typing import Any, Dict

from src.agents.base_agent import KephraAgent
from src.models.agent_models import AgentType

logger = logging.getLogger(__name__)

class ConsensusAgent(KephraAgent):
    """
    Agent that aggregates evaluation decisions from multiple agents
    and outputs a final accept/reject decision with basic confidence.
    """
    def __init__(
        self,
        name: str = "Consensus Agent",
        role: str = "Aggregate peer evaluations and determine consensus",
        goal: str = "Reach a final decision on EIP proposals based on weighted votes",
        model: str = None,
        temperature: float = None,
        verbose: bool = False
    ):
        super().__init__(
            name=name,
            role=role,
            goal=goal,
            agent_type=AgentType.CONSENSUS,
            model=model or None,
            temperature=temperature or 0.0,
            verbose=verbose
        )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        input_data: {
            'proposal_id': str,
            'evaluations': { agent_id: { 'decision': 'accept'|'reject', 'confidence': float, ... }, ... }
        }
        returns: { 'proposal_id': str, 'final_decision': 'accept'|'reject', 'confidence': float }
        """
        proposal_id = input_data.get('proposal_id')
        evaluations = input_data.get('evaluations', {})

        # Count weighted votes
        total_weight = 0.0
        accept_weight = 0.0
        for eval_data in evaluations.values():
            conf = float(eval_data.get('confidence', 0.0))
            total_weight += conf
            if eval_data.get('decision') == 'accept':
                accept_weight += conf

        # Determine final decision
        if total_weight > 0:
            ratio = accept_weight / total_weight
        else:
            ratio = 0.0

        final_decision = 'accept' if ratio >= 0.5 else 'reject'
        final_confidence = round(ratio * 100, 2)

        logger.info(f"Consensus for {proposal_id}: {final_decision} ({final_confidence}% accept)")
        return {
            'proposal_id': proposal_id,
            'final_decision': final_decision,
            'confidence': final_confidence
        } 