"""
MCP-Enhanced Reviewer Agent for Kephra.

This agent extends the base reviewer agent with MCP capabilities for more
advanced analysis of Ethereum Improvement Proposals (EIPs).
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

from src.agents.reviewer_agent import ReviewerAgent
from src.models.agent_models import AgentConfig, AgentType, DecisionType, ProposalEvaluation

logger = logging.getLogger(__name__)


class MCPEnhancedReviewerAgent(ReviewerAgent):
    """
    Agent specialized in reviewing EIPs with enhanced capabilities via MCP.
    
    This agent extends the base ReviewerAgent with access to MCP servers
    that provide tools for EIP validation, code analysis, and compatibility checking.
    """
    
    def __init__(
        self,
        name: str,
        role: str = "Enhanced Ethereum Protocol Reviewer",
        goal: str = "Thoroughly evaluate EIPs using advanced tools and real-time blockchain data",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        reputation_score: float = 1.0,
        tools: Optional[List[Any]] = None,
        verbose: bool = False,
        mcp_tools: Optional[List[str]] = None,
        mcp_resources: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize an MCP-Enhanced Reviewer Agent.
        
        Args:
            name: The agent's name
            role: The agent's role description
            goal: The agent's goal
            model: The LLM model to use
            temperature: Temperature setting for the model
            reputation_score: Initial reputation score
            tools: List of tools the agent can use
            verbose: Whether to log detailed information
            mcp_tools: List of MCP tool names the agent should have access to
            mcp_resources: List of MCP resource URIs the agent should have access to
            kwargs: Additional keyword arguments
        """
        # Default MCP tools if none provided
        if mcp_tools is None:
            mcp_tools = [
                "search_eips",
                "get_eip_content",
                "check_eip_compatibility",
                "validate_solidity_code", 
                "analyze_gas_efficiency"
            ]
        
        # Default MCP resources if none provided
        if mcp_resources is None:
            mcp_resources = []  # Will be populated with available EIP resources
        
        super().__init__(
            name=name,
            role=role,
            goal=goal,
            model=model,
            temperature=temperature,
            reputation_score=reputation_score,
            tools=tools,
            verbose=verbose,
            mcp_tools=mcp_tools,
            mcp_resources=mcp_resources,
            **kwargs
        )
        
        # Additional attributes specific to MCP-enhanced reviewer
        self.eip_compatibility_cache = {}
        self.related_eips_cache = {}
    
    async def process_async(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a proposal asynchronously with MCP-enhanced analysis.
        
        Args:
            proposal_data: Proposal data to review
            
        Returns:
            Enhanced review results
        """
        logger.info(f"MCP-Enhanced Reviewer {self.name} processing proposal: {proposal_data.get('proposal_id', 'Unknown')}")
        self.review_count += 1
        
        # Ensure MCP is initialized
        await self.ensure_mcp_initialized()
        
        # Extract key elements from the proposal
        proposal_id = proposal_data.get("proposal_id", "Unknown")
        
        # Extract EIP number
        eip_number = None
        if proposal_id.startswith("EIP-"):
            eip_number = proposal_id.replace("EIP-", "")
        
        # Additional MCP-enhanced analysis
        enhanced_data = await self._mcp_enhanced_analysis(proposal_data)
        
        # Merge enhanced data with proposal data for standard review
        enhanced_proposal_data = {**proposal_data, **enhanced_data}
        
        # Use the regular processing method with enhanced data
        review = super().process(enhanced_proposal_data)
        
        # Add MCP-specific analysis results to the review
        review["mcp_enhanced_analysis"] = {
            "compatibility": enhanced_data.get("compatibility", {}),
            "related_eips": enhanced_data.get("related_eips", []),
            "code_validation": enhanced_data.get("code_validation", {}),
            "gas_analysis": enhanced_data.get("gas_analysis", {})
        }
        
        logger.info(f"MCP-Enhanced review completed for {proposal_id}")
        
        return review
    
    async def evaluate_proposal_async(self, proposal_id: str, proposal_data: Dict[str, Any]) -> ProposalEvaluation:
        """
        Evaluate a proposal asynchronously with MCP-enhanced capabilities.
        
        Args:
            proposal_id: Unique identifier of the proposal
            proposal_data: The proposal data to evaluate
            
        Returns:
            A structured evaluation of the proposal
        """
        # Process the proposal with MCP enhancements
        review = await self.process_async(proposal_data)
        
        # Extract recommendation
        recommendation = review["recommendation"]
        
        # Create a formal evaluation object with additional MCP data
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
                "criteria_scores": review["criteria_scores"],
                "mcp_enhanced_analysis": review.get("mcp_enhanced_analysis", {})
            }
        )
        
        return evaluation
    
    async def _mcp_enhanced_analysis(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform MCP-enhanced analysis on the proposal.
        
        Args:
            proposal_data: Proposal data to analyze
            
        Returns:
            Enhanced analysis results
        """
        results = {}
        
        # Extract key data
        proposal_id = proposal_data.get("proposal_id", "Unknown")
        specification = proposal_data.get("specification", "")
        
        # Extract EIP number
        eip_number = None
        if proposal_id.startswith("EIP-"):
            eip_number = proposal_id.replace("EIP-", "")
        
        # 1. Check EIP compatibility if EIP number is available
        if eip_number:
            try:
                compatibility = await self.call_mcp_tool("check_eip_compatibility", {"eip_number": eip_number})
                results["compatibility"] = compatibility
                
                # Cache the results
                self.eip_compatibility_cache[eip_number] = compatibility
            except Exception as e:
                logger.error(f"Error checking EIP compatibility: {e}")
                results["compatibility"] = {"status": "error", "message": str(e)}
        
        # 2. Search for related EIPs
        try:
            # Extract meaningful keywords from the proposal
            keywords = self._extract_keywords(proposal_data)
            
            related_eips = []
            for keyword in keywords[:3]:  # Limit to top 3 keywords to avoid too many requests
                search_results = await self.call_mcp_tool("search_eips", {"query": keyword})
                if search_results.get("status") == "success" and isinstance(search_results.get("data", []), list):
                    related_eips.extend(search_results["data"])
            
            # Remove duplicates and the current EIP
            seen_eips = set()
            filtered_eips = []
            for eip in related_eips:
                eip_id = eip.get("id", "")
                if eip_id and eip_id != proposal_id and eip_id not in seen_eips:
                    seen_eips.add(eip_id)
                    filtered_eips.append(eip)
            
            results["related_eips"] = filtered_eips[:5]  # Limit to top 5 related EIPs
            
            # Cache the results
            self.related_eips_cache[proposal_id] = filtered_eips
        except Exception as e:
            logger.error(f"Error searching for related EIPs: {e}")
            results["related_eips"] = []
        
        # 3. Validate code samples if present
        code_samples = self._extract_code_samples(proposal_data)
        code_validation_results = {}
        gas_analysis_results = {}
        
        for i, code in enumerate(code_samples):
            if "solidity" in code.get("language", "").lower():
                try:
                    # Validate the code
                    validation = await self.call_mcp_tool("validate_solidity_code", {"code": code["code"]})
                    code_validation_results[f"sample_{i+1}"] = validation
                    
                    # Analyze gas efficiency
                    gas_analysis = await self.call_mcp_tool("analyze_gas_efficiency", {"code": code["code"]})
                    gas_analysis_results[f"sample_{i+1}"] = gas_analysis
                except Exception as e:
                    logger.error(f"Error validating code sample {i+1}: {e}")
        
        results["code_validation"] = code_validation_results
        results["gas_analysis"] = gas_analysis_results
        
        return results
    
    def _extract_keywords(self, proposal_data: Dict[str, Any]) -> List[str]:
        """
        Extract meaningful keywords from the proposal for searching related EIPs.
        
        Args:
            proposal_data: Proposal data
            
        Returns:
            List of keywords
        """
        keywords = []
        
        # Add title words
        title = proposal_data.get("title", "")
        if title:
            keywords.extend([word.lower() for word in title.split() if len(word) > 3])
        
        # Add type and category
        eip_type = proposal_data.get("type", "")
        if eip_type:
            keywords.append(eip_type.lower())
        
        category = proposal_data.get("category", "")
        if category:
            keywords.append(category.lower())
        
        # Extract key terms from abstract/description
        description = proposal_data.get("description", "")
        if description:
            # Simple keyword extraction (just for demonstration)
            potential_keywords = [word.lower() for word in description.split() 
                               if len(word) > 5 and word.lower() not in ["ethereum", "proposal", "standard"]]
            keywords.extend(potential_keywords[:5])  # Add up to 5 keywords from description
        
        # Remove duplicates and return
        return list(dict.fromkeys(keywords))
    
    def _extract_code_samples(self, proposal_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract code samples from the proposal for validation.
        
        Args:
            proposal_data: Proposal data
            
        Returns:
            List of code samples with language information
        """
        code_samples = []
        
        # First, check if there are already parsed code examples
        if "code_examples" in proposal_data and isinstance(proposal_data["code_examples"], list):
            return proposal_data["code_examples"]
        
        # Otherwise, extract from specification or other content
        specification = proposal_data.get("specification", "")
        if specification:
            import re
            # Find code blocks with language tags (```language\ncode```)
            matches = re.findall(r'```(\w*)\n(.*?)```', specification, re.DOTALL)
            for lang, code in matches:
                if code.strip():  # Only add non-empty code blocks
                    code_samples.append({
                        "language": lang.strip() or "unknown",
                        "code": code.strip()
                    })
        
        return code_samples
    
    def _simulate_criterion_score(self, criterion: str, proposal_data: Dict[str, Any]) -> float:
        """
        Simulate a score for a specific criterion with MCP-enhanced data.
        
        This overrides the base method to incorporate MCP analysis results.
        
        Args:
            criterion: Criterion to score
            proposal_data: Enhanced proposal data with MCP results
            
        Returns:
            Score for the criterion (0.0 to 1.0)
        """
        # Get MCP analysis results
        mcp_compatibility = proposal_data.get("compatibility", {})
        mcp_code_validation = proposal_data.get("code_validation", {})
        mcp_gas_analysis = proposal_data.get("gas_analysis", {})
        
        # Use the parent's implementation as a base score
        base_score = super()._simulate_criterion_score(criterion, proposal_data)
        
        # Enhance scores with MCP data
        if criterion == "technical_correctness":
            if mcp_code_validation:
                # Average validation results for multiple code samples
                valid_samples = 0
                valid_count = 0
                for sample_key, validation in mcp_code_validation.items():
                    if validation.get("status") == "success":
                        valid_samples += 1 if validation.get("valid", False) else 0
                        valid_count += 1
                
                if valid_count > 0:
                    # Adjust the base score based on code validation
                    validation_score = valid_samples / valid_count
                    # Blend with base score (60% validation, 40% base)
                    return (validation_score * 0.6) + (base_score * 0.4)
        
        elif criterion == "implementation_feasibility":
            if mcp_gas_analysis:
                # Check if gas analysis shows reasonable efficiency
                high_gas_efficiency = True
                for sample_key, analysis in mcp_gas_analysis.items():
                    if analysis.get("status") == "success":
                        gas_data = analysis.get("gas_analysis", {})
                        if gas_data.get("percentage_savings", 0) > 30:
                            # If potential gas savings are high, the implementation isn't optimal
                            high_gas_efficiency = False
                            break
                
                # Adjust score based on gas efficiency
                if high_gas_efficiency:
                    return min(base_score + 0.2, 1.0)  # Boost score if gas efficient
                else:
                    return max(base_score - 0.1, 0.0)  # Slightly penalize if not gas efficient
        
        elif criterion == "backward_compatibility":
            if mcp_compatibility and mcp_compatibility.get("status") == "success":
                consensus_info = mcp_compatibility.get("consensus_info", {})
                if consensus_info:
                    # Check if it's a hard fork that might break compatibility
                    is_hard_fork = consensus_info.get("layer") == "both"
                    if is_hard_fork:
                        return max(base_score - 0.15, 0.0)  # Reduce score for hard forks
        
        # Return the base score if no MCP-specific adjustments were made
        return base_score
    
    def _identify_strengths(self, criteria_scores: Dict[str, float], proposal_data: Dict[str, Any]) -> List[str]:
        """
        Identify strengths of the proposal with MCP-enhanced analysis.
        
        Args:
            criteria_scores: Scores for each criterion
            proposal_data: Enhanced proposal data with MCP results
            
        Returns:
            List of identified strengths
        """
        # Get base strengths from parent method
        strengths = super()._identify_strengths(criteria_scores, proposal_data)
        
        # Add MCP-specific strengths
        mcp_compatibility = proposal_data.get("compatibility", {})
        
        if mcp_compatibility and mcp_compatibility.get("status") == "success":
            # Check if all major clients support it
            compatibility = mcp_compatibility.get("compatibility", {})
            if compatibility and all(client_data.get("compatible", False) for client_data in compatibility.values()):
                strengths.append("All major Ethereum clients support this EIP, ensuring wide adoption")
        
        # Check code validation results
        mcp_code_validation = proposal_data.get("code_validation", {})
        if mcp_code_validation:
            valid_samples = all(
                validation.get("valid", False) 
                for validation in mcp_code_validation.values() 
                if validation.get("status") == "success"
            )
            if valid_samples:
                strengths.append("Code samples are technically sound with no severe security issues")
        
        # Check gas analysis results
        mcp_gas_analysis = proposal_data.get("gas_analysis", {})
        if mcp_gas_analysis:
            gas_efficient = True
            for analysis in mcp_gas_analysis.values():
                if analysis.get("status") == "success":
                    # Consider inefficient if more than 20% potential savings
                    if analysis.get("gas_analysis", {}).get("percentage_savings", 0) > 20:
                        gas_efficient = False
                        break
            
            if gas_efficient:
                strengths.append("Implementation appears gas efficient, with limited optimization potential")
        
        return strengths
    
    def _identify_weaknesses(self, criteria_scores: Dict[str, float], proposal_data: Dict[str, Any]) -> List[str]:
        """
        Identify weaknesses of the proposal with MCP-enhanced analysis.
        
        Args:
            criteria_scores: Scores for each criterion
            proposal_data: Enhanced proposal data with MCP results
            
        Returns:
            List of identified weaknesses
        """
        # Get base weaknesses from parent method
        weaknesses = super()._identify_weaknesses(criteria_scores, proposal_data)
        
        # Add MCP-specific weaknesses
        mcp_compatibility = proposal_data.get("compatibility", {})
        
        if mcp_compatibility and mcp_compatibility.get("status") == "success":
            # Check if any major clients don't support it
            compatibility = mcp_compatibility.get("compatibility", {})
            incompatible_clients = [
                client for client, client_data in compatibility.items() 
                if not client_data.get("compatible", False)
            ]
            if incompatible_clients:
                clients_str = ", ".join(incompatible_clients)
                weaknesses.append(f"Lacks support in some Ethereum clients ({clients_str}), which could affect adoption")
        
        # Check code validation results
        mcp_code_validation = proposal_data.get("code_validation", {})
        if mcp_code_validation:
            issues = []
            for sample_key, validation in mcp_code_validation.items():
                if validation.get("status") == "success":
                    issues.extend(validation.get("issues", []))
            
            high_severity_issues = [issue for issue in issues if issue.get("severity") == "high"]
            if high_severity_issues:
                weaknesses.append(f"Code contains {len(high_severity_issues)} high-severity security issues that must be addressed")
        
        # Check gas analysis results
        mcp_gas_analysis = proposal_data.get("gas_analysis", {})
        if mcp_gas_analysis:
            for sample_key, analysis in mcp_gas_analysis.values():
                if analysis.get("status") == "success":
                    gas_data = analysis.get("gas_analysis", {})
                    if gas_data.get("percentage_savings", 0) > 30:
                        weaknesses.append("Implementation is not gas efficient, with significant optimization potential (>30% savings possible)")
                        break
        
        return weaknesses
    
    @classmethod
    def from_config(cls, config: AgentConfig) -> "MCPEnhancedReviewerAgent":
        """
        Create an MCPEnhancedReviewerAgent from a configuration object.
        
        Args:
            config: Agent configuration
            
        Returns:
            An initialized MCPEnhancedReviewerAgent
        """
        return cls(
            name=config.name,
            role=config.role,
            goal=config.goal,
            model=config.model,
            temperature=config.temperature,
            reputation_score=config.reputation_score,
            verbose=config.verbose,
            mcp_tools=config.additional_config.get("mcp_tools"),
            mcp_resources=config.additional_config.get("mcp_resources"),
            **config.additional_config
        ) 