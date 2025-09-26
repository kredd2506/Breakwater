# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains the **NRP K8s System** - an intelligent routing and management system that combines NRP (National Research Platform) LLM capabilities with Kubernetes operations. The system analyzes user intent and routes requests to appropriate handlers for either K8s operational commands or documentation/explanation queries.

## Project Structure

```
breakwater/
├── nrp_k8s_system/           # Main Python package
│   ├── __init__.py
│   ├── intelligent_router.py # Main routing logic with intent classification  
│   ├── cli.py                # CLI entry point
│   ├── core/                 # Core utilities
│   │   ├── __init__.py
│   │   └── nrp_init.py       # NRP LLM initialization
│   ├── systems/              # System components
│   │   ├── __init__.py
│   │   ├── k8s_operations.py # Kubernetes operations using Python client
│   │   └── qain.py           # Information extraction (optional)
│   ├── cache/                # Runtime cache directory
│   ├── config/               # Configuration templates
│   ├── requirements.txt      # Python dependencies
│   └── pyproject.toml        # Package configuration
└── README.md                 # Project documentation
```

## Development Commands

### Installation and Setup
```bash
cd nrp_k8s_system
pip install -r requirements.txt
# Or install as editable package
pip install -e .
```

### Running the System
```bash
# Single command mode
python -m nrp_k8s_system.intelligent_router "list my pods"
python -m nrp_k8s_system.intelligent_router "How do I request GPUs?"

# Interactive mode
python -m nrp_k8s_system.intelligent_router

# Using installed entry points
nrp-k8s "list pods"
intelligent-router
```

### Testing and Development
```bash
# Run direct test
python nrp_k8s_system/test_installation.py

# Code formatting (when available)
black nrp_k8s_system/
```

### Optional Development Dependencies
```bash
pip install -e ".[dev]"  # Includes pytest, black, flake8, mypy
```

## Core Architecture

### Intelligent Router (intelligent_router.py)
- **Intent Classification**: Uses NRP LLM to analyze user input and classify as COMMAND, EXPLANATION, or UNCLEAR
- **Command Handler**: Routes K8s operations to `k8s_operations.py` 
- **Explanation Handler**: Provides comprehensive guidance using NRP LLM with contextual examples
- **Smart Fallback**: Keyword-based classification when LLM fails

### K8s Operations (systems/k8s_operations.py) 
- Direct Kubernetes Python client integration
- ReAct (Reasoning + Acting) agent pattern for natural language K8s interactions
- Supports: list, describe, get operations for pods, services, deployments, jobs, etc.
- Operates in 'gsoc' namespace by default
- Includes permission checking and error handling

### NRP Integration (core/nrp_init.py)
- Initializes NRP LLM client with environment-based configuration
- Supports gemma3 model via https://llm.nrp-nautilus.io/
- Fallback to OpenAI client if configured

## Environment Configuration

Required environment variables (create `.env` file):
```bash
NRP_API_KEY=your_nrp_api_key_here
NRP_BASE_URL=https://llm.nrp-nautilus.io/
NRP_MODEL=gemma3
```

Optional:
```bash
OPENAI_API_KEY=fallback_openai_key
OPENAI_BASE_URL=openai_endpoint
```

## Key Dependencies

- `langchain-openai` - NRP LLM integration
- `kubernetes` - K8s cluster operations  
- `python-dotenv` - Environment configuration
- `openai` - Alternative LLM client
- `pydantic` - Data validation
- `requests`, `beautifulsoup4` - Web scraping capabilities

## Development Notes

- The system assumes operation within or connected to an NRP Kubernetes cluster
- Default namespace is 'gsoc'
- Uses both in-cluster and local kubectl configurations
- Intent classification falls back to keyword matching if LLM fails
- Modular architecture allows easy extension of handlers and operations
- Type hints used throughout for better IDE support

## Entry Points

The package provides two CLI entry points:
- `nrp-k8s` - Main CLI entry via cli.py
- `intelligent-router` - Direct access to router functionality

## Cache and Persistence

- Runtime cache stored in `nrp_k8s_system/cache/`
- Isolated caches per component to avoid corruption
- 15-minute self-cleaning cache for web fetch operations