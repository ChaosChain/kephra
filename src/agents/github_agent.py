"""
GitHub integration agents for Kephra.

GitHubIssueAgent: triages issues using the GitHub MCP server.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from src.agents.base_agent import KephraAgent, Agent
from src.config.settings import settings
from src.models.agent_models import AgentType

# Import MCP client
try:
    from modelcontextprotocol.client import Client as MCPClient
    from modelcontextprotocol.transport import StdioTransport
except ImportError:
    MCPClient = None

logger = logging.getLogger(__name__)

class IssueTriageAgent(KephraAgent):
    """
    Agent to triage GitHub issues via MCP, with EIP-specific classification taxonomy.
    Lists open issues, labels them with protocol/EIP tags via LLM, and updates labels on GitHub.
    """
    def __init__(
        self,
        name: str = "Issue Triage Agent",
        role: str = "Automate GitHub issue triage",
        goal: str = "Label open issues on a GitHub repository",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        verbose: bool = False
    ):
        super().__init__(
            name=name,
            role=role,
            goal=goal,
            agent_type=AgentType.PROPOSER,
            model=model or settings.default_agent_model,
            temperature=temperature or settings.temperature,
            verbose=verbose
        )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper for async GitHub issue triage.
        input_data: {
            "owner": "<github_org_or_user>",
            "repo": "<repo_name>",
            "state": "open"  # optional, default 'open'
        }
        """
        # Only use asyncio.run in a non-async context
        try:
            loop = asyncio.get_running_loop()
            # We're already in an event loop, so we can't use asyncio.run
            logger.warning("Calling process from inside an event loop - this will not work correctly")
            return {
                "owner": input_data.get("owner", "unknown"),
                "repo": input_data.get("repo", "unknown"),
                "triaged_issues": [],
                "error": "Cannot call asyncio.run from inside an event loop"
            }
        except RuntimeError:
            # No event loop running, so we can use asyncio.run
            return asyncio.run(self.process_async(input_data))
    
    def process_sync(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Version of process that can be called from async context.
        Uses GitHub API directly instead of MCP when available.
        Returns an empty list if token is not provided or on error.
        """
        owner = input_data.get("owner", "ethereum")
        repo = input_data.get("repo", "EIPs")
        
        # Check if we have a GitHub token in settings
        from src.config.settings import settings
        github_token = getattr(settings, "github_token", None)
        
        if github_token and github_token != "ghp_YOUR_GITHUB_TOKEN_HERE":
            # Use the GitHub API directly
            try:
                import requests
                
                # GitHub API endpoint for issues
                url = f"https://api.github.com/repos/{owner}/{repo}/issues"
                
                # Set up headers with token
                headers = {
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                
                # Get issues from GitHub
                response = requests.get(url, headers=headers, params={"state": "open"})
                response.raise_for_status()  # Raise exception for HTTP errors
                
                # Process the response
                github_issues = response.json()
                
                # Process issues
                processed_issues = []
                for issue in github_issues:
                    # Check if issue needs an EIP
                    title = issue.get("title", "")
                    body = issue.get("body", "")
                    needs_eip = self._check_if_needs_eip(title, body)
                    
                    # Get labels
                    labels = [label.get("name") for label in issue.get("labels", [])]
                    
                    # Process the issue
                    processed_issue = {
                        "number": issue.get("number"),
                        "title": title,
                        "body": body,
                        "labels": labels,
                        "needs_eip": needs_eip,
                        "repo": repo,
                        "url": issue.get("html_url")
                    }
                    processed_issues.append(processed_issue)
                
                # Filter for issues that need EIPs
                triaged_issues = [
                    issue for issue in processed_issues
                    if issue.get("needs_eip", False)
                ]
                
                logger.info(f"Found {len(processed_issues)} issues in {owner}/{repo}, {len(triaged_issues)} need EIPs")
                
                return {
                    "owner": owner,
                    "repo": repo,
                    "issues": processed_issues,
                    "triaged_issues": triaged_issues
                }
            
            except Exception as e:
                logger.error(f"Error fetching issues from GitHub: {str(e)}")
                logger.info("No issues returned - add valid GitHub token to fetch real issues")
        else:
            logger.info("No GitHub token available - add a valid token to fetch real issues")
        
        # Return empty lists instead of mock data
        return {
            "owner": owner,
            "repo": repo,
            "issues": [],  # Empty list instead of mock issues
            "triaged_issues": []  # Empty list instead of mock triaged issues
        }
    
    def _check_if_needs_eip(self, title: str, body: str) -> bool:
        """
        Check if an issue needs an EIP based on its title and body.
        This is a simplified heuristic - a real implementation would use more sophisticated NLP.
        """
        # Check for keywords that suggest EIP is needed
        eip_keywords = [
            "proposal", "eip", "standard", "improvement", "protocol", "new feature",
            "enhancement", "upgrade", "interface", "specification"
        ]
        
        # Combine title and body for search
        text = (title + " " + (body or "")).lower()
        
        # Check for keywords
        for keyword in eip_keywords:
            if keyword.lower() in text:
                return True
        
        return False

    async def process_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if MCPClient is None:
            raise RuntimeError("modelcontextprotocol package not installed")

        owner = input_data.get("owner")
        repo = input_data.get("repo")
        state = input_data.get("state", "open")

        # Connect to MCP GitHub server
        transport = StdioTransport()
        client = MCPClient(transport=transport)
        await client.initialize()

        # Fetch open issues
        response = await client.call_tool("list_issues", {
            "owner": owner,
            "repo": repo,
            "state": state
        })
        issues: List[Dict[str, Any]] = response.get("data", [])

        triaged: List[Dict[str, Any]] = []
        for issue in issues:
            number = issue.get("number")
            title = issue.get("title", "")
            body = issue.get("body", "")

            # Classify issue labels using LLM
            prompt = (
                f"Label this issue with comma-separated labels from: protocol, client-bug, security, upgrade, documentation, discussion "
                f"based on its title and description.\n\n"
                f"Title: {title}\n\nDescription: {body}"
            )
            # Use direct LLM call instead of the crewAI agent.chat method
            # We'll implement a mock for development
            raw = f"protocol, documentation"  # Mock response until we implement proper LLM integration
            labels = [lbl.strip() for lbl in raw.split(",") if lbl.strip()]

            # Update labels on GitHub via MCP
            await client.call_tool("update_issue_labels", {
                "owner": owner,
                "repo": repo,
                "issue_number": number,
                "labels": labels
            })

            triaged.append({
                "number": number,
                "title": title,
                "body": body,
                "assigned_labels": labels
            })

        return {
            "owner": owner,
            "repo": repo,
            "triaged_issues": triaged
        } 