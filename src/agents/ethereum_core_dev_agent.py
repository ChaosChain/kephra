"""
Ethereum Core Developer Agent for Kephra.

This agent specializes in blockchain protocol development, EIP creation, 
review, and consensus building. It can analyze protocol changes, review code, 
and provide gas optimizations.
"""

import logging
import json
from typing import Any, Dict, List, Optional, Union

from src.agents.base_agent import KephraAgent
from src.models.agent_models import AgentConfig, AgentType, ProposalEvaluation, DecisionType
from src.tools.ethereum_tools import GasAnalyzer, EthereumCompatibilityChecker
from src.tools.eip_tools import EIPStandardsChecker

logger = logging.getLogger(__name__)

class EthereumCoreDevAgent(KephraAgent):
    """
    Agent that emulates the behavior of an Ethereum Core Developer.
    
    This agent can:
    - Author high-quality EIPs based on community issues
    - Review and improve protocol suggestions
    - Analyze gas and performance implications
    - Provide protocol expertise on a technical question
    
    It's designed to facilitate real protocol development workflows and
    can be adapted to work with L2s and DAOs by adjusting its parameters.
    """
    
    def __init__(
        self,
        name: str,
        role: str = "Ethereum Core Protocol Developer",
        goal: str = "Improve Ethereum's scalability, security, and functionality through protocol improvements",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        expertise_areas: Optional[List[str]] = None,
        is_champion: bool = False, 
        chain_id: int = 1,  # Ethereum Mainnet by default
        consensus_rules: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Any]] = None,
        verbose: bool = False,
        mcp_tools: Optional[List[str]] = None,
        mcp_resources: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize an Ethereum Core Developer Agent.
        
        Args:
            name: The agent's name
            role: The agent's role description
            goal: The agent's goal
            model: The LLM model to use
            temperature: Temperature setting for the model
            expertise_areas: Areas of expertise (e.g., consensus, EVM, p2p, state, etc.)
            is_champion: Whether this agent is an EIP champion (can formally propose)
            chain_id: ID of the chain this developer specializes in (1 for Ethereum)
            consensus_rules: Rules this agent follows when evaluating proposals
            tools: List of tools the agent can use
            verbose: Whether to log detailed information
            mcp_tools: List of MCP tool names this agent can use
            mcp_resources: List of MCP resource URIs this agent can access
            kwargs: Additional keyword arguments
        """
        # Initialize standard tools for core dev if none provided
        if tools is None:
            tools = [
                GasAnalyzer(),
                EthereumCompatibilityChecker(),
                EIPStandardsChecker(),
            ]
        
        # Initialize standard MCP tools if none provided
        if mcp_tools is None:
            mcp_tools = [
                "code_analysis",
                "solidity_validation", 
                "evm_bytecode_analysis",
                "eip_metadata",
                "github_issues"
            ]
        
        # Initialize standard MCP resources if none provided
        if mcp_resources is None:
            mcp_resources = [
                "eip:1559",   # Fee market
                "eip:1167",   # Minimal proxy contract
                "eip:721",    # NFT standard
                "eip:20",     # Token standard
            ]
        
        super().__init__(
            name=name,
            role=role,
            goal=goal,
            agent_type=AgentType.PROPOSER,  # Core devs can propose new protocol changes
            model=model,
            temperature=temperature,
            tools=tools,
            verbose=verbose,
            mcp_tools=mcp_tools,
            mcp_resources=mcp_resources,
        )
        
        # Core dev specific attributes
        self.expertise_areas = expertise_areas or ["consensus", "evm", "networking"]
        self.is_champion = is_champion
        self.chain_id = chain_id
        self.consensus_rules = consensus_rules or {
            "backward_compatible": 0.8,  # Weight for backward compatibility
            "security": 0.9,            # Weight for security considerations
            "efficiency": 0.7,          # Weight for efficiency improvements
            "complexity": 0.5,          # Weight for added complexity (lower is better)
            "use_case": 0.6,            # Weight for real-world use cases
        }
        
        # Track EIPs this agent has authored or championed
        self.authored_eips = []
        self.championed_eips = []
        
        # Add any additional configuration
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        logger.info(f"Initialized EthereumCoreDevAgent: {name} with expertise in {', '.join(self.expertise_areas)}")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an input and provide a protocol developer response.
        
        Depending on the action specified, this can:
        - Create a new EIP from a GitHub issue
        - Review an existing EIP or protocol change
        - Analyze gas and performance implications
        - Provide protocol expertise on a technical question
        
        Args:
            input_data: Dictionary with action type and relevant data
            
        Returns:
            Response data specific to the requested action
        """
        action = input_data.get("action", "review")
        
        if action == "create_eip":
            return self._create_eip(input_data)
        elif action == "review_eip":
            return self._review_eip(input_data)
        elif action == "analyze_gas":
            return self._analyze_gas(input_data)
        elif action == "check_compatibility":
            return self._check_compatibility(input_data)
        elif action == "provide_expertise":
            return self._provide_expertise(input_data)
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}. Supported actions are: create_eip, review_eip, analyze_gas, check_compatibility, provide_expertise"
            }
    
    def _create_eip(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new EIP from a GitHub issue or other input."""
        issue_data = input_data.get("issue_data", {})
        
        # Generate EIP details based on expertise
        eip_title = issue_data.get("title", "Untitled EIP")
        eip_abstract = self._generate_abstract(issue_data)
        eip_motivation = self._generate_motivation(issue_data)
        eip_specification = self._generate_specification(issue_data)
        eip_rationale = self._generate_rationale(issue_data)
        eip_implementation = self._generate_implementation(issue_data)
        
        # Determine the appropriate EIP type and category
        eip_type, eip_category = self._determine_eip_type_and_category(issue_data)
        
        # Prepare EIP document
        eip_data = {
            "title": eip_title,
            "author": self.name,
            "status": "Draft",
            "type": eip_type,
            "category": eip_category,
            "abstract": eip_abstract,
            "motivation": eip_motivation,
            "specification": eip_specification,
            "rationale": eip_rationale,
            "implementation": eip_implementation,
            "requires": self._determine_dependencies(issue_data),
            "chain_id": self.chain_id
        }
        
        # Add to authored EIPs
        self.authored_eips.append(eip_title)
        
        return {
            "status": "success",
            "eip_data": eip_data,
            "author": self.name,
            "feedback": "EIP created based on core developer expertise"
        }
    
    def _review_eip(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Review an existing EIP with core developer perspective."""
        eip_data = input_data.get("eip_data", {})
        
        # Apply core dev expertise to evaluate the proposal
        technical_score = self._evaluate_technical_correctness(eip_data)
        security_score = self._evaluate_security_implications(eip_data)
        compatibility_score = self._evaluate_compatibility(eip_data)
        efficiency_score = self._evaluate_efficiency(eip_data)
        complexity_score = self._evaluate_complexity(eip_data)
        use_case_score = self._evaluate_use_case(eip_data)
        
        # Calculate weighted score based on core dev consensus rules
        weighted_score = (
            technical_score * 1.0 +  # Base weight is 1.0
            security_score * self.consensus_rules["security"] +
            compatibility_score * self.consensus_rules["backward_compatible"] +
            efficiency_score * self.consensus_rules["efficiency"] +
            (1 - complexity_score) * self.consensus_rules["complexity"] +  # Lower complexity is better
            use_case_score * self.consensus_rules["use_case"]
        ) / (1.0 + sum(self.consensus_rules.values()) - self.consensus_rules["complexity"])  # Normalize
        
        # Generate strengths and weaknesses
        strengths = self._identify_strengths(eip_data, {
            "technical_correctness": technical_score,
            "security": security_score,
            "compatibility": compatibility_score,
            "efficiency": efficiency_score,
            "complexity": complexity_score,
            "use_case": use_case_score
        })
        
        weaknesses = self._identify_weaknesses(eip_data, {
            "technical_correctness": technical_score,
            "security": security_score,
            "compatibility": compatibility_score,
            "efficiency": efficiency_score,
            "complexity": complexity_score,
            "use_case": use_case_score
        })
        
        # Determine decision based on score and expertise
        decision, confidence, reasoning = self._make_decision(weighted_score, strengths, weaknesses)
        
        return {
            "status": "success",
            "eip_id": input_data.get("eip_id", "Unknown"),
            "scores": {
                "technical_correctness": technical_score,
                "security": security_score,
                "compatibility": compatibility_score,
                "efficiency": efficiency_score,
                "complexity": complexity_score,
                "use_case": use_case_score,
                "weighted": weighted_score
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "suggested_improvements": self._suggest_improvements(eip_data, weaknesses)
        }
    
    def _analyze_gas(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze gas and performance implications of code or EIP."""
        code = input_data.get("code", "")
        eip_data = input_data.get("eip_data", {})
        
        # Use GasAnalyzer tool
        gas_analyzer = next((tool for tool in self.tools if isinstance(tool, GasAnalyzer)), None)
        
        if gas_analyzer and code:
            return gas_analyzer._run(code)
        
        # If no code provided but EIP data is available, analyze based on EIP
        if eip_data:
            specification = eip_data.get("specification", "")
            abstract = eip_data.get("abstract", "")
            
            # Perform conceptual gas analysis based on description
            gas_impact, optimization_suggestions = self._analyze_gas_conceptually(
                specification + "\n" + abstract
            )
            
            return {
                "status": "success",
                "gas_impact": gas_impact,
                "optimization_suggestions": optimization_suggestions
            }
        
        return {
            "status": "error",
            "message": "No code or EIP data provided for gas analysis"
        }
    
    def _check_compatibility(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check compatibility with Ethereum clients or standards."""
        code = input_data.get("code", "")
        eip_data = input_data.get("eip_data", {})
        
        # Use EthereumCompatibilityChecker tool
        compatibility_checker = next(
            (tool for tool in self.tools if isinstance(tool, EthereumCompatibilityChecker)), None
        )
        
        if compatibility_checker:
            return compatibility_checker._run(code or json.dumps(eip_data))
        
        # If no tool available, perform conceptual compatibility analysis
        return self._analyze_compatibility_conceptually(eip_data)
    
    def _provide_expertise(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide protocol expertise on a technical question."""
        question = input_data.get("question", "")
        
        # Generate response based on expertise areas
        relevant_expertise = []
        for area in self.expertise_areas:
            if area.lower() in question.lower():
                relevant_expertise.append(area)
        
        response = self._generate_expert_response(question, relevant_expertise)
        
        return {
            "status": "success",
            "question": question,
            "response": response,
            "relevant_expertise": relevant_expertise
        }
    
    # Helper methods for EIP creation
    
    def _generate_abstract(self, issue_data: Dict[str, Any]) -> str:
        """Generate an abstract for a new EIP."""
        title = issue_data.get("title", "")
        body = issue_data.get("body", "")
        
        # For now, a placeholder implementation
        # In practice, this would use LLM to generate high-quality abstracts
        return f"This EIP proposes a solution to {title.lower()}. " + \
               f"It aims to address the issues described in the GitHub issue " + \
               f"while maintaining backward compatibility and security."
    
    def _generate_motivation(self, issue_data: Dict[str, Any]) -> str:
        """Generate the motivation section for a new EIP."""
        # Placeholder implementation
        return "The motivation for this proposal stems from the need to address " + \
               "limitations in the current implementation. These changes will " + \
               "improve user experience, security, and efficiency."
    
    def _generate_specification(self, issue_data: Dict[str, Any]) -> str:
        """Generate the specification section for a new EIP."""
        # Placeholder implementation
        return "The technical specification for the proposed changes includes " + \
               "detailed implementation guidance, interface definitions, and " + \
               "necessary algorithms."
    
    def _generate_rationale(self, issue_data: Dict[str, Any]) -> str:
        """Generate the rationale section for a new EIP."""
        # Placeholder implementation
        return "This approach was selected after considering alternatives. " + \
               "It provides the best balance of compatibility, performance, " + \
               "and implementation complexity."
    
    def _generate_implementation(self, issue_data: Dict[str, Any]) -> str:
        """Generate the implementation section for a new EIP."""
        # Placeholder implementation
        return "A reference implementation will be provided as this proposal " + \
               "moves through the standardization process."
    
    def _determine_eip_type_and_category(self, issue_data: Dict[str, Any]) -> tuple:
        """Determine the appropriate EIP type and category."""
        title = issue_data.get("title", "").lower()
        body = issue_data.get("body", "").lower()
        
        # Simple heuristic, in practice would use more sophisticated analysis
        if "standard" in title or "interface" in title or "token" in title:
            return "Standards Track", "ERC"
        elif "consensus" in title or "fork" in title or "protocol" in title:
            return "Standards Track", "Core"
        elif "networking" in title or "devp2p" in title:
            return "Standards Track", "Networking"
        elif "meta" in title or "process" in title:
            return "Meta", "Process"
        else:
            return "Standards Track", "Core"  # Default
    
    def _determine_dependencies(self, issue_data: Dict[str, Any]) -> List[str]:
        """Determine EIP dependencies based on issue data."""
        # Placeholder implementation
        # In practice, would analyze issue content to find related EIPs
        return []
    
    # Helper methods for EIP review
    
    def _evaluate_technical_correctness(self, eip_data: Dict[str, Any]) -> float:
        """Evaluate the technical correctness of an EIP."""
        # Placeholder implementation
        # In practice, would perform detailed technical analysis
        return 0.85
    
    def _evaluate_security_implications(self, eip_data: Dict[str, Any]) -> float:
        """Evaluate security implications of an EIP."""
        # Placeholder implementation
        return 0.75
    
    def _evaluate_compatibility(self, eip_data: Dict[str, Any]) -> float:
        """Evaluate backward compatibility of an EIP."""
        # Placeholder implementation
        return 0.8
    
    def _evaluate_efficiency(self, eip_data: Dict[str, Any]) -> float:
        """Evaluate efficiency improvements of an EIP."""
        # Placeholder implementation
        return 0.7
    
    def _evaluate_complexity(self, eip_data: Dict[str, Any]) -> float:
        """Evaluate added complexity of an EIP. Higher is more complex."""
        # Placeholder implementation
        return 0.4
    
    def _evaluate_use_case(self, eip_data: Dict[str, Any]) -> float:
        """Evaluate real-world use cases for an EIP."""
        # Placeholder implementation
        return 0.65
    
    def _identify_strengths(self, eip_data: Dict[str, Any], scores: Dict[str, float]) -> List[str]:
        """Identify strengths of the EIP based on scores."""
        strengths = []
        
        if scores.get("technical_correctness", 0) > 0.7:
            strengths.append("Technically sound approach")
        
        if scores.get("security", 0) > 0.7:
            strengths.append("Good security considerations")
        
        if scores.get("compatibility", 0) > 0.7:
            strengths.append("Maintains backward compatibility")
        
        if scores.get("efficiency", 0) > 0.7:
            strengths.append("Provides efficiency improvements")
        
        if scores.get("complexity", 0) < 0.5:
            strengths.append("Manageable complexity")
        
        if scores.get("use_case", 0) > 0.7:
            strengths.append("Strong real-world use cases")
        
        return strengths
    
    def _identify_weaknesses(self, eip_data: Dict[str, Any], scores: Dict[str, float]) -> List[str]:
        """Identify weaknesses of the EIP based on scores."""
        weaknesses = []
        
        if scores.get("technical_correctness", 1) < 0.6:
            weaknesses.append("Technical approach needs improvement")
        
        if scores.get("security", 1) < 0.6:
            weaknesses.append("Security concerns need to be addressed")
        
        if scores.get("compatibility", 1) < 0.6:
            weaknesses.append("Backward compatibility issues")
        
        if scores.get("efficiency", 1) < 0.6:
            weaknesses.append("Efficiency could be improved")
        
        if scores.get("complexity", 0) > 0.7:
            weaknesses.append("Overly complex implementation")
        
        if scores.get("use_case", 1) < 0.6:
            weaknesses.append("Use case needs stronger justification")
        
        return weaknesses
    
    def _make_decision(self, score: float, strengths: List[str], weaknesses: List[str]) -> tuple:
        """Make a decision based on score, strengths, and weaknesses."""
        if score >= 0.8:
            return (
                DecisionType.APPROVE,
                0.9,
                "The proposal is technically sound and aligns with protocol goals."
            )
        elif score >= 0.6:
            return (
                DecisionType.APPROVE,
                0.7,
                "The proposal is generally solid though improvements could be made."
            )
        elif score >= 0.4:
            # Consider the balance of strengths vs weaknesses
            if len(weaknesses) > len(strengths):
                return (
                    DecisionType.REJECT,
                    0.6,
                    "The proposal has significant weaknesses that should be addressed."
                )
            else:
                return (
                    DecisionType.ABSTAIN,
                    0.6,
                    "The proposal shows potential but needs substantial revisions."
                )
        else:
            return (
                DecisionType.REJECT,
                0.8,
                "The proposal falls short of the required standards for inclusion."
            )
    
    def _suggest_improvements(self, eip_data: Dict[str, Any], weaknesses: List[str]) -> List[str]:
        """Suggest improvements based on identified weaknesses."""
        # Placeholder implementation
        # In practice, would generate tailored improvement suggestions
        suggestions = []
        
        for weakness in weaknesses:
            if "technical approach" in weakness.lower():
                suggestions.append("Refine the technical approach with more detailed specifications.")
            elif "security" in weakness.lower():
                suggestions.append("Add a security considerations section addressing potential vulnerabilities.")
            elif "compatibility" in weakness.lower():
                suggestions.append("Clarify how backward compatibility is maintained or provide migration path.")
            elif "efficiency" in weakness.lower():
                suggestions.append("Consider optimizations to reduce gas costs or computational overhead.")
            elif "complex" in weakness.lower():
                suggestions.append("Simplify the implementation approach without sacrificing functionality.")
            elif "use case" in weakness.lower():
                suggestions.append("Provide concrete examples of how this EIP benefits the ecosystem.")
        
        return suggestions
    
    # Helper methods for gas analysis
    
    def _analyze_gas_conceptually(self, description: str) -> tuple:
        """
        Analyze gas implications conceptually based on description.
        
        Returns:
            Tuple of (gas_impact, optimization_suggestions)
        """
        # Placeholder implementation
        # In practice, would perform detailed analysis based on text
        return "Moderate increase in gas costs", [
            "Consider batching operations to reduce overall gas cost",
            "Optimize storage access patterns",
            "Evaluate whether all proposed state changes are necessary"
        ]
    
    # Helper methods for compatibility analysis
    
    def _analyze_compatibility_conceptually(self, eip_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze compatibility conceptually based on EIP data.
        
        Returns:
            Compatibility analysis results
        """
        # Placeholder implementation
        return {
            "status": "success",
            "backward_compatible": True,
            "client_compatibility": {
                "geth": {"compatible": True, "notes": "No issues expected"},
                "nethermind": {"compatible": True, "notes": "No issues expected"},
                "erigon": {"compatible": True, "notes": "No issues expected"},
                "besu": {"compatible": True, "notes": "No issues expected"}
            },
            "tooling_compatibility": {
                "truffle": {"compatible": True},
                "hardhat": {"compatible": True},
                "foundry": {"compatible": True}
            },
            "warnings": []
        }
    
    # Helper methods for expertise provision
    
    def _generate_expert_response(self, question: str, relevant_expertise: List[str]) -> str:
        """Generate an expert response based on the question and relevant expertise."""
        # Placeholder implementation
        # In practice, would use LLM with specialized prompt
        if "consensus" in relevant_expertise:
            return "From a consensus perspective, this involves careful consideration of validator incentives and network security. The key technical aspects include..."
        elif "evm" in relevant_expertise:
            return "In terms of EVM execution, this would require changes to opcodes and gas costs. The implementation would need to account for..."
        elif "networking" in relevant_expertise:
            return "For the networking layer, this would impact how peers communicate and synchronize. The main considerations include..."
        else:
            return "This question involves multiple aspects of the Ethereum protocol. Based on my analysis..."
    
    @classmethod
    def from_config(cls, config: AgentConfig) -> "EthereumCoreDevAgent":
        """
        Create an EthereumCoreDevAgent from a configuration object.
        
        Args:
            config: Agent configuration
            
        Returns:
            An initialized EthereumCoreDevAgent
        """
        # Extract additional config for core dev agent
        extra_config = config.additional_config or {}
        expertise_areas = extra_config.get("expertise_areas", ["consensus", "evm", "networking"])
        is_champion = extra_config.get("is_champion", False)
        chain_id = extra_config.get("chain_id", 1)
        consensus_rules = extra_config.get("consensus_rules", None)
        
        return cls(
            name=config.name,
            role=config.role,
            goal=config.goal,
            model=config.model,
            temperature=config.temperature,
            expertise_areas=expertise_areas,
            is_champion=is_champion,
            chain_id=chain_id,
            consensus_rules=consensus_rules,
            verbose=config.verbose,
            **{k: v for k, v in extra_config.items() if k not in ["expertise_areas", "is_champion", "chain_id", "consensus_rules"]}
        ) 