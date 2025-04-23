"""
Ethereum Core Developer Agent for protocol and EIP development
"""

import logging
import re
import random
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.common.schema import EIPProposal, GithubIssue, EIPCategory, EIPStatus, EIPType
from src.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

class EthereumCoreDevAgent(BaseAgent):
    """
    Agent that simulates an Ethereum core developer.
    
    This agent can:
    1. Analyze GitHub issues and determine if they need an EIP
    2. Draft EIP proposals based on issues
    3. Provide technical feedback on EIPs
    4. Simulate implementation impact
    5. Vote on EIPs in governance calls
    
    Each core dev agent has a specialty area and client focus,
    influencing their perspective and priorities.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str = None,
        specialty: str = None,
        client: str = None,
        **kwargs
    ):
        """
        Initialize the Ethereum Core Dev Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name for this agent
            specialty: Area of expertise (consensus, execution, p2p, etc.)
            client: Preferred Ethereum client (geth, erigon, etc.)
            **kwargs: Additional arguments passed to BaseAgent
        """
        super().__init__(agent_id=agent_id, **kwargs)
        
        # Set default name if not provided
        if name is None:
            name = f"CoreDev-{agent_id[-6:]}"
        self.name = name
        
        # Set specialty if not provided
        if specialty is None:
            specialties = [
                "consensus layer", "execution layer", "networking", 
                "cryptography", "tooling", "testing", "performance"
            ]
            specialty = random.choice(specialties)
        self.specialty = specialty
        
        # Set client preference if not provided
        if client is None:
            clients = settings["ethereum"]["clients"]
            client = random.choice(clients)
        self.client = client
        
        # Agent's personality traits (influences decision making)
        self.traits = {
            "innovation": random.uniform(0.3, 1.0),  # Preference for novel solutions
            "caution": random.uniform(0.3, 1.0),     # Risk aversion
            "community": random.uniform(0.3, 1.0),   # Emphasis on community needs
            "pragmatism": random.uniform(0.3, 1.0),  # Focus on practicality
            "decentralization": random.uniform(0.5, 1.0),  # Prioritization of decentralization
        }
        
        # Agent's knowledge and background
        self.background = self._generate_background()
        
        logger.info(f"Created {self.name} (ID: {agent_id}): {self.specialty} specialist with {self.client} focus")
    
    def _generate_background(self) -> str:
        """Generate a plausible background for this core developer."""
        years_experience = random.randint(2, 10)
        
        backgrounds = [
            f"Ethereum core developer with {years_experience} years of experience, focused on {self.specialty}.",
            f"Open source contributor to {self.client} for {years_experience} years, specializing in {self.specialty}.",
            f"Protocol researcher with background in {self.specialty}, contributing to {self.client} development.",
            f"Former researcher now working on {self.specialty} for Ethereum, primarily with {self.client}.",
            f"Smart contract security expert who transitioned to core development in {self.specialty}."
        ]
        
        return random.choice(backgrounds)
    
    def analyze_issue(self, issue: GithubIssue) -> Dict[str, Any]:
        """
        Analyze a GitHub issue to determine if it requires an EIP,
        and what kind of EIP would be appropriate.
        
        Args:
            issue: The GitHub issue to analyze
            
        Returns:
            Analysis result containing:
            - needs_eip: Whether this issue should become an EIP
            - eip_type: Suggested EIP type if applicable
            - eip_category: Suggested EIP category if applicable
            - confidence: Confidence level in this assessment
            - rationale: Reasoning behind the decision
        """
        logger.info(f"{self.name} analyzing issue #{issue.number}: {issue.title}")
        
        # Prepare prompt for the LLM
        prompt = self._create_issue_analysis_prompt(issue)
        
        # Get response from LLM
        response = self.llm.generate_text(prompt)
        
        # Parse the analysis from the response
        return self._parse_issue_analysis(response, issue)
    
    def _create_issue_analysis_prompt(self, issue: GithubIssue) -> str:
        """Create a prompt for analyzing whether an issue needs an EIP."""
        return f"""You are {self.name}, an Ethereum core developer specializing in {self.specialty}
with particular experience using {self.client}. {self.background}

Your task is to analyze the following GitHub issue from the Ethereum repository
and determine whether it should be addressed with an Ethereum Improvement Proposal (EIP).

---
ISSUE #{issue.number}: {issue.title}

Created by: {issue.author}
Created on: {issue.created_at}
Labels: {', '.join(issue.labels) if issue.labels else 'None'}

{issue.body}
---

Please analyze this issue and respond with the following information in JSON format:

1. Does this issue need an EIP? (Answer with "needs_eip": true or false)
2. If it needs an EIP, what type of EIP? (Standards Track, Informational, or Meta)
3. If it's a Standards Track EIP, what category? (Core, Networking, Interface, ERC)
4. What is your confidence level in this assessment? (0.0 to 1.0)
5. Provide a brief rationale for your decision.

Response format:
{{"needs_eip": true/false, "eip_type": "Standards Track/Informational/Meta", "eip_category": "Core/Networking/Interface/ERC", "confidence": 0.X, "rationale": "Your reasoning here"}}
"""
    
    def _parse_issue_analysis(self, response: str, issue: GithubIssue) -> Dict[str, Any]:
        """Parse the LLM response to extract analysis details."""
        logger.debug(f"Raw analysis response: {response}")
        
        try:
            # Try to extract JSON from the response
            import json
            
            # Find JSON-like content
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                analysis = json.loads(json_str)
            else:
                # Fallback parsing
                analysis = {
                    "needs_eip": "true" in response.lower() and "needs_eip" in response.lower(),
                    "eip_type": "Standards Track" if "Standards Track" in response else "Informational",
                    "eip_category": "Core",  # Default
                    "confidence": 0.5,  # Default
                    "rationale": "Extracted from non-JSON response"
                }
                
                # Try to determine category
                for category in ["Core", "Networking", "Interface", "ERC"]:
                    if category in response:
                        analysis["eip_category"] = category
                        break
            
            # Ensure required fields have appropriate values
            if "needs_eip" not in analysis:
                analysis["needs_eip"] = False
                
            # Convert string 'true'/'false' to boolean if needed
            if isinstance(analysis["needs_eip"], str):
                analysis["needs_eip"] = analysis["needs_eip"].lower() == "true"
                
            if "confidence" not in analysis:
                analysis["confidence"] = 0.5
                
            if "rationale" not in analysis:
                analysis["rationale"] = "No explicit rationale provided"
            
            # Add additional metadata
            analysis["issue_number"] = issue.number
            analysis["agent_id"] = self.agent_id
            analysis["agent_name"] = self.name
            analysis["timestamp"] = datetime.now().isoformat()
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error parsing analysis response: {e}")
            # Return fallback analysis
            return {
                "needs_eip": False,
                "eip_type": "Standards Track",
                "eip_category": "Core",
                "confidence": 0.3,
                "rationale": f"Error parsing response: {str(e)}",
                "issue_number": issue.number,
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    def draft_eip(self, issue: GithubIssue, analysis: Dict[str, Any]) -> EIPProposal:
        """
        Draft an EIP proposal based on a GitHub issue and its analysis.
        
        Args:
            issue: The GitHub issue to base the EIP on
            analysis: Previous analysis of the issue
            
        Returns:
            A draft EIP proposal
        """
        logger.info(f"{self.name} drafting EIP for issue #{issue.number}: {issue.title}")
        
        # Prepare prompt for the LLM
        prompt = self._create_eip_draft_prompt(issue, analysis)
        
        # Get response from LLM
        response = self.llm.generate_text(prompt)
        
        # Parse the EIP from the response
        return self._parse_eip_draft(response, issue, analysis)
    
    def _create_eip_draft_prompt(self, issue: GithubIssue, analysis: Dict[str, Any]) -> str:
        """Create a prompt for drafting an EIP based on an issue."""
        return f"""You are {self.name}, an Ethereum core developer specializing in {self.specialty}
with particular experience using {self.client}. {self.background}

Your task is to draft an Ethereum Improvement Proposal (EIP) based on the following GitHub issue:

---
ISSUE #{issue.number}: {issue.title}

Created by: {issue.author}
Created on: {issue.created_at}
Labels: {', '.join(issue.labels) if issue.labels else 'None'}

{issue.body}
---

Your analysis determined that this issue needs an EIP with the following details:
- EIP Type: {analysis.get('eip_type', 'Standards Track')}
- EIP Category: {analysis.get('eip_category', 'Core')}
- Rationale: {analysis.get('rationale', 'Not provided')}

Please draft a complete EIP in markdown format following the official EIP template.
Include all required sections: Abstract, Motivation, Specification, Rationale, and
Backwards Compatibility. If applicable, also include Security Considerations and
Test Cases. Make your draft technically precise and complete enough to be considered
by the Ethereum community.

Take into account your specialty in {self.specialty} and experience with {self.client}
when drafting technical details. Your proposal should be practical to implement,
aligned with Ethereum's ethos, and clear in its benefits.
"""
    
    def _parse_eip_draft(self, response: str, issue: GithubIssue, analysis: Dict[str, Any]) -> EIPProposal:
        """Parse the LLM response to create an EIP proposal object."""
        # Extract title using regex
        title_match = re.search(r'(?:title:|# EIP-XXXX:|# )(.+?)\n', response, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else issue.title
        
        # Extract abstract
        abstract_match = re.search(r'(?:## Abstract|## Simple Summary)\s+(.*?)(?:##|\Z)', 
                                  response, re.DOTALL | re.IGNORECASE)
        abstract = abstract_match.group(1).strip() if abstract_match else ""
        
        # Extract authors - default to core dev name if not found
        authors_match = re.search(r'(?:author:|authors:)(.+?)\n', response, re.IGNORECASE)
        authors = authors_match.group(1).strip() if authors_match else self.name
        
        # Determine EIP type from analysis
        eip_type_str = analysis.get('eip_type', 'Standards Track')
        try:
            eip_type = EIPType[eip_type_str.replace(' ', '_').upper()]
        except (KeyError, AttributeError):
            eip_type = EIPType.STANDARDS_TRACK
        
        # Determine EIP category from analysis
        eip_category_str = analysis.get('eip_category', 'Core')
        try:
            eip_category = EIPCategory[eip_category_str.upper()]
        except (KeyError, AttributeError):
            eip_category = EIPCategory.CORE
        
        # Create EIP proposal
        eip = EIPProposal(
            title=title,
            abstract=abstract,
            content=response,
            authors=[authors],
            type=eip_type,
            category=eip_category,
            status=EIPStatus.DRAFT,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            github_issue_id=issue.number,
            eip_number=None,  # To be assigned later
            source_agent_id=self.agent_id,
        )
        
        return eip
    
    def review_eip(self, eip: EIPProposal) -> Dict[str, Any]:
        """
        Review an EIP proposal and provide feedback.
        
        Args:
            eip: The EIP proposal to review
            
        Returns:
            Review results containing:
            - score: Overall score for the EIP (0.0 to 1.0)
            - feedback: Detailed feedback
            - concerns: List of concerns
            - strengths: List of strengths
            - decision: Recommendation (approve, reject, revise)
        """
        logger.info(f"{self.name} reviewing EIP: {eip.title}")
        
        # Prepare prompt for the LLM
        prompt = self._create_eip_review_prompt(eip)
        
        # Get response from LLM
        response = self.llm.generate_text(prompt)
        
        # Parse the review from the response
        return self._parse_eip_review(response, eip)
    
    def _create_eip_review_prompt(self, eip: EIPProposal) -> str:
        """Create a prompt for reviewing an EIP."""
        return f"""You are {self.name}, an Ethereum core developer specializing in {self.specialty}
with particular experience using {self.client}. {self.background}

Your task is to review the following Ethereum Improvement Proposal (EIP) and provide
technical feedback based on your expertise.

---
{eip.content}
---

Please review this EIP thoroughly, considering:
1. Technical correctness and completeness
2. Alignment with Ethereum's principles and roadmap
3. Implementation feasibility, especially for {self.client}
4. Backwards compatibility concerns
5. Security implications
6. Overall clarity and quality

Based on your specialty in {self.specialty}, pay particular attention to aspects
related to your domain of expertise.

Provide your review in JSON format with the following structure:
{{
  "score": 0.X,  // Overall score from 0.0 to 1.0
  "feedback": "Your detailed feedback here",
  "concerns": ["Concern 1", "Concern 2", ...],
  "strengths": ["Strength 1", "Strength 2", ...],
  "decision": "approve/reject/revise"
}}

Your score should reflect your overall assessment, where:
- 0.0-0.3: Reject, significant issues
- 0.4-0.6: Needs major revisions
- 0.7-0.8: Minor revisions recommended
- 0.9-1.0: Approve as is
"""

    def _parse_eip_review(self, response: str, eip: EIPProposal) -> Dict[str, Any]:
        """Parse the LLM response to extract review details."""
        logger.debug(f"Raw review response: {response}")
        
        try:
            # Try to extract JSON from the response
            import json
            
            # Find JSON-like content
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                review = json.loads(json_str)
            else:
                # Fallback parsing for non-JSON responses
                review = {
                    "score": 0.5,  # Default
                    "feedback": response,
                    "concerns": ["Response format was incorrect"],
                    "strengths": [],
                    "decision": "revise"
                }
            
            # Validate and fill missing fields
            if "score" not in review:
                review["score"] = 0.5
                
            if "feedback" not in review:
                review["feedback"] = "No detailed feedback provided"
                
            if "concerns" not in review:
                review["concerns"] = []
                
            if "strengths" not in review:
                review["strengths"] = []
                
            if "decision" not in review:
                # Derive decision based on score
                score = review["score"]
                if score >= 0.9:
                    review["decision"] = "approve"
                elif score <= 0.3:
                    review["decision"] = "reject"
                else:
                    review["decision"] = "revise"
            
            # Add additional metadata
            review["eip_title"] = eip.title
            review["agent_id"] = self.agent_id
            review["agent_name"] = self.name
            review["specialty"] = self.specialty
            review["timestamp"] = datetime.now().isoformat()
            
            # Log the review
            logger.info(f"{self.name} reviewed '{eip.title}' - Score: {review['score']}, Decision: {review['decision']}")
            
            return review
            
        except Exception as e:
            logger.error(f"Error parsing review response: {e}")
            # Return fallback review
            return {
                "score": 0.5,
                "feedback": f"Error parsing review: {str(e)}\n\nRaw response: {response}",
                "concerns": ["Error in review processing"],
                "strengths": [],
                "decision": "revise",
                "eip_title": eip.title,
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "specialty": self.specialty,
                "timestamp": datetime.now().isoformat()
            }
    
    def simulate_implementation(self, eip: EIPProposal) -> Dict[str, Any]:
        """
        Simulate the implementation of an EIP and assess its impact.
        
        Args:
            eip: The EIP to simulate
            
        Returns:
            Simulation results containing:
            - feasibility: Implementation feasibility score (0.0 to 1.0)
            - complexity: Implementation complexity assessment
            - estimated_effort: Estimated development effort in person-weeks
            - impact: Impact on client implementations
            - risks: Potential risks or issues
        """
        logger.info(f"{self.name} simulating implementation for EIP: {eip.title}")
        
        # Prepare prompt for the LLM
        prompt = self._create_simulation_prompt(eip)
        
        # Get response from LLM
        response = self.llm.generate_text(prompt)
        
        # Parse the simulation results from the response
        return self._parse_simulation_results(response, eip)
    
    def _create_simulation_prompt(self, eip: EIPProposal) -> str:
        """Create a prompt for simulating EIP implementation."""
        return f"""You are {self.name}, an Ethereum core developer specializing in {self.specialty}
with particular experience using {self.client}. {self.background}

Your task is to simulate the implementation of the following EIP and assess its
technical impact, especially on {self.client} and other Ethereum clients.

---
{eip.content}
---

Please analyze this EIP from an implementation perspective and provide:

1. A technical assessment of implementation feasibility
2. Complexity analysis for different Ethereum clients
3. Estimated development effort required
4. Potential impacts on network performance, security, and user experience
5. Any risks or challenges specific to {self.client} implementation

Based on your specialty in {self.specialty}, provide detailed insights on
implementation challenges and opportunities in that area.

Respond in JSON format with the following structure:
{{
  "feasibility": 0.X,  // Implementation feasibility score from 0.0 to 1.0
  "complexity": "low/medium/high",
  "estimated_effort": X,  // Person-weeks of development effort
  "client_impacts": {{
    "geth": "Description of impact on Geth",
    "erigon": "Description of impact on Erigon",
    "nethermind": "Description of impact on Nethermind",
    "besu": "Description of impact on Besu"
  }},
  "performance_impact": "Description of performance impact",
  "security_considerations": "Security analysis",
  "risks": ["Risk 1", "Risk 2", ...],
  "implementation_notes": "Detailed implementation guidance"
}}
"""

    def _parse_simulation_results(self, response: str, eip: EIPProposal) -> Dict[str, Any]:
        """Parse the LLM response to extract simulation results."""
        logger.debug(f"Raw simulation response: {response}")
        
        try:
            # Try to extract JSON from the response
            import json
            
            # Find JSON-like content
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                simulation = json.loads(json_str)
            else:
                # Fallback parsing for non-JSON responses
                simulation = {
                    "feasibility": 0.5,  # Default
                    "complexity": "medium",
                    "estimated_effort": 4,  # Default 4 weeks
                    "client_impacts": {
                        "geth": "Unknown impact",
                        "erigon": "Unknown impact",
                        "nethermind": "Unknown impact",
                        "besu": "Unknown impact"
                    },
                    "performance_impact": "Unknown",
                    "security_considerations": "Not assessed",
                    "risks": ["Response format was incorrect"],
                    "implementation_notes": response
                }
            
            # Validate and fill missing fields
            if "feasibility" not in simulation:
                simulation["feasibility"] = 0.5
                
            if "complexity" not in simulation:
                simulation["complexity"] = "medium"
                
            if "estimated_effort" not in simulation:
                simulation["estimated_effort"] = 4
                
            if "client_impacts" not in simulation:
                simulation["client_impacts"] = {
                    "geth": "Not assessed",
                    "erigon": "Not assessed",
                    "nethermind": "Not assessed",
                    "besu": "Not assessed"
                }
                
            if "risks" not in simulation:
                simulation["risks"] = []
            
            # Add additional metadata
            simulation["eip_title"] = eip.title
            simulation["agent_id"] = self.agent_id
            simulation["agent_name"] = self.name
            simulation["specialty"] = self.specialty
            simulation["timestamp"] = datetime.now().isoformat()
            
            # Log the simulation results
            logger.info(f"{self.name} simulated '{eip.title}' - Feasibility: {simulation['feasibility']}, Complexity: {simulation['complexity']}")
            
            return simulation
            
        except Exception as e:
            logger.error(f"Error parsing simulation response: {e}")
            # Return fallback simulation
            return {
                "feasibility": 0.5,
                "complexity": "medium",
                "estimated_effort": 4,
                "client_impacts": {
                    "geth": "Not assessed due to error",
                    "erigon": "Not assessed due to error",
                    "nethermind": "Not assessed due to error",
                    "besu": "Not assessed due to error"
                },
                "performance_impact": f"Error parsing simulation: {str(e)}",
                "security_considerations": "Not assessed due to error",
                "risks": ["Error in simulation processing"],
                "implementation_notes": f"Raw response: {response}",
                "eip_title": eip.title,
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "specialty": self.specialty,
                "timestamp": datetime.now().isoformat()
            }
    
    def vote_on_eip(self, eip: EIPProposal, reviews: List[Dict[str, Any]], simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Vote on an EIP proposal based on reviews and simulations.
        
        Args:
            eip: The EIP to vote on
            reviews: List of reviews from various agents
            simulations: List of simulation results
            
        Returns:
            Voting results containing:
            - vote: Final vote (for/against/abstain)
            - confidence: Confidence in the vote (0.0 to 1.0)
            - rationale: Reasoning behind the vote
        """
        logger.info(f"{self.name} voting on EIP: {eip.title}")
        
        # Prepare prompt for the LLM
        prompt = self._create_voting_prompt(eip, reviews, simulations)
        
        # Get response from LLM
        response = self.llm.generate_text(prompt)
        
        # Parse the vote from the response
        return self._parse_vote(response, eip)
    
    def _create_voting_prompt(self, eip: EIPProposal, reviews: List[Dict[str, Any]], simulations: List[Dict[str, Any]]) -> str:
        """Create a prompt for voting on an EIP."""
        # Format reviews for inclusion in prompt
        reviews_text = "\n\n".join([
            f"Review by {review.get('agent_name', 'Anonymous')} (specialty: {review.get('specialty', 'unknown')}):\n"
            f"- Score: {review.get('score', 'N/A')}\n"
            f"- Decision: {review.get('decision', 'N/A')}\n"
            f"- Feedback: {review.get('feedback', 'None provided')[:300]}...\n"
            f"- Concerns: {', '.join(review.get('concerns', []))}\n"
            f"- Strengths: {', '.join(review.get('strengths', []))}"
            for review in reviews
        ])
        
        # Format simulations for inclusion in prompt
        simulations_text = "\n\n".join([
            f"Simulation by {sim.get('agent_name', 'Anonymous')} (specialty: {sim.get('specialty', 'unknown')}):\n"
            f"- Feasibility: {sim.get('feasibility', 'N/A')}\n"
            f"- Complexity: {sim.get('complexity', 'N/A')}\n"
            f"- Estimated Effort: {sim.get('estimated_effort', 'N/A')} person-weeks\n"
            f"- {self.client} Impact: {sim.get('client_impacts', {}).get(self.client.lower(), 'Not assessed')}\n"
            f"- Risks: {', '.join(sim.get('risks', []))}"
            for sim in simulations
        ])
        
        return f"""You are {self.name}, an Ethereum core developer specializing in {self.specialty}
with particular experience using {self.client}. {self.background}

You need to cast your vote on the following EIP proposal during an Ethereum core
developer call.

EIP TITLE: {eip.title}
EIP TYPE: {eip.type.name.replace('_', ' ')}
EIP CATEGORY: {eip.category.name}

ABSTRACT:
{eip.abstract}

REVIEWS FROM OTHER CORE DEVELOPERS:
{reviews_text}

IMPLEMENTATION SIMULATIONS:
{simulations_text}

Based on your expertise, personal traits, and the feedback above, cast your vote
on this EIP. Consider:

1. Your specialty in {self.specialty} and how this EIP impacts that area
2. Your experience with {self.client} and implementation concerns
3. Your personal traits:
   - Innovation priority: {self.traits['innovation']:.2f}
   - Caution level: {self.traits['caution']:.2f}
   - Community focus: {self.traits['community']:.2f}
   - Pragmatism: {self.traits['pragmatism']:.2f}
   - Decentralization priority: {self.traits['decentralization']:.2f}

Respond in JSON format:
{{
  "vote": "for/against/abstain",
  "confidence": 0.X,  // Confidence in your vote from 0.0 to 1.0
  "rationale": "Your detailed reasoning here",
  "conditions": "Any conditions for changing your vote",
  "alignment": "How this aligns with your specialty and values"
}}
"""

    def _parse_vote(self, response: str, eip: EIPProposal) -> Dict[str, Any]:
        """Parse the LLM response to extract voting details."""
        logger.debug(f"Raw voting response: {response}")
        
        try:
            # Try to extract JSON from the response
            import json
            
            # Find JSON-like content
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                vote = json.loads(json_str)
            else:
                # Fallback parsing for non-JSON responses
                vote = {
                    "vote": "abstain",  # Default if cannot determine
                    "confidence": 0.5,
                    "rationale": response,
                    "conditions": "None specified",
                    "alignment": "Could not determine from response"
                }
                
                # Try to determine vote from text
                if "vote for" in response.lower() or "in favor" in response.lower():
                    vote["vote"] = "for"
                elif "vote against" in response.lower() or "not in favor" in response.lower():
                    vote["vote"] = "against"
            
            # Validate and fill missing fields
            if "vote" not in vote:
                vote["vote"] = "abstain"
                
            if "confidence" not in vote:
                vote["confidence"] = 0.5
                
            if "rationale" not in vote:
                vote["rationale"] = "No rationale provided"
                
            if "conditions" not in vote:
                vote["conditions"] = "None specified"
                
            if "alignment" not in vote:
                vote["alignment"] = "Not specified"
            
            # Add additional metadata
            vote["eip_title"] = eip.title
            vote["agent_id"] = self.agent_id
            vote["agent_name"] = self.name
            vote["specialty"] = self.specialty
            vote["client"] = self.client
            vote["timestamp"] = datetime.now().isoformat()
            
            # Log the vote
            logger.info(f"{self.name} voted '{vote['vote']}' on '{eip.title}' with confidence {vote['confidence']}")
            
            return vote
            
        except Exception as e:
            logger.error(f"Error parsing vote response: {e}")
            # Return fallback vote
            return {
                "vote": "abstain",
                "confidence": 0.3,
                "rationale": f"Error parsing vote: {str(e)}\n\nRaw response: {response}",
                "conditions": "Error occurred during voting",
                "alignment": "Not assessed due to error",
                "eip_title": eip.title,
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "specialty": self.specialty,
                "client": self.client,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_profile(self) -> Dict[str, Any]:
        """
        Get the agent's profile including its specialties and traits.
        
        Returns:
            Dictionary with agent profile information
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "agent_type": "EthereumCoreDevAgent",
            "specialty": self.specialty,
            "client": self.client,
            "background": self.background,
            "traits": self.traits,
        } 