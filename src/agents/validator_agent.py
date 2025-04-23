"""
Validator Agent for Kephra.

This agent is responsible for validating Ethereum Improvement Proposals (EIPs)
by performing rigorous checks, verifications, and attestations to ensure
proposals adhere to technical standards and are compatible with the Ethereum ecosystem.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.agents.base_agent import KephraAgent
from src.models.agent_models import AgentConfig, AgentType, DecisionType, ProposalEvaluation
from src.tools.validation_tools import CompatibilityChecker, ImplementationVerifier

logger = logging.getLogger(__name__)


class ValidatorAgent(KephraAgent):
    """
    Agent specialized in validating Ethereum Improvement Proposals.
    
    The validator performs technical verification and compatibility tests on proposals
    to ensure they work correctly, are technically sound, and integrate properly
    with the existing Ethereum ecosystem. It provides attestations regarding
    the implementability and compatibility of proposals.
    """
    
    def __init__(
        self,
        name: str,
        role: str = "Ethereum Proposal Validator",
        goal: str = "Rigorously verify proposals for technical correctness and ecosystem compatibility",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        reputation_score: float = 1.0,
        tools: Optional[List[Any]] = None,
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize a Validator Agent.
        
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
        # Initialize standard tools for validator if none provided
        if tools is None:
            tools = [
                CompatibilityChecker(),
                ImplementationVerifier(),
                # Add more specialized verification tools as needed
            ]
        
        super().__init__(
            name=name,
            role=role,
            goal=goal,
            agent_type=AgentType.VALIDATOR,
            model=model,
            temperature=temperature,
            reputation_score=reputation_score,
            tools=tools,
            verbose=verbose,
        )
        
        # Validator-specific attributes
        self.validation_checklist = kwargs.get("validation_checklist", [
            "code_correctness",
            "backward_compatibility",
            "edge_case_handling",
            "implementation_completeness",
            "security_compliance",
            "performance_impact",
            "gas_efficiency"
        ])
        
        self.validation_count = 0
        self.test_environments = kwargs.get("test_environments", ["mainnet-fork", "testnet", "local"])
        
        logger.info(f"Initialized ValidatorAgent: {name} with {len(self.validation_checklist)} validation criteria")
    
    def process(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a proposal to validate it according to technical specifications.
        
        Args:
            proposal_data: Proposal data to validate
            
        Returns:
            Validation results
        """
        logger.info(f"Validator {self.name} processing proposal: {proposal_data.get('proposal_id', 'Unknown')}")
        self.validation_count += 1
        
        # Extract key elements from the proposal
        proposal_id = proposal_data.get("proposal_id", "Unknown")
        specification = proposal_data.get("specification", "")
        implementation = proposal_data.get("implementation", "")
        test_suite = proposal_data.get("tests", {})
        
        # Perform validation tests
        validation_results = self._validate_proposal(proposal_data)
        
        # Run implementation in test environments
        test_results = self._run_implementation_tests(
            implementation=implementation,
            test_suite=test_suite,
            environments=self.test_environments
        )
        
        # Check edge cases and failure modes
        edge_case_results = self._check_edge_cases(implementation, proposal_data)
        
        # Consolidate results into a comprehensive validation report
        validation_report = {
            "proposal_id": proposal_id,
            "validation_id": f"VAL-{self.name}-{self.validation_count}",
            "validation_timestamp": self._get_timestamp(),
            "checks_passed": validation_results["checks_passed"],
            "checks_failed": validation_results["checks_failed"],
            "test_results": test_results,
            "edge_case_results": edge_case_results,
            "is_valid": validation_results["is_valid"],
            "attestation": self._generate_attestation(validation_results, test_results, edge_case_results),
        }
        
        logger.info(f"Validation completed for {proposal_id}: {'Valid' if validation_report['is_valid'] else 'Invalid'}")
        
        return validation_report
    
    def evaluate_proposal(self, proposal_id: str, proposal_data: Dict[str, Any]) -> ProposalEvaluation:
        """
        Evaluate a proposal and return a formal evaluation based on validation.
        
        Args:
            proposal_id: Unique identifier of the proposal
            proposal_data: The proposal data to evaluate
            
        Returns:
            A structured evaluation of the proposal
        """
        # Process the proposal to get validation results
        validation_report = self.process(proposal_data)
        
        # Extract attestation
        attestation = validation_report["attestation"]
        
        # Determine decision based on validation results
        if validation_report["is_valid"]:
            decision = DecisionType.APPROVE
        elif attestation["fixable"]:
            decision = DecisionType.ABSTAIN
        else:
            decision = DecisionType.REJECT
        
        # Create a formal evaluation object
        evaluation = ProposalEvaluation(
            proposal_id=proposal_id,
            agent_id=self.name,
            agent_type=AgentType.VALIDATOR,
            decision=decision,
            confidence=attestation["confidence"],
            reasoning=attestation["statement"],
            reputation_weight=self.reputation_score,
            metrics={
                "checks_passed": len(validation_report["checks_passed"]),
                "checks_failed": len(validation_report["checks_failed"]),
                "test_pass_rate": self._calculate_test_pass_rate(validation_report["test_results"]),
                "edge_case_pass_rate": self._calculate_edge_case_pass_rate(validation_report["edge_case_results"])
            }
        )
        
        return evaluation
    
    def _validate_proposal(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a proposal against the validation checklist.
        
        Args:
            proposal_data: The proposal data to validate
            
        Returns:
            Validation results including passed and failed checks
        """
        # In a real implementation, this would perform actual validation checks
        # using the provided tools and external verification methods
        
        # For this skeleton, we'll simulate validation results
        checks_passed = []
        checks_failed = []
        
        # Simulate validation checks
        for check in self.validation_checklist:
            # For demo purposes, simulate different outcomes for different checks
            if check in ["code_correctness", "implementation_completeness", "gas_efficiency"]:
                # Assume these checks pass if implementation is provided
                if proposal_data.get("implementation"):
                    checks_passed.append(check)
                else:
                    checks_failed.append(f"{check} - No implementation provided")
            
            elif check == "backward_compatibility":
                # Check if backward compatibility is explicitly addressed
                if "backward_compatibility" in proposal_data.get("considerations", []):
                    checks_passed.append(check)
                else:
                    checks_failed.append(f"{check} - Backward compatibility not addressed")
            
            elif check == "edge_case_handling":
                # Check if edge cases are documented and handled
                if proposal_data.get("edge_cases") or proposal_data.get("tests", {}).get("edge_cases"):
                    checks_passed.append(check)
                else:
                    checks_failed.append(f"{check} - Edge cases not documented")
            
            elif check == "security_compliance":
                # Check if security considerations are addressed
                if "security" in proposal_data.get("considerations", []):
                    checks_passed.append(check)
                else:
                    checks_failed.append(f"{check} - Security considerations not addressed")
            
            elif check == "performance_impact":
                # Check if performance impact is addressed
                if "performance" in proposal_data.get("considerations", []):
                    checks_passed.append(check)
                else:
                    checks_failed.append(f"{check} - Performance impact not addressed")
        
        # Determine if the proposal is valid based on failed checks
        is_valid = len(checks_failed) == 0 or (
            len(checks_failed) < len(self.validation_checklist) / 3  # Less than 1/3 of checks failed
            and not any(critical in checks_failed for critical in [
                "code_correctness", "security_compliance"  # Critical checks
            ])
        )
        
        return {
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "is_valid": is_valid
        }
    
    def _run_implementation_tests(
        self, 
        implementation: str, 
        test_suite: Dict[str, Any],
        environments: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run tests on the implementation in different environments.
        
        Args:
            implementation: The implementation code
            test_suite: Test cases to run
            environments: Environments to test in
            
        Returns:
            Test results by environment
        """
        # In a real implementation, this would run actual tests
        # For this skeleton, we'll simulate test results
        
        results = {}
        
        for env in environments:
            # Simulate test runs in each environment
            env_results = {
                "passed": [],
                "failed": [],
                "pass_rate": 0.0,
            }
            
            # If no implementation or tests, all tests "fail"
            if not implementation or not test_suite:
                env_results["passed"] = []
                env_results["failed"] = ["No implementation or tests provided"]
                env_results["pass_rate"] = 0.0
            else:
                # Simulate test results based on environment
                if env == "mainnet-fork":
                    # Mainnet tests are more stringent
                    env_results["passed"] = ["basic_functionality", "standard_cases"]
                    env_results["failed"] = ["edge_cases", "gas_optimization"]
                    env_results["pass_rate"] = 0.5
                elif env == "testnet":
                    # Testnet passes more tests
                    env_results["passed"] = ["basic_functionality", "standard_cases", "edge_cases"]
                    env_results["failed"] = ["gas_optimization"]
                    env_results["pass_rate"] = 0.75
                else:  # local
                    # Local environment passes all tests
                    env_results["passed"] = ["basic_functionality", "standard_cases", "edge_cases", "gas_optimization"]
                    env_results["failed"] = []
                    env_results["pass_rate"] = 1.0
            
            results[env] = env_results
        
        return results
    
    def _check_edge_cases(self, implementation: str, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check implementation against edge cases and failure modes.
        
        Args:
            implementation: The implementation code
            proposal_data: The full proposal data
            
        Returns:
            Edge case test results
        """
        # In a real implementation, this would run edge case tests
        # For this skeleton, we'll simulate results
        
        # Check if edge cases are defined
        edge_cases = proposal_data.get("edge_cases", [])
        
        if not implementation or not edge_cases:
            return {
                "passed": [],
                "failed": ["No implementation or edge cases provided"],
                "pass_rate": 0.0
            }
        
        # Simulate edge case testing
        # For demo purposes, assume 80% of edge cases pass
        num_edge_cases = len(edge_cases)
        num_passed = int(num_edge_cases * 0.8)
        
        passed = edge_cases[:num_passed]
        failed = edge_cases[num_passed:]
        
        return {
            "passed": passed,
            "failed": failed,
            "pass_rate": num_passed / num_edge_cases if num_edge_cases > 0 else 0.0
        }
    
    def _generate_attestation(
        self,
        validation_results: Dict[str, Any],
        test_results: Dict[str, Dict[str, Any]],
        edge_case_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a formal attestation based on validation and test results.
        
        Args:
            validation_results: Results from validation checks
            test_results: Results from implementation tests
            edge_case_results: Results from edge case testing
            
        Returns:
            Formal attestation
        """
        # Determine if the proposal is valid overall
        is_valid = validation_results["is_valid"]
        
        # Calculate overall test pass rate across environments
        total_passed = sum(len(results["passed"]) for results in test_results.values())
        total_tests = total_passed + sum(len(results["failed"]) for results in test_results.values())
        test_pass_rate = total_passed / total_tests if total_tests > 0 else 0.0
        
        # Calculate edge case pass rate
        edge_case_pass_rate = edge_case_results["pass_rate"]
        
        # Determine confidence based on test and edge case results
        confidence = (test_pass_rate * 0.6) + (edge_case_pass_rate * 0.4)
        
        # Determine if issues are fixable
        fixable = not is_valid and len(validation_results["checks_failed"]) < len(self.validation_checklist) / 2
        
        # Generate attestation statement
        if is_valid:
            if confidence > 0.8:
                statement = (
                    "I formally attest that this proposal has been rigorously validated and passes all "
                    f"critical checks with a confidence of {confidence:.2f}. The implementation has been "
                    "tested across multiple environments and handles edge cases appropriately."
                )
            else:
                statement = (
                    "I attest that this proposal passes validation checks, but with some concerns about "
                    f"test coverage (pass rate: {test_pass_rate:.2f}) and edge case handling "
                    f"(pass rate: {edge_case_pass_rate:.2f}). It is technically valid but would benefit from "
                    "additional testing and refinement."
                )
        else:
            if fixable:
                statement = (
                    "I cannot attest to the validity of this proposal in its current form. It fails "
                    f"{len(validation_results['checks_failed'])} validation checks that should be addressed. "
                    "However, these issues appear fixable with targeted improvements."
                )
            else:
                statement = (
                    "I formally reject attestation for this proposal due to significant validation failures. "
                    f"It fails {len(validation_results['checks_failed'])} critical checks including "
                    f"{', '.join(validation_results['checks_failed'][:3])}... These issues suggest "
                    "fundamental problems with the proposal's design or implementation."
                )
        
        return {
            "valid": is_valid,
            "confidence": confidence,
            "fixable": fixable,
            "statement": statement
        }
    
    def _calculate_test_pass_rate(self, test_results: Dict[str, Dict[str, Any]]) -> float:
        """
        Calculate the overall test pass rate across all environments.
        
        Args:
            test_results: Test results by environment
            
        Returns:
            Overall test pass rate
        """
        total_passed = sum(len(results["passed"]) for results in test_results.values())
        total_tests = total_passed + sum(len(results["failed"]) for results in test_results.values())
        return total_passed / total_tests if total_tests > 0 else 0.0
    
    def _calculate_edge_case_pass_rate(self, edge_case_results: Dict[str, Any]) -> float:
        """
        Calculate the edge case pass rate.
        
        Args:
            edge_case_results: Edge case test results
            
        Returns:
            Edge case pass rate
        """
        return edge_case_results["pass_rate"]
    
    def _get_timestamp(self) -> str:
        """
        Get the current timestamp in ISO format.
        
        Returns:
            Current timestamp
        """
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    @classmethod
    def from_config(cls, config: AgentConfig) -> "ValidatorAgent":
        """
        Create a ValidatorAgent from a configuration object.
        
        Args:
            config: Agent configuration
            
        Returns:
            An initialized ValidatorAgent
        """
        return cls(
            name=config.name,
            role=config.role,
            goal=config.goal,
            model=config.model,
            temperature=config.temperature,
            reputation_score=config.reputation_score,
            verbose=config.verbose,
            test_environments=config.additional_config.get("test_environments", ["mainnet-fork", "testnet", "local"]),
            **config.additional_config
        ) 