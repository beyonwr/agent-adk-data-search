"""
Agents Package

This package contains the agent implementations and tools for the
Data Search Agent system.

The main components are:
- agent.py: Root agent definition
- mcp_server.py: FastMCP server with all tool implementations
- sub_agents/: Specialized sub-agents for different tasks
- utils/: Utility functions for state management, database, etc.
"""

from .agent import root_agent
from . import mcp_server

__all__ = ["root_agent", "mcp_server"]