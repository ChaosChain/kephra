"""
EIP Repository MCP Server.

This server provides access to the local EIP repository.
"""

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
    """EIP model."""
    
    eip_id: str
    title: str
    author: str
    status: str
    type: str
    created: str
    content: str


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"name": "EIP Repository MCP Server", "status": "running"}


@app.get("/eips")
def list_eips():
    """List all EIPs in the repository."""
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
    """Get a specific EIP by ID."""
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
        
        for line in content.split("\n"):
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
    """Create a new EIP."""
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
        
        content = f"""---
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
"""
        
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
    """Run the EIP Repository MCP Server."""
    port = int(os.environ.get("PORT", 8083))
    logger.info(f"Starting EIP Repository MCP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
