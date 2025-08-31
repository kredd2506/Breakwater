#!/usr/bin/env python3
"""
CLI entry point for NRP K8s System
"""

import sys
from .intelligent_router import main as router_main

def main():
    """Main CLI entry point"""
    router_main()

if __name__ == "__main__":
    main()