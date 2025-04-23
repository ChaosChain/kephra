"""
Ethereum-specific tools for working with EIPs, Ethereum code, and simulations.

This module provides specialized tools for parsing EIPs, analyzing Ethereum code,
running simulations, and interacting with Ethereum nodes.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.tools.base_tool import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EIPParserInput(BaseModel):
    """Input schema for the EIP Parser tool."""
    
    eip_content: str = Field(..., description="Raw content of the EIP (typically markdown)")
    eip_id: Optional[str] = Field(None, description="EIP ID if known (e.g., 'EIP-1559')")


class CodeAnalyzerInput(BaseModel):
    """Input schema for the Code Analyzer tool."""
    
    code: str = Field(..., description="The code to analyze")
    file_path: Optional[str] = Field(None, description="File path if available")
    language: str = Field("solidity", description="Programming language (default: solidity)")
    context: Optional[str] = Field(None, description="Additional context about the code")


class EIPParser(BaseTool):
    """
    Tool for parsing and extracting structured information from EIP documents.
    
    This tool takes raw EIP text (typically in markdown format) and extracts
    metadata, specification details, and other structured information.
    """
    
    name: str = "EIP Parser"
    description: str = "Parses EIP documents and extracts structured information"
    args_schema: type[BaseModel] = EIPParserInput
    
    def _run(self, eip_content: str, eip_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse an EIP document and extract structured information.
        
        Args:
            eip_content: Raw content of the EIP
            eip_id: EIP ID if known
            
        Returns:
            Dictionary with structured EIP information
        """
        logger.info(f"Parsing EIP {eip_id or 'unknown'}")
        
        try:
            # Extract basic metadata using regex patterns
            # This is a simplified implementation - a real one would be more robust
            title_match = re.search(r'title:\s*(.+?)(?:\n|$)', eip_content, re.IGNORECASE)
            author_match = re.search(r'author:\s*(.+?)(?:\n|$)', eip_content, re.IGNORECASE)
            status_match = re.search(r'status:\s*(.+?)(?:\n|$)', eip_content, re.IGNORECASE)
            type_match = re.search(r'type:\s*(.+?)(?:\n|$)', eip_content, re.IGNORECASE)
            category_match = re.search(r'category:\s*(.+?)(?:\n|$)', eip_content, re.IGNORECASE)
            created_match = re.search(r'created:\s*(.+?)(?:\n|$)', eip_content, re.IGNORECASE)
            
            # Extract EIP number if not provided
            if not eip_id:
                eip_match = re.search(r'EIP[:\s-]*(\d+)', eip_content, re.IGNORECASE)
                if eip_match:
                    eip_id = f"EIP-{eip_match.group(1)}"
            
            # Get the specification section
            spec_match = re.search(r'## Specification\s+(.+?)(?=##|\Z)', eip_content, re.DOTALL | re.IGNORECASE)
            specification = spec_match.group(1).strip() if spec_match else ""
            
            # Get the abstract/summary
            abstract_match = re.search(r'## Abstract\s+(.+?)(?=##|\Z)', eip_content, re.DOTALL | re.IGNORECASE)
            if not abstract_match:
                abstract_match = re.search(r'## Simple Summary\s+(.+?)(?=##|\Z)', eip_content, re.DOTALL | re.IGNORECASE)
            description = abstract_match.group(1).strip() if abstract_match else ""
            
            # Extract code examples if any
            code_blocks = re.findall(r'```(\w*)\n(.*?)```', eip_content, re.DOTALL)
            code_examples = [{"language": lang or "text", "code": code.strip()} for lang, code in code_blocks]
            
            # Construct the result
            result = {
                "proposal_id": eip_id or "Unknown",
                "title": title_match.group(1).strip() if title_match else "Unknown",
                "author": author_match.group(1).strip() if author_match else "Unknown",
                "status": status_match.group(1).strip() if status_match else "Unknown",
                "type": type_match.group(1).strip() if type_match else "Unknown",
                "category": category_match.group(1).strip() if category_match else None,
                "created": created_match.group(1).strip() if created_match else str(datetime.now().date()),
                "description": description,
                "specification": specification,
                "code_examples": code_examples,
                "raw_content": eip_content,
                "requires": [],  # Would extract dependencies in a real implementation
                "implementations": []  # Would extract implementations in a real implementation
            }
            
            logger.info(f"Successfully parsed EIP {result['proposal_id']}: {result['title']}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error parsing EIP: {str(e)}")
            # Return a minimal result with the error
            return {
                "proposal_id": eip_id or "Unknown",
                "raw_content": eip_content,
                "error": str(e),
                "partial": True
            }


class CodeAnalyzer(BaseTool):
    """
    Tool for analyzing Ethereum-related code.
    
    This tool analyzes code for potential issues, security vulnerabilities,
    gas efficiency, and alignment with best practices.
    """
    
    name: str = "Code Analyzer"
    description: str = "Analyzes Ethereum code for issues, security vulnerabilities, and best practices"
    args_schema: type[BaseModel] = CodeAnalyzerInput
    
    def _run(
        self, 
        code: str, 
        file_path: Optional[str] = None, 
        language: str = "solidity",
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze code for issues, security vulnerabilities, and best practices.
        
        Args:
            code: The code to analyze
            file_path: Path to the file (if available)
            language: Programming language of the code
            context: Additional context about the code
            
        Returns:
            Analysis results
        """
        logger.info(f"Analyzing {language} code{f' in {file_path}' if file_path else ''}")
        
        try:
            # This is a simplified implementation
            # In a real system, this would use specialized code analysis tools
            # or LLM-based analysis with appropriate prompting
            
            # For demonstration purposes, we'll just do some basic pattern matching
            issues = []
            highlights = []
            
            # Check for common issues in Solidity code
            if language.lower() == "solidity":
                # Check for potential reentrancy
                if "call.value" in code or "call{value:" in code:
                    if not "ReentrancyGuard" in code and not "nonReentrant" in code:
                        issues.append({
                            "severity": "high",
                            "type": "security",
                            "message": "Potential reentrancy vulnerability detected. Consider using ReentrancyGuard.",
                            "line": self._find_line_number(code, "call.value")
                        })
                
                # Check for proper visibility
                if "function " in code and "visibility" not in context:
                    funcs_without_visibility = re.findall(r'function\s+(\w+)\s*\([^)]*\)\s*(?!private|public|internal|external)', code)
                    if funcs_without_visibility:
                        issues.append({
                            "severity": "medium",
                            "type": "best practice",
                            "message": f"Functions without explicit visibility: {', '.join(funcs_without_visibility)}",
                            "line": self._find_line_number(code, f"function {funcs_without_visibility[0]}")
                        })
                
                # Check for unsafe math
                if "pragma solidity <0.8" in code:
                    if "SafeMath" not in code:
                        issues.append({
                            "severity": "medium",
                            "type": "security",
                            "message": "Using Solidity <0.8.0 without SafeMath. Consider upgrading or using SafeMath.",
                            "line": self._find_line_number(code, "pragma solidity")
                        })
                
                # Highlight good patterns
                if "require(" in code or "assert(" in code:
                    highlights.append({
                        "type": "validation",
                        "message": "Input validation present",
                        "positive": True
                    })
            
            # Analysis for EVM bytecode
            elif language.lower() == "evm" or language.lower() == "bytecode":
                # Very simplified bytecode analysis
                if "SLOAD" in code and "SSTORE" in code:
                    highlights.append({
                        "type": "state",
                        "message": "Code interacts with contract storage",
                        "positive": True
                    })
            
            # Analysis for Python (used in some Ethereum tools and tests)
            elif language.lower() == "python":
                if "web3" in code:
                    highlights.append({
                        "type": "tool",
                        "message": "Uses web3.py for Ethereum interaction",
                        "positive": True
                    })
            
            # General analysis
            complexity_score = self._estimate_complexity(code)
            
            # Construct the result
            result = {
                "language": language,
                "file_path": file_path,
                "issues": issues,
                "highlights": highlights,
                "complexity": complexity_score,
                "summary": self._generate_summary(issues, highlights, complexity_score, language),
                "lines_of_code": len(code.split("\n"))
            }
            
            logger.info(f"Code analysis complete: found {len(issues)} issues")
            
            return result
        
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            return {
                "language": language,
                "file_path": file_path,
                "error": str(e),
                "partial": True
            }
    
    def _find_line_number(self, code: str, pattern: str) -> int:
        """Find the first line number where a pattern appears."""
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if pattern in line:
                return i + 1
        return 0
    
    def _estimate_complexity(self, code: str) -> Dict[str, Any]:
        """Estimate code complexity using simple metrics."""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        functions = re.findall(r'function\s+\w+', code)
        loops = len(re.findall(r'for\s*\(|while\s*\(', code))
        conditionals = len(re.findall(r'if\s*\(', code))
        
        # Simple cyclomatic complexity estimate
        cyclomatic = 1 + loops + conditionals
        
        return {
            "cyclomatic_complexity": cyclomatic,
            "function_count": len(functions),
            "non_empty_lines": len(non_empty_lines)
        }
    
    def _generate_summary(
        self, 
        issues: List[Dict[str, Any]], 
        highlights: List[Dict[str, Any]], 
        complexity: Dict[str, Any],
        language: str
    ) -> str:
        """Generate a summary of the analysis."""
        high_severity = sum(1 for issue in issues if issue.get("severity") == "high")
        medium_severity = sum(1 for issue in issues if issue.get("severity") == "medium")
        low_severity = sum(1 for issue in issues if issue.get("severity") == "low")
        
        if high_severity > 0:
            quality = "concerning"
        elif medium_severity > 0:
            quality = "needs improvement"
        elif low_severity > 0:
            quality = "generally good with minor issues"
        else:
            quality = "good"
        
        summary = f"The {language} code is {quality}. "
        
        if issues:
            summary += f"Found {len(issues)} issues: {high_severity} high severity, {medium_severity} medium severity, and {low_severity} low severity. "
        
        if complexity["cyclomatic_complexity"] > 10:
            summary += f"The code has high complexity ({complexity['cyclomatic_complexity']}), which may indicate it's difficult to reason about. "
        
        if highlights:
            summary += f"Positive aspects include: {', '.join(h['message'] for h in highlights)}."
        
        return summary 