# NRP K8s System

**Intelligent NRP + Kubernetes routing and management system**

A smart routing system that analyzes user intent and routes requests to appropriate handlers:
- **Command Detection**: Routes kubectl/k8s operational commands to k8s_operations.py  
- **Question/Explanation**: Routes documentation questions to NRP+K8s hybrid system

## Features

- 🤖 **Intelligent Intent Classification**: Uses NRP LLM to determine if user wants to execute commands or get explanations
- ⚡ **Direct K8s Operations**: Execute kubectl commands through Python Kubernetes client
- 📚 **NRP Documentation Integration**: Get comprehensive guidance using NRP LLM with contextual examples
- 🔄 **Smart Fallback**: Handles unclear intents with clarification prompts
- 💬 **Interactive Mode**: Chat interface for continuous interaction
- 🧩 **Modular Architecture**: Clean package structure for easy maintenance and extension

## Quick Start

### Installation

```bash
# Clone or copy the nrp_k8s_system directory
cd nrp_k8s_system

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### Configuration

1. Copy the environment template:
   ```bash
   cp config/default.env .env
   ```

2. Edit `.env` with your NRP credentials:
   ```bash
   NRP_API_KEY=your_nrp_api_key_here
   NRP_BASE_URL=https://llm.nrp-nautilus.io/
   NRP_MODEL=gemma3
   ```

3. Ensure kubectl is configured for your NRP cluster

### Usage

**Single command mode:**
```bash
# K8s operations
python -m nrp_k8s_system.intelligent_router "list my pods"
python -m nrp_k8s_system.intelligent_router "describe pod myapp"

# Documentation/guidance
python -m nrp_k8s_system.intelligent_router "How do I request GPUs?"
python -m nrp_k8s_system.intelligent_router "What are storage best practices?"
```

**Interactive mode:**
```bash
python -m nrp_k8s_system.intelligent_router
```

**Using as installed package:**
```bash
# If installed with pip install -e .
nrp-k8s "list pods"
intelligent-router
```

## Architecture

```
nrp_k8s_system/
├── __init__.py                 # Package initialization
├── intelligent_router.py      # Main routing logic
├── cli.py                     # CLI entry point
├── requirements.txt           # Dependencies
├── pyproject.toml            # Package configuration
├── core/                     # Core utilities
│   ├── __init__.py
│   └── nrp_init.py           # NRP LLM initialization
├── systems/                  # System components
│   ├── __init__.py
│   ├── k8s_operations.py     # Kubernetes operations
│   └── qain.py              # Information extraction (optional)
├── cache/                    # Cache directory
│   └── .gitkeep
└── config/                   # Configuration templates
    └── default.env           # Environment template
```

## Components

### Intent Classification
- Uses NRP LLM to analyze user input
- Classifies as COMMAND, EXPLANATION, or UNCLEAR
- Fallback to keyword-based classification if LLM fails

### Command Handler  
- Routes kubectl operations to `k8s_operations.py`
- Supports: list, get, describe for pods, services, deployments, jobs, etc.
- Works in 'gsoc' namespace by default

### Explanation Handler
- Provides comprehensive NRP+K8s guidance
- Generates contextual examples based on user questions  
- Covers GPU requests, storage setup, job scheduling, etc.

## Examples

### K8s Commands
```bash
"list my pods"           → Shows pods in gsoc namespace
"get services"           → Lists services  
"describe pod myapp"     → Pod details
"show deployments"       → Deployment list
"list nodes"             → Cluster nodes
```

### Documentation Queries
```bash
"How do I request A100 GPUs?"        → GPU allocation guide
"What are storage best practices?"   → Storage documentation  
"How do I run batch jobs?"           → Job scheduling guide
"Explain persistent volumes"         → PV/PVC concepts
```

## Development

### Project Structure
The package follows Python packaging best practices:
- Clean module separation
- Type hints throughout
- Comprehensive error handling
- Modular design for extensibility

### Adding New Features

1. **New K8s Operations**: Add functions to `systems/k8s_operations.py`
2. **New Intent Types**: Extend `UserIntent` enum and classification logic
3. **New Handlers**: Create handler functions in `intelligent_router.py`

### Testing
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests (when available)
pytest

# Code formatting
black nrp_k8s_system/
```

## Dependencies

### Core Dependencies
- `langchain-openai` - NRP LLM integration
- `kubernetes` - K8s cluster operations  
- `python-dotenv` - Environment configuration
- `openai` - Alternative LLM client

### Optional Dependencies
- `requests`, `beautifulsoup4` - Web scraping (for enhanced features)
- `numpy`, `scikit-learn` - Analytics (for advanced features)
- `pydantic` - Data validation

## Configuration

### Environment Variables
- `NRP_API_KEY` - **Required** - Your NRP API key
- `NRP_BASE_URL` - NRP LLM endpoint (default: https://llm.nrp-nautilus.io/)
- `NRP_MODEL` - Model name (default: gemma3)
- `OPENAI_API_KEY` - Fallback OpenAI key
- `OPENAI_BASE_URL` - OpenAI endpoint

### Kubernetes
- Uses your existing kubectl configuration
- Defaults to 'gsoc' namespace
- Supports both in-cluster and local configurations

## Troubleshooting

### Common Issues

1. **"NRP_API_KEY not found"**
   - Ensure `.env` file exists with valid `NRP_API_KEY`
   - Check environment variable is set

2. **"Could not configure Kubernetes client"**
   - Verify kubectl is installed and configured
   - Check cluster connectivity

3. **Import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Verify Python version >= 3.8

4. **Intent classification fails**
   - System falls back to keyword-based classification
   - Check NRP API connectivity

## License

MIT License - see package metadata for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable  
5. Submit a pull request

## Support

For issues and questions:
1. Check this README and troubleshooting section
2. Review the code documentation
3. Open an issue in the project repository