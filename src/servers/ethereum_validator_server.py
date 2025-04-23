"""
Ethereum Validator MCP Server.

This server provides validation services for Ethereum code, including
Solidity smart contracts, EVM bytecode, and protocol implementations.
"""

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
    """Root endpoint."""
    return {"name": "Ethereum Validator MCP Server", "status": "running"}


@app.post("/validate/solidity")
async def validate_solidity(solidity_code: str):
    """Validate Solidity code using solc."""
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
    """Validate EVM bytecode."""
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
    """Simulate gas usage for EVM bytecode."""
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
    """Run the Ethereum Validator MCP Server."""
    port = int(os.environ.get("PORT", 8084))
    logger.info(f"Starting Ethereum Validator MCP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
