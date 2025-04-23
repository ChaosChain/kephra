#!/usr/bin/env python
"""
Setup script for Kephra MCP servers.

This script initializes the project directory structure and downloads
the required MCP servers from the modelcontextprotocol/servers repository.
"""

import os
import sys
import subprocess
import shutil
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# MCP Server definitions
MCP_SERVERS = {
    "github": {
        "type": "npm",
        "package": "@modelcontextprotocol/server-github",
        "version": "latest"
    },
    "filesystem": {
        "type": "npm",
        "package": "@modelcontextprotocol/server-filesystem",
        "version": "latest"
    },
    "git": {
        "type": "pip",
        "package": "mcp-server-git",
        "version": "latest"
    }
}

# Directory structure
DIRECTORIES = [
    "mcp_servers",
    "workspace",
    "eip_repo",
    "src/servers"
]


def check_prerequisites():
    """Check if the required tools are installed."""
    prerequisites_met = True
    
    # Check Node.js
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        node_version = result.stdout.strip()
        logger.info(f"Node.js: {node_version}")
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("Node.js is not installed or not in PATH")
        prerequisites_met = False
    
    # Check npm
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        npm_version = result.stdout.strip()
        logger.info(f"npm: {npm_version}")
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("npm is not installed or not in PATH")
        prerequisites_met = False
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    logger.info(f"Python: {python_version}")
    
    # Check pip
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        pip_version = result.stdout.strip()
        logger.info(f"pip: {pip_version}")
    except subprocess.SubprocessError:
        logger.error("pip is not installed")
        prerequisites_met = False
    
    return prerequisites_met


def create_directory_structure():
    """Create the necessary directory structure."""
    logger.info("Creating directory structure...")
    
    for directory in DIRECTORIES:
        directory_path = Path(directory)
        if not directory_path.exists():
            logger.info(f"Creating directory: {directory}")
            directory_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("Directory structure created.")


def install_mcp_servers():
    """Install the required MCP servers."""
    logger.info("Installing MCP servers...")
    
    for server_name, server_info in MCP_SERVERS.items():
        logger.info(f"Installing {server_name} MCP server...")
        
        if server_info["type"] == "npm":
            try:
                # Install npm package
                package_spec = f"{server_info['package']}@{server_info['version']}"
                cmd = ["npm", "install", "-g", package_spec]
                
                logger.info(f"Running: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info(f"Successfully installed {server_name} MCP server")
            except subprocess.SubprocessError as e:
                logger.error(f"Error installing {server_name} MCP server: {str(e)}")
                logger.error(f"stderr: {e.stderr if hasattr(e, 'stderr') else ''}")
                continue
        
        elif server_info["type"] == "pip":
            try:
                # Install pip package
                package_spec = f"{server_info['package']}"
                if server_info["version"] != "latest":
                    package_spec += f"=={server_info['version']}"
                
                cmd = [sys.executable, "-m", "pip", "install", package_spec]
                
                logger.info(f"Running: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info(f"Successfully installed {server_name} MCP server")
            except subprocess.SubprocessError as e:
                logger.error(f"Error installing {server_name} MCP server: {str(e)}")
                logger.error(f"stderr: {e.stderr if hasattr(e, 'stderr') else ''}")
                continue
    
    logger.info("MCP servers installation completed.")


def initialize_git_repo():
    """Initialize the Git repository for EIPs."""
    logger.info("Initializing EIP Git repository...")
    
    eip_repo_path = Path("eip_repo")
    
    if not eip_repo_path.exists():
        eip_repo_path.mkdir(parents=True, exist_ok=True)
    
    # Check if it's already a git repo
    git_dir = eip_repo_path / ".git"
    if git_dir.exists():
        logger.info("EIP repository is already initialized.")
        return
    
    try:
        # Initialize git repo
        cmd = ["git", "init"]
        subprocess.run(
            cmd,
            cwd=str(eip_repo_path),
            capture_output=True,
            text=True,
            check=True
        )
        
        # Clone ethereum/EIPs if possible
        try:
            # First clean the directory (except .git)
            for item in eip_repo_path.iterdir():
                if item.name != ".git":
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            
            # Clone the content (not the repo itself)
            cmd = ["git", "clone", "--depth", "1", "https://github.com/ethereum/EIPs.git", "."]
            subprocess.run(
                cmd,
                cwd=str(eip_repo_path),
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Successfully cloned ethereum/EIPs repository.")
        except subprocess.SubprocessError as e:
            logger.warning(f"Could not clone ethereum/EIPs repository: {str(e)}")
            logger.warning("Creating basic structure instead.")
            
            # Create basic structure
            (eip_repo_path / "EIPS").mkdir(exist_ok=True)
            (eip_repo_path / "assets").mkdir(exist_ok=True)
            
            # Create README
            with open(eip_repo_path / "README.md", "w") as f:
                f.write("# Ethereum Improvement Proposals (EIPs)\n\nLocal repository for EIPs managed by Kephra.\n")
    
    except subprocess.SubprocessError as e:
        logger.error(f"Error initializing git repository: {str(e)}")


def create_env_file():
    """Create a .env file with default settings."""
    logger.info("Creating .env file...")
    
    env_path = Path(".env")
    
    # Don't overwrite existing .env file
    if env_path.exists():
        logger.info(".env file already exists. Skipping.")
        return
    
    env_content = """# Kephra Configuration
LOG_LEVEL=INFO
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GITHUB_TOKEN=

# MCP Configuration
MCP_ENABLED=true
MCP_PORT=8080
AUTO_START_MCP_SERVERS=true

# Autonomous Workflow Configuration
AUTONOMOUS_MODE=false
ISSUE_POLLING_INTERVAL=300
AUTO_EIP_GENERATION=false
AUTO_IMPLEMENTATION=false

# GitHub Configuration
GITHUB_OWNER=ethereum
GITHUB_REPOS=["EIPs"]

# Filesystem Configuration
FILESYSTEM_PATH=./workspace
EIP_REPOSITORY_PATH=./eip_repo
"""
    
    with open(env_path, "w") as f:
        f.write(env_content)
    
    logger.info(".env file created.")


def create_custom_servers():
    """Create custom MCP server implementation files."""
    logger.info("Creating custom MCP server implementations...")
    
    # EIP Repository Server
    eip_repo_server_path = Path("src/servers/eip_repository_server.py")
    if not eip_repo_server_path.exists():
        eip_repo_server_content = """\"\"\"
EIP Repository MCP Server.

This server provides access to the local EIP repository.
\"\"\"

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="EIP Repository MCP Server")

# Repository path
EIP_REPO_PATH = os.environ.get("EIP_REPOSITORY_PATH", "./eip_repo")


class EIP(BaseModel):
    \"\"\"EIP model.\"\"\"
    
    eip_id: str
    title: str
    author: str
    status: str
    type: str
    created: str
    content: str


@app.get("/")
def read_root():
    \"\"\"Root endpoint.\"\"\"
    return {"name": "EIP Repository MCP Server", "status": "running"}


@app.get("/eips")
def list_eips():
    \"\"\"List all EIPs in the repository.\"\"\"
    try:
        eips_dir = Path(EIP_REPO_PATH) / "EIPS"
        if not eips_dir.exists():
            return {"eips": []}
        
        eips = []
        for eip_file in eips_dir.glob("eip-*.md"):
            eip_id = eip_file.stem.upper()
            eips.append({
                "eip_id": eip_id,
                "file_path": str(eip_file.relative_to(Path(EIP_REPO_PATH)))
            })
        
        return {"eips": eips}
    except Exception as e:
        logger.error(f"Error listing EIPs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/eips/{eip_id}")
def get_eip(eip_id: str):
    \"\"\"Get a specific EIP by ID.\"\"\"
    try:
        # Normalize EIP ID
        eip_id = eip_id.upper()
        if eip_id.startswith("EIP-"):
            eip_id = eip_id
        elif eip_id.isdigit():
            eip_id = f"EIP-{eip_id}"
        
        # Find the EIP file
        eip_file = Path(EIP_REPO_PATH) / "EIPS" / f"{eip_id.lower()}.md"
        if not eip_file.exists():
            raise HTTPException(status_code=404, detail=f"EIP {eip_id} not found")
        
        # Read the EIP content
        with open(eip_file, "r") as f:
            content = f.read()
        
        # Parse basic metadata
        metadata = {}
        in_header = False
        header_lines = []
        
        for line in content.split("\\n"):
            if line.strip() == "---" and not in_header:
                in_header = True
                continue
            elif line.strip() == "---" and in_header:
                in_header = False
                break
            
            if in_header:
                header_lines.append(line)
        
        for line in header_lines:
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip().lower()] = value.strip()
        
        # Create EIP object
        eip = {
            "eip_id": eip_id,
            "title": metadata.get("title", "Unknown"),
            "author": metadata.get("author", "Unknown"),
            "status": metadata.get("status", "Unknown"),
            "type": metadata.get("type", "Unknown"),
            "created": metadata.get("created", "Unknown"),
            "content": content
        }
        
        return eip
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting EIP {eip_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/eips")
def create_eip(eip: Dict[str, Any]):
    \"\"\"Create a new EIP.\"\"\"
    try:
        # Validate EIP data
        if "eip_id" not in eip:
            raise HTTPException(status_code=400, detail="EIP ID is required")
        
        eip_id = eip["eip_id"].upper()
        if not eip_id.startswith("EIP-"):
            eip_id = f"EIP-{eip_id}"
        
        # Check if EIP already exists
        eip_file = Path(EIP_REPO_PATH) / "EIPS" / f"{eip_id.lower()}.md"
        if eip_file.exists():
            raise HTTPException(status_code=409, detail=f"EIP {eip_id} already exists")
        
        # Ensure directory exists
        eip_dir = Path(EIP_REPO_PATH) / "EIPS"
        eip_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate EIP content
        title = eip.get("title", "Untitled EIP")
        author = eip.get("author", "Unknown")
        status = eip.get("status", "Draft")
        eip_type = eip.get("type", "Standards Track")
        created = eip.get("created", "Unknown")
        
        content = f\"\"\"---
eip: {eip_id.replace("EIP-", "")}
title: {title}
author: {author}
status: {status}
type: {eip_type}
created: {created}
---

## Abstract

{eip.get("abstract", "Abstract goes here.")}

## Motivation

{eip.get("motivation", "Motivation goes here.")}

## Specification

{eip.get("specification", "Specification goes here.")}

## Rationale

{eip.get("rationale", "Rationale goes here.")}

## Implementation

{eip.get("implementation", "Implementation goes here.")}
\"\"\"
        
        # Write EIP file
        with open(eip_file, "w") as f:
            f.write(content)
        
        # Commit to git if available
        try:
            import subprocess
            
            # Add to git
            subprocess.run(
                ["git", "add", str(eip_file.relative_to(Path(EIP_REPO_PATH)))],
                cwd=EIP_REPO_PATH,
                check=True
            )
            
            # Commit
            subprocess.run(
                ["git", "commit", "-m", f"Add {eip_id}: {title}"],
                cwd=EIP_REPO_PATH,
                check=True
            )
            
            logger.info(f"Committed {eip_id} to git repository")
        except Exception as e:
            logger.warning(f"Could not commit {eip_id} to git: {str(e)}")
        
        return {"status": "success", "eip_id": eip_id, "file_path": str(eip_file)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating EIP: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    \"\"\"Run the EIP Repository MCP Server.\"\"\"
    port = int(os.environ.get("PORT", 8083))
    logger.info(f"Starting EIP Repository MCP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
"""
        
        with open(eip_repo_server_path, "w") as f:
            f.write(eip_repo_server_content)
        
        logger.info("Created EIP Repository MCP Server implementation.")
    
    # Ethereum Validator Server
    eth_validator_server_path = Path("src/servers/ethereum_validator_server.py")
    if not eth_validator_server_path.exists():
        eth_validator_server_content = """\"\"\"
Ethereum Validator MCP Server.

This server provides validation services for Ethereum code, including
Solidity smart contracts, EVM bytecode, and protocol implementations.
\"\"\"

import os
import sys
import json
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import uvicorn

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Ethereum Validator MCP Server")


@app.get("/")
def read_root():
    \"\"\"Root endpoint.\"\"\"
    return {"name": "Ethereum Validator MCP Server", "status": "running"}


@app.post("/validate/solidity")
async def validate_solidity(solidity_code: str):
    \"\"\"Validate Solidity code using solc.\"\"\"
    try:
        # Check if solc is installed
        try:
            subprocess.run(["solc", "--version"], capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            return {
                "status": "error",
                "message": "Solidity compiler (solc) not found. Please install it."
            }
        
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(suffix=".sol", delete=False) as temp_file:
            temp_file.write(solidity_code.encode())
            temp_file_path = temp_file.name
        
        try:
            # Validate using solc
            result = subprocess.run(
                ["solc", "--optimize", temp_file_path],
                capture_output=True,
                text=True,
                check=False  # Don't raise an exception on error
            )
            
            # Check for errors
            if result.returncode != 0:
                return {
                    "status": "error",
                    "message": "Solidity compilation failed",
                    "errors": result.stderr
                }
            
            # Success
            return {
                "status": "success",
                "message": "Solidity code is valid",
                "output": result.stdout
            }
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
    except Exception as e:
        logger.error(f"Error validating Solidity code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate/evm")
async def validate_evm(bytecode: str):
    \"\"\"Validate EVM bytecode.\"\"\"
    try:
        # Simple validation - check if it's a valid hex string
        try:
            # Strip 0x prefix if present
            if bytecode.startswith("0x"):
                bytecode = bytecode[2:]
            
            # Check if it's a valid hex string
            int(bytecode, 16)
            
            # Check if length is even (each byte is 2 hex chars)
            if len(bytecode) % 2 != 0:
                return {
                    "status": "error",
                    "message": "Invalid bytecode length (must be even)"
                }
            
            # Success
            return {
                "status": "success",
                "message": "EVM bytecode is valid",
                "size_bytes": len(bytecode) // 2
            }
        except ValueError:
            return {
                "status": "error",
                "message": "Invalid bytecode format (must be hexadecimal)"
            }
    except Exception as e:
        logger.error(f"Error validating EVM bytecode: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate/gas")
async def simulate_gas(bytecode: str):
    \"\"\"Simulate gas usage for EVM bytecode.\"\"\"
    try:
        # This is a simplified simulation
        # In a real implementation, this would use an EVM implementation
        
        # Strip 0x prefix if present
        if bytecode.startswith("0x"):
            bytecode = bytecode[2:]
        
        try:
            # Check if it's a valid hex string
            int(bytecode, 16)
        except ValueError:
            return {
                "status": "error",
                "message": "Invalid bytecode format (must be hexadecimal)"
            }
        
        # Simplified gas calculation
        # In reality, this would execute the bytecode in an EVM implementation
        bytecode_bytes = bytearray.fromhex(bytecode)
        
        # Very simple gas calculation based on bytecode length
        # This is not accurate for real gas calculation
        gas_estimate = len(bytecode_bytes) * 2
        
        return {
            "status": "success",
            "gas_estimate": gas_estimate,
            "code_size_bytes": len(bytecode_bytes)
        }
    except Exception as e:
        logger.error(f"Error simulating gas usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    \"\"\"Run the Ethereum Validator MCP Server.\"\"\"
    port = int(os.environ.get("PORT", 8084))
    logger.info(f"Starting Ethereum Validator MCP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
"""
        
        with open(eth_validator_server_path, "w") as f:
            f.write(eth_validator_server_content)
        
        logger.info("Created Ethereum Validator MCP Server implementation.")
    
    # Create __init__.py in servers directory
    servers_init_path = Path("src/servers/__init__.py")
    if not servers_init_path.exists():
        with open(servers_init_path, "w") as f:
            f.write("""\"\"\"
Custom MCP Servers for Kephra.

This package contains custom MCP server implementations for
the Kephra autonomous agent system.
\"\"\"

__all__ = ["eip_repository_server", "ethereum_validator_server"]
""")
        
        logger.info("Created servers package __init__.py.")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Setup script for Kephra MCP servers"
    )
    
    parser.add_argument(
        "--install-only",
        action="store_true",
        help="Only install MCP servers, skip other setup steps"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    logger.info("Starting Kephra MCP servers setup...")
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("Prerequisites not met. Please install the required tools.")
        return 1
    
    if not args.install_only:
        # Create directory structure
        create_directory_structure()
        
        # Initialize git repository
        initialize_git_repo()
        
        # Create .env file
        create_env_file()
        
        # Create custom servers
        create_custom_servers()
    
    # Install MCP servers
    install_mcp_servers()
    
    logger.info("Setup completed successfully!")
    logger.info("To start using Kephra with MCP, run:")
    logger.info("python -m src.main --autonomous")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 