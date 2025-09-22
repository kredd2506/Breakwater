#!/usr/bin/env python3
"""
Main Router Module for NRP K8s System
=====================================

Compatibility layer that delegates to the enhanced agent orchestrator.
"""

from typing import Tuple
from ..agents import route_user_request as agent_route_user_request
from ..agents import interactive_mode as agent_interactive_mode


def route_user_request(user_input: str) -> Tuple[str, bool]:
    """
    Main routing function - delegates to the enhanced agent orchestrator.

    Args:
        user_input: Raw user input string

    Returns:
        Tuple of (response_message, success_flag)
    """
    return agent_route_user_request(user_input)


def interactive_mode():
    """Interactive mode - delegates to the enhanced agent orchestrator."""
    agent_interactive_mode()