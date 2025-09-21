#!/usr/bin/env python3
"""
Intelligent NRP + K8s Router - Main Entry Point
===============================================

Simplified main entry point that delegates to the new modular router system.
Maintains backward compatibility while using the refactored components.
"""

import sys
from pathlib import Path

# Handle both direct execution and module execution
try:
    from .routers.main_router import route_user_request, interactive_mode
except ImportError:
    # Direct execution - add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from nrp_k8s_system.routers.main_router import route_user_request, interactive_mode


def main():
    """Main entry point for backward compatibility."""
    if len(sys.argv) > 1:
        # Command line mode
        user_input = " ".join(sys.argv[1:])
        result, success = route_user_request(user_input)
        print(result)
        sys.exit(0 if success else 1)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()