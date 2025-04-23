"""
Base tool implementation for the Kephra system.

This module provides a custom implementation of the BaseTool class
to match the interface expected by other components without requiring
external dependencies.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, Union

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    Abstract base class for all tools in the Kephra system.
    
    This class provides a common interface for all tools, allowing them
    to be used by agents in a consistent way.
    """
    
    name: str
    description: str
    args_schema: Optional[Type[BaseModel]] = None
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        """
        Initialize a tool.
        
        Args:
            name: The tool's name (overrides class attribute if provided)
            description: The tool's description (overrides class attribute if provided)
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
    
    def __call__(self, *args, **kwargs) -> Any:
        """
        Call the tool with the given arguments.
        
        This method validates the input arguments if an args_schema is defined,
        then calls the _run method to execute the tool's functionality.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            The result of the tool's execution
        """
        # Log the tool invocation
        arg_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        logger.debug(f"Calling tool {self.name} with args: {arg_str}")
        
        # Validate arguments if schema is provided
        if self.args_schema and hasattr(self.args_schema, "parse_obj"):
            validated_args = self.args_schema.parse_obj(kwargs)
            # Convert to dict and pass as kwargs
            kwargs = validated_args.dict()
        
        # Call the _run method with the validated arguments
        return self._run(*args, **kwargs)
    
    @abstractmethod
    def _run(self, *args, **kwargs) -> Any:
        """
        Execute the tool's functionality.
        
        This method must be implemented by subclasses to provide the actual
        functionality of the tool.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            The result of the tool's execution
        """
        pass
    
    def __str__(self) -> str:
        """Return a string representation of the tool."""
        return f"{self.name}: {self.description}" 