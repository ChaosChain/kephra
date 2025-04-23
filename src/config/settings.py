"""
Configuration settings for the Kephra agent system.
Loads values from environment variables or .env file.
"""

import os
from enum import Enum
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import logging

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file if it exists
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"
TMP_DIR = BASE_DIR / "tmp"

# GitHub settings
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "ethereum")
GITHUB_REPOS = os.getenv("GITHUB_REPOS", "EIPs").split(",")
ISSUE_POLLING_INTERVAL = int(os.getenv("ISSUE_POLLING_INTERVAL", "300"))

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_FILE = os.getenv("LOG_FILE", str(LOGS_DIR / "kephra.log"))

# Agent settings
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4")
MOCK_AGENT = os.getenv("MOCK_AGENT", "false").lower() == "true"

# Mock data settings
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
USE_MOCK_ISSUES = os.getenv("USE_MOCK_ISSUES", "false").lower() == "true"
USE_MOCK_EIPS = os.getenv("USE_MOCK_EIPS", "false").lower() == "true"

# MCP settings
MCP_ENABLED = os.getenv("MCP_ENABLED", "true").lower() == "true"
MCP_MOCK_ENABLED = os.getenv("MCP_MOCK_ENABLED", "true").lower() == "true"
MCP_HOST = os.getenv("MCP_HOST", "localhost")
MCP_PORT_BASE = int(os.getenv("MCP_PORT_BASE", "8001"))
MCP_DEBUG = os.getenv("MCP_DEBUG", "false").lower() == "true"

# Dashboard settings
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "localhost")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))
DASHBOARD_DEBUG = os.getenv("DASHBOARD_DEBUG", "false").lower() == "true"

# EIP Repository settings
EIP_DIR = os.getenv("EIP_DIR", str(DATA_DIR / "eips"))
EIP_REPO_URL = os.getenv("EIP_REPO_URL", "https://github.com/ethereum/EIPs.git")
EIP_REPO_BRANCH = os.getenv("EIP_REPO_BRANCH", "master")
CLONE_REPO = os.getenv("CLONE_REPO", "false").lower() == "true"
GIT_COMMIT_CHANGES = os.getenv("GIT_COMMIT_CHANGES", "false").lower() == "true"

# EIP Review settings
MIN_SCORE_TO_ACCEPT = float(os.getenv("MIN_SCORE_TO_ACCEPT", "0.7"))
MIN_SCORE_TO_CONSIDER = float(os.getenv("MIN_SCORE_TO_CONSIDER", "0.4"))

# Ethereum Core Development settings
ETHEREUM_CLIENTS = os.getenv("ETHEREUM_CLIENTS", "geth,erigon,nethermind,besu").split(",")
PROTOCOL_DEVELOPMENT_ENABLED = os.getenv("PROTOCOL_DEVELOPMENT_ENABLED", "true").lower() == "true"
PROTOCOL_NAME = os.getenv("PROTOCOL_NAME", "Ethereum")
CHAIN_ID = int(os.getenv("CHAIN_ID", "1"))
NUM_CORE_DEVS = int(os.getenv("NUM_CORE_DEVS", "3"))
NUM_REVIEWERS = int(os.getenv("NUM_REVIEWERS", "2"))
GOVERNANCE_MODEL = os.getenv("GOVERNANCE_MODEL", "eip")  # Options: eip, dao, l2
AUTO_SUBMIT_PROPOSALS = os.getenv("AUTO_SUBMIT_PROPOSALS", "false").lower() == "true"

# Layer 2 settings
L2_CHAINS = os.getenv("L2_CHAINS", "optimism,arbitrum,polygon,base,zksync").split(",")
L2_ENABLED = os.getenv("L2_ENABLED", "false").lower() == "true"
L2_NAME = os.getenv("L2_NAME", "")
L2_CHAIN_ID = int(os.getenv("L2_CHAIN_ID", "0"))

# DAO settings
DAO_FRAMEWORKS = os.getenv("DAO_FRAMEWORKS", "aragon,daohaus,colony,snapshot").split(",")
DAO_ENABLED = os.getenv("DAO_ENABLED", "false").lower() == "true"
DAO_NAME = os.getenv("DAO_NAME", "")
DAO_FRAMEWORK = os.getenv("DAO_FRAMEWORK", "aragon")

# MCP servers configuration
MCP_SERVERS = {
    "github": {
        "module": "src.common.mcp_integration",
        "class": "GitHubMCPServer",
        "host": MCP_HOST,
        "port": MCP_PORT_BASE,
        "enabled": MCP_ENABLED,
    },
    "eip_repository": {
        "module": "src.servers.eip_repository_server",
        "class": "app",
        "host": MCP_HOST,
        "port": MCP_PORT_BASE + 1,
        "enabled": MCP_ENABLED,
    },
    "ethereum_validator": {
        "module": "src.servers.ethereum_validator_server",
        "class": "app",
        "host": MCP_HOST,
        "port": MCP_PORT_BASE + 2,
        "enabled": MCP_ENABLED,
    },
    "ethereum_client": {
        "module": "src.servers.ethereum_client_mcp_server",
        "class": "app",
        "host": MCP_HOST,
        "port": MCP_PORT_BASE + 3,
        "enabled": PROTOCOL_DEVELOPMENT_ENABLED,
    }
}

# Protocol Development Workflow configuration
PROTOCOL_DEV_WORKFLOW = {
    "protocol_name": PROTOCOL_NAME,
    "chain_id": CHAIN_ID,
    "num_core_devs": NUM_CORE_DEVS,
    "num_reviewers": NUM_REVIEWERS,
    "governance_model": GOVERNANCE_MODEL,
    "mcp_servers": list(MCP_SERVERS.keys()),
    "github_repo": f"{GITHUB_OWNER}/{GITHUB_REPOS[0]}",
    "auto_submit": AUTO_SUBMIT_PROPOSALS,
    "verbose": LOG_LEVEL.lower() == "debug",
}

# L2 Workflow configuration
L2_DEV_WORKFLOW = {
    "protocol_name": L2_NAME,
    "chain_id": L2_CHAIN_ID,
    "num_core_devs": NUM_CORE_DEVS,
    "num_reviewers": NUM_REVIEWERS,
    "governance_model": "dao" if L2_NAME.lower() in ["optimism", "arbitrum"] else "l2",
    "mcp_servers": list(MCP_SERVERS.keys()),
    "github_repo": f"{L2_NAME.lower()}/governance" if L2_NAME else "",
    "auto_submit": AUTO_SUBMIT_PROPOSALS,
    "verbose": LOG_LEVEL.lower() == "debug",
}

# DAO Workflow configuration
DAO_DEV_WORKFLOW = {
    "protocol_name": DAO_NAME,
    "chain_id": CHAIN_ID,  # Assuming DAO is on Ethereum mainnet by default
    "num_core_devs": 2,  # Fewer core devs for DAOs
    "num_reviewers": 3,  # More reviewers for DAOs (community-focused)
    "governance_model": "dao",
    "mcp_servers": list(MCP_SERVERS.keys()),
    "github_repo": f"{DAO_NAME.lower()}/governance" if DAO_NAME else "",
    "auto_submit": AUTO_SUBMIT_PROPOSALS,
    "verbose": LOG_LEVEL.lower() == "debug",
    "dao_framework": DAO_FRAMEWORK,
}

# Combine all settings in a single dictionary for easy access
settings = {
    "base_dir": str(BASE_DIR),
    "src_dir": str(SRC_DIR),
    "data_dir": str(DATA_DIR),
    "logs_dir": str(LOGS_DIR),
    "output_dir": str(OUTPUT_DIR),
    "tmp_dir": str(TMP_DIR),
    "github": {
        "token": GITHUB_TOKEN,
        "owner": GITHUB_OWNER,
        "repos": GITHUB_REPOS,
        "issue_polling_interval": ISSUE_POLLING_INTERVAL,
    },
    "logging": {
        "level": LOG_LEVEL,
        "format": LOG_FORMAT,
        "file": LOG_FILE,
    },
    "agent": {
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "model_name": MODEL_NAME,
        "mock_agent": MOCK_AGENT,
    },
    "mock": {
        "use_mock_data": USE_MOCK_DATA,
        "use_mock_issues": USE_MOCK_ISSUES,
        "use_mock_eips": USE_MOCK_EIPS,
    },
    "mcp": {
        "enabled": MCP_ENABLED,
        "mock_enabled": MCP_MOCK_ENABLED,
        "host": MCP_HOST,
        "port_base": MCP_PORT_BASE,
        "debug": MCP_DEBUG,
        "servers": MCP_SERVERS,
    },
    "dashboard": {
        "host": DASHBOARD_HOST,
        "port": DASHBOARD_PORT,
        "debug": DASHBOARD_DEBUG,
    },
    "eip_repository": {
        "eip_dir": EIP_DIR,
        "repo_url": EIP_REPO_URL,
        "branch": EIP_REPO_BRANCH,
        "clone_repo": CLONE_REPO,
        "git_commit_changes": GIT_COMMIT_CHANGES,
    },
    "eip_review": {
        "min_score_to_accept": MIN_SCORE_TO_ACCEPT,
        "min_score_to_consider": MIN_SCORE_TO_CONSIDER,
    },
    "ethereum": {
        "clients": ETHEREUM_CLIENTS,
        "protocol_development_enabled": PROTOCOL_DEVELOPMENT_ENABLED,
        "protocol_name": PROTOCOL_NAME,
        "chain_id": CHAIN_ID,
        "num_core_devs": NUM_CORE_DEVS,
        "num_reviewers": NUM_REVIEWERS,
        "governance_model": GOVERNANCE_MODEL,
    },
    "l2": {
        "chains": L2_CHAINS,
        "enabled": L2_ENABLED,
        "name": L2_NAME,
        "chain_id": L2_CHAIN_ID,
    },
    "dao": {
        "frameworks": DAO_FRAMEWORKS,
        "enabled": DAO_ENABLED,
        "name": DAO_NAME,
        "framework": DAO_FRAMEWORK,
    },
    "workflow": {
        "protocol_dev": PROTOCOL_DEV_WORKFLOW,
        "l2_dev": L2_DEV_WORKFLOW,
        "dao_dev": DAO_DEV_WORKFLOW,
    }
}

# Create directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR, OUTPUT_DIR, TMP_DIR]:
    directory.mkdir(exist_ok=True)

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ]
)


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Configuration settings for the Kephra agent system."""

    # Basic configuration
    log_level: str = Field(default="INFO")
    environment: Environment = Field(default=Environment.DEVELOPMENT)

    # API Keys
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    github_token: str = Field(default="")  # Added for GitHub MCP server

    # Agent settings
    default_agent_model: str = Field(default="gpt-4o")
    max_tokens: int = Field(default=8192)
    temperature: float = Field(default=0.2)

    # MCP Configuration
    mcp_enabled: bool = Field(default=True)
    mcp_port: int = Field(default=8080)
    mcp_host: str = Field(default="localhost")
    mcp_transport_type: str = Field(default="stdio")  # "stdio" or "http"
    mcp_server_path: Optional[str] = Field(default=None)  # Path to MCP server executable
    mcp_registry_url: Optional[str] = Field(default=None)  # URL for MCP registry when available
    mcp_servers_dir: Optional[str] = Field(default="./mcp_servers")  # Directory for local MCP servers
    
    # New MCP Server Management Settings
    auto_start_mcp_servers: bool = Field(default=True)  # Whether to automatically start MCP servers
    mcp_server_configs: Optional[Dict[str, Dict[str, Any]]] = Field(default=None)  # Custom server configurations
    
    # GitHub MCP Configuration
    github_owner: str = Field(default="ethereum")  # Default GitHub organization for monitoring
    github_repos: List[str] = Field(default=["EIPs"])  # Default repos to monitor
    
    # Filesystem MCP Configuration
    filesystem_path: Optional[str] = Field(default="./workspace")  # Path for filesystem access
    
    # Git MCP Configuration
    eip_repository_path: Optional[str] = Field(default="./eip_repo")  # Path to local EIP repository

    # Autonomous Workflow Configuration
    autonomous_mode: bool = Field(default=False)  # Whether to run in autonomous mode
    issue_polling_interval: int = Field(default=300)  # Seconds between GitHub issue checks
    auto_eip_generation: bool = Field(default=False)  # Whether to automatically generate EIPs
    auto_implementation: bool = Field(default=False)  # Whether to automatically implement code
    auto_submit_eips: bool = Field(default=False)  # Whether to automatically submit generated EIPs to repository
    consensus_threshold: float = Field(default=0.7)  # Threshold for consensus approval

    # Database Configuration
    database_url: str = Field(default="sqlite:///kephra.db")

    # Ethereum Configuration
    eth_node_url: Optional[str] = Field(default=None)
    eth_chain_id: int = Field(default=1)  # Mainnet by default

    # ChaosChain Configuration
    chaoschain_node_url: Optional[str] = Field(default="http://localhost:26657")
    chaoschain_api_url: Optional[str] = Field(default="http://localhost:1317")

    class Config:
        """Pydantic settings configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_prefix = ""  # No prefix
        extra = "ignore"


# Instantiate settings
settings = Settings()


def get_settings() -> Settings:
    """Return settings instance for dependency injection."""
    return settings 