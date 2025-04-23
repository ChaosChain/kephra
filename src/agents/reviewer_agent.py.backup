"""
Reviewer Agent for Kephra.

This agent is responsible for reviewing and evaluating Ethereum Improvement Proposals (EIPs).
It analyzes proposals for technical correctness, standards compliance, and overall quality.
"""

import logging
from typing import Any, Dict, List, Optional

from src.agents.base_agent import KephraAgent
from src.models.agent_models import AgentConfig, AgentType, DecisionType, ProposalEvaluation
from src.tools.eip_tools import EIPStandardsChecker

logger = logging.getLogger(__name__)


class ReviewerAgent(KephraAgent):
    """
    Agent specialized in reviewing and evaluating Ethereum Improvement Proposals.
    
    The reviewer examines proposals for technical correctness, adherence to EIP standards,
    implementation feasibility, and overall contribution to the Ethereum ecosystem.
    It provides detailed feedback and recommendations based on its evaluation.
    """
    
    def __init__(
        self,
        name: str,
        role: str = "Ethereum Protocol Reviewer",
        goal: str = "Rigorously evaluate proposals for technical correctness and standards compliance",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        reputation_score: float = 1.0,
        tools: Optional[List[Any]] = None,
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize a Reviewer Agent.
        
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
        # Initialize standard tools for reviewer if none provided
        if tools is None:
            tools = [
                EIPStandardsChecker(),
                # Add more specialized reviewing tools as needed
            ]
        
        super().__init__(
            name=name,
            role=role,
            goal=goal,
            agent_type=AgentType.REVIEWER,
            model=model,
            temperature=temperature,
            reputation_score=reputation_score,
            tools=tools,
            verbose=verbose,
        )
        
        # Reviewer-specific attributes
        self.review_criteria = kwargs.get("review_criteria", [
            "technical_correctness",
            "standards_compliance",
            "implementation_feasibility",
            "backward_compatibility",
            "forward_compatibility",
            "clarity",
            "contribution_value"
        ])
        
        self.review_count = 0
        
        logger.info(f"Initialized ReviewerAgent: {name} with {len(self.review_criteria)} review criteria")
    
    def process(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a proposal to review and evaluate it.
        
        Args:
            proposal_data: Proposal data to review
            
        Returns:
            Review results
        """
        logger.info(f"Reviewer {self.name} processing proposal: {proposal_data.get('proposal_id', 'Unknown')}")
        self.review_count += 1
        
        # Extract key elements from the proposal
        proposal_id = proposal_data.get("proposal_id", "Unknown")
        title = proposal_data.get("title", "")
        abstract = proposal_data.get("abstract", "")
        specification = proposal_data.get("specification", "")
        motivation = proposal_data.get("motivation", "")
        rationale = proposal_data.get("rationale", "")
        
        # Perform the review
        review_results = self._review_proposal(proposal_data)
        
        # Consolidate results into a comprehensive review
        review = {
            "proposal_id": proposal_id,
            "review_id": f"REV-{self.name}-{self.review_count}",
            "criteria_scores": review_results["criteria_scores"],
            "overall_score": review_results["overall_score"],
            "strengths": review_results["strengths"],
            "weaknesses": review_results["weaknesses"],
            "comments": review_results["comments"],
            "recommendation": self._generate_recommendation(review_results),
        }
        
        logger.info(f"Review completed for {proposal_id}: {review['recommendation']['decision']}")
        
        return review
    
    def evaluate_proposal(self, proposal_id: str, proposal_data: Dict[str, Any]) -> ProposalEvaluation:
        """
        Evaluate a proposal and return a formal evaluation based on review.
        
        Args:
            proposal_id: Unique identifier of the proposal
            proposal_data: The proposal data to evaluate
        
        Returns:
            A structured evaluation of the proposal
        """
        # Process the proposal to get review results
        review = self.process(proposal_data)
        
        # Extract recommendation
        recommendation = review["recommendation"]
        
        # Create a formal evaluation object
        evaluation = ProposalEvaluation(
            proposal_id=proposal_id,
            agent_id=self.name,
            agent_type=AgentType.REVIEWER,
            decision=recommendation["decision"],
            confidence=recommendation["confidence"],
            reasoning=recommendation["reasoning"],
            reputation_weight=self.reputation_score,
            metrics={
                "overall_score": review["overall_score"],
                "criteria_scores": review["criteria_scores"]
            }
        )
        
        return evaluation
    
    def _review_proposal(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review the proposal according to established criteria.
        
        Args:
            proposal_data: Proposal data to review
            
        Returns:
            Review results
        """
        # Use the actual tools to perform the review
        criteria_scores = {}
        issues = []
        
        # Get the raw content for the EIP
        raw_content = proposal_data.get("raw_content", "")
        proposal_id = proposal_data.get("proposal_id", "Unknown")
        
        # Use EIPStandardsChecker to check compliance
        standards_checker = next((tool for tool in self.tools if isinstance(tool, EIPStandardsChecker)), None)
        
        if standards_checker and raw_content:
            # Run the standards checker
            standards_results = standards_checker._run(raw_content, proposal_id)
            
            # Set standards_compliance score based on results
            is_compliant = standards_results.get("is_compliant", False)
            compliance_issues = standards_results.get("issues", [])
            
            # Add issues to our list
            issues.extend(compliance_issues)
            
            # Set standards compliance score
            if is_compliant:
                criteria_scores["standards_compliance"] = 1.0
            else:
                # Calculate score based on number and severity of issues
                high_issues = sum(1 for issue in compliance_issues if issue.get("severity") == "high")
                med_issues = sum(1 for issue in compliance_issues if issue.get("severity") == "medium")
                low_issues = sum(1 for issue in compliance_issues if issue.get("severity") == "low")
                
                # Penalty system: high issues have more weight
                penalty = (high_issues * 0.3) + (med_issues * 0.1) + (low_issues * 0.05)
                criteria_scores["standards_compliance"] = max(0.0, 1.0 - penalty)
            
            # Get client compatibility from MCP if available
            compatibility = standards_results.get("mcp_compatibility", {})
            if compatibility:
                supported_clients = sum(1 for client in compatibility.values() if client.get("compatible", False))
                total_clients = len(compatibility) or 1
                criteria_scores["backward_compatibility"] = min(1.0, supported_clients / total_clients)
        
        # For any criteria we haven't set with tools, simulate a reasonable score
        for criterion in self.review_criteria:
            if criterion not in criteria_scores:
                criteria_scores[criterion] = self._simulate_criterion_score(criterion, proposal_data)
        
        # Calculate overall score as weighted average
        weights = {
            "technical_correctness": 0.25,
            "standards_compliance": 0.2,
            "implementation_feasibility": 0.15,
            "backward_compatibility": 0.1,
            "forward_compatibility": 0.1,
            "clarity": 0.1,
            "contribution_value": 0.1
        }
        
        overall_score = sum(
            criteria_scores.get(criterion, 0) * weights.get(criterion, 0)
            for criterion in self.review_criteria
        ) / sum(weights.get(criterion, 0) for criterion in self.review_criteria)
        
        # Generate strengths and weaknesses
        strengths = self._identify_strengths(criteria_scores, proposal_data)
        weaknesses = self._identify_weaknesses(criteria_scores, proposal_data)
        
        # Generate detailed comments
        comments = self._generate_comments(criteria_scores, strengths, weaknesses, proposal_data)
        
        return {
            "criteria_scores": criteria_scores,
            "overall_score": overall_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "comments": comments
        }
    
    def _simulate_criterion_score(self, criterion: str, proposal_data: Dict[str, Any]) -> float:
        """
        Simulate a score for a specific review criterion.
        
        Args:
            criterion: The criterion to score
            proposal_data: The proposal data
            
        Returns:
            A score between 0.0 and 1.0
        """
        # This is a placeholder. In a real implementation, this would
        # use sophisticated analysis techniques specific to each criterion.
        
        # For demonstration, base scores on presence of key sections
        # and the length and quality of content
        
        # Check if required sections exist
        has_title = bool(proposal_data.get("title", ""))
        has_abstract = bool(proposal_data.get("abstract", ""))
        has_specification = bool(proposal_data.get("specification", ""))
        has_motivation = bool(proposal_data.get("motivation", ""))
        has_rationale = bool(proposal_data.get("rationale", ""))
        has_implementation = bool(proposal_data.get("implementation", ""))
        has_examples = bool(proposal_data.get("examples", ""))
        has_references = bool(proposal_data.get("references", ""))
        
        # Base score on completeness of proposal
        completeness = sum([
            has_title * 0.05,
            has_abstract * 0.1,
            has_specification * 0.25,
            has_motivation * 0.15,
            has_rationale * 0.15,
            has_implementation * 0.15,
            has_examples * 0.1,
            has_references * 0.05
        ])
        
        # Adjust score based on criterion
        if criterion == "technical_correctness":
            # Higher weight on specification and implementation
            base_score = 0.5 + (has_specification * 0.3 + has_implementation * 0.2)
            # In real implementation, would check actual technical correctness
        
        elif criterion == "standards_compliance":
            # Higher weight on format and structure
            base_score = completeness
            # In real implementation, would check against EIP standards
        
        elif criterion == "implementation_feasibility":
            # Higher weight on specification and examples
            base_score = 0.4 + (has_specification * 0.3 + has_examples * 0.3)
            # In real implementation, would assess technical feasibility
        
        elif criterion == "backward_compatibility":
            # Simulate compatibility assessment
            base_score = 0.7  # Assume mostly compatible
            # In real implementation, would check compatibility concerns
        
        elif criterion == "forward_compatibility":
            # Simulate compatibility assessment
            base_score = 0.6  # Assume reasonably forward-compatible
            # In real implementation, would assess future-proofing
        
        elif criterion == "clarity":
            # Higher weight on quality of writing
            base_score = 0.3 + completeness * 0.7
            # In real implementation, would assess readability and clarity
        
        elif criterion == "contribution_value":
            # Higher weight on motivation and rationale
            base_score = 0.2 + (has_motivation * 0.4 + has_rationale * 0.4)
            # In real implementation, would assess value to ecosystem
        
        else:
            # Default scoring
            base_score = completeness
        
        # Add some realistic variation
        import random
        variation = random.uniform(-0.1, 0.1)
        
        # Ensure score is within bounds
        final_score = max(0.0, min(1.0, base_score + variation))
        
        return final_score
    
    def _identify_strengths(self, criteria_scores: Dict[str, float], proposal_data: Dict[str, Any]) -> List[str]:
        """
        Identify strengths of the proposal based on criteria scores.
        
        Args:
            criteria_scores: Scores for each review criterion
            proposal_data: Proposal data
            
        Returns:
            List of strengths
        """
        # Use LLMs and MCP data for more accurate identification
        
        strengths = []
        
        # High technical correctness
        if criteria_scores.get("technical_correctness", 0) > 0.8:
            strengths.append("Technically sound approach")
        
        # High standards compliance
        if criteria_scores.get("standards_compliance", 0) > 0.8:
            strengths.append("Complies well with EIP standards and format requirements")
        
        # Check for client compatibility from MCP data if available
        compatibility = proposal_data.get("mcp_compatibility", {})
        if compatibility:
            client_support = sum(1 for client, data in compatibility.items() 
                              if isinstance(data, dict) and data.get("compatible", False))
            if client_support >= 3:  # If at least 3 clients support it
                strengths.append(f"Compatible with {client_support} major Ethereum clients")
        
        # Add fork-related strength if available from MCP
        consensus_info = proposal_data.get("consensus_info", {})
        if consensus_info and "fork" in consensus_info:
            strengths.append(f"Included in the {consensus_info.get('fork')} network upgrade")
        
        # High implementation feasibility
        if criteria_scores.get("implementation_feasibility", 0) > 0.7:
            strengths.append("Feasible implementation approach")
        
        # Good backward compatibility
        if criteria_scores.get("backward_compatibility", 0) > 0.7:
            strengths.append("Good backward compatibility")
        
        # Overall contribution value
        if criteria_scores.get("contribution_value", 0) > 0.8:
            strengths.append("Significant positive impact on the Ethereum ecosystem")
        
        # Clear writing
        if criteria_scores.get("clarity", 0) > 0.8:
            strengths.append("Clear and well-documented proposal")
        
        return strengths
    
    def _identify_weaknesses(self, criteria_scores: Dict[str, float], proposal_data: Dict[str, Any]) -> List[str]:
        """
        Identify weaknesses of the proposal based on criteria scores.
        
        Args:
            criteria_scores: Scores for each review criterion
            proposal_data: Proposal data
            
        Returns:
            List of weaknesses
        """
        # Use LLMs and MCP data for more accurate identification
        
        weaknesses = []
        
        # Low technical correctness
        if criteria_scores.get("technical_correctness", 0) < 0.5:
            weaknesses.append("Technical approach needs significant improvement")
        
        # Low standards compliance
        if criteria_scores.get("standards_compliance", 0) < 0.6:
            # Extract specific non-compliance issues
            if "issues" in proposal_data and proposal_data["issues"]:
                # Group by severity
                high_issues = [i["message"] for i in proposal_data["issues"] if i.get("severity") == "high"]
                if high_issues:
                    weaknesses.append(f"EIP format issues: {', '.join(high_issues)}")
                else:
                    weaknesses.append("Does not adequately comply with EIP standards")
            else:
                weaknesses.append("Does not adequately comply with EIP standards")
                
        # Low client compatibility (from MCP data)
        compatibility = proposal_data.get("mcp_compatibility", {})
        if compatibility:
            incompatible_clients = [client for client, data in compatibility.items() 
                                if isinstance(data, dict) and not data.get("compatible", False)]
            if incompatible_clients:
                weaknesses.append(f"Compatibility issues with clients: {', '.join(incompatible_clients)}")
        
        # Low implementation feasibility
        if criteria_scores.get("implementation_feasibility", 0) < 0.5:
            weaknesses.append("Implementation approach may be challenging")
        
        # Poor backward compatibility
        if criteria_scores.get("backward_compatibility", 0) < 0.5:
            weaknesses.append("Potential backward compatibility issues")
        
        # Low contribution value
        if criteria_scores.get("contribution_value", 0) < 0.5:
            weaknesses.append("Limited impact on the Ethereum ecosystem")
        
        # Unclear writing
        if criteria_scores.get("clarity", 0) < 0.6:
            weaknesses.append("Could benefit from clearer documentation")
        
        return weaknesses
    
    def _generate_comments(
        self, 
        criteria_scores: Dict[str, float], 
        strengths: List[str], 
        weaknesses: List[str],
        proposal_data: Dict[str, Any]
    ) -> str:
        """
        Generate detailed review comments.
        
        Args:
            criteria_scores: Scores for each criterion
            strengths: Identified strengths
            weaknesses: Identified weaknesses
            proposal_data: The proposal data
            
        Returns:
            Detailed review comments
        """
        # In a real implementation, this would generate more sophisticated
        # and contextual comments based on a deeper analysis of the proposal
        
        comments = []
        
        # Add introduction
        title = proposal_data.get("title", "this proposal")
        comments.append(f"This review evaluates {title} against established EIP criteria.")
        
        # Add strengths section if there are strengths
        if strengths:
            comments.append("\nStrengths:")
            for strength in strengths:
                comments.append(f"- {strength}")
        
        # Add weaknesses section if there are weaknesses
        if weaknesses:
            comments.append("\nAreas for improvement:")
            for weakness in weaknesses:
                comments.append(f"- {weakness}")
        
        # Add specific comments on criteria
        comments.append("\nDetailed assessment:")
        for criterion in self.review_criteria:
            score = criteria_scores.get(criterion, 0)
            formatted_criterion = criterion.replace("_", " ").title()
            comments.append(f"- {formatted_criterion}: {score:.2f}/1.00")
        
        # Add conclusion based on overall score
        overall_score = sum(criteria_scores.values()) / len(criteria_scores) if criteria_scores else 0
        if overall_score >= 0.8:
            comments.append("\nOverall, this is an excellent proposal that meets or exceeds expectations in most areas.")
        elif overall_score >= 0.6:
            comments.append("\nOverall, this is a solid proposal with some areas that could benefit from improvement.")
        elif overall_score >= 0.4:
            comments.append("\nOverall, this proposal shows promise but requires significant improvements before it can be recommended.")
        else:
            comments.append("\nOverall, this proposal has fundamental issues that need to be addressed before further consideration.")
        
        return "\n".join(comments)
    
    def _generate_recommendation(self, review_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a recommendation based on the review.
        
        Args:
            review_results: Review results
            
        Returns:
            Recommendation including decision, confidence, and reasoning
        """
        overall_score = review_results["overall_score"]
        strengths = review_results["strengths"]
        weaknesses = review_results["weaknesses"]
        
        # Determine decision based on overall score
        if overall_score >= 0.8:
            decision = DecisionType.APPROVE
            confidence = 0.8 + (overall_score - 0.8) * 2  # Scale from 0.8 to 1.0
            reasoning = "The proposal is of high quality and meets the necessary standards. " + \
                        f"It scored {overall_score:.2f} overall, with particular strengths in " + \
                        ", ".join(k.replace("_", " ") for k, v in review_results["criteria_scores"].items() if v >= 0.8)
        
        elif overall_score >= 0.6:
            decision = DecisionType.APPROVE
            confidence = 0.4 + (overall_score - 0.6) * 2  # Scale from 0.4 to 0.8
            reasoning = "The proposal is generally solid though not without flaws. " + \
                        f"It scored {overall_score:.2f} overall. " + \
                        f"With {len(strengths)} strengths and {len(weaknesses)} areas needing improvement."
        
        elif overall_score >= 0.4:
            if len(weaknesses) > len(strengths) * 2:
                decision = DecisionType.REJECT
                confidence = 0.4 + (0.6 - overall_score) * 2  # Scale from 0.4 to 0.8
                reasoning = "The proposal has too many significant issues to approve in its current form. " + \
                            f"It scored {overall_score:.2f} overall, with {len(weaknesses)} notable weaknesses."
            else:
                decision = DecisionType.ABSTAIN
                confidence = 0.5
                reasoning = "The proposal shows potential but needs substantial revisions before approval. " + \
                            f"It scored {overall_score:.2f} overall, with both strengths and significant weaknesses."
        
        else:
            decision = DecisionType.REJECT
            confidence = 0.7 + (0.4 - overall_score) * 0.75  # Scale from 0.7 to 1.0
            reasoning = "The proposal falls significantly short of the required standards. " + \
                        f"It scored only {overall_score:.2f} overall, with critical issues in " + \
                        ", ".join(k.replace("_", " ") for k, v in review_results["criteria_scores"].items() if v <= 0.3)
        
        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning
        }
    
    @classmethod
    def from_config(cls, config: AgentConfig) -> "ReviewerAgent":
        """
        Create a ReviewerAgent from a configuration object.
        
        Args:
            config: Agent configuration
            
        Returns:
            An initialized ReviewerAgent
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