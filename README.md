# NRP K8s System 🚀

An intelligent routing and management system that combines NRP (National Research Platform) LLM capabilities with Kubernetes operations. Features both a web-based chat interface and a powerful MCP (Model Context Protocol) server.

## ✨ Features

- 🌐 **Web Chat Interface** - Browser-based chat with NRP DeepSeek-R1 integration
- 🔧 **MCP Server** - FastMCP server with Kubernetes operations and NRP knowledge base
- ☸️ **Kubernetes Operations** - Full K8s resource management and troubleshooting
- 🧠 **Intelligent Routing** - AI-powered intent classification and response routing
- 📚 **NRP Knowledge Base** - Comprehensive documentation and templates
- 🎮 **GPU Support** - A100, A40, RTX series with proper resource specifications
- 📊 **Progress Tracking** - Real-time progress reporting and structured logging

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Git
- Internet connection for package installation

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd breakwater
python setup.py
```

The setup script will:
- ✅ Check Python version
- 📦 Install all dependencies
- 📁 Create necessary directories
- 🔧 Setup environment configuration
- 📄 Create .env file from template

### 2. Start the Servers

**Option A: Both servers at once**
```bash
# Terminal 1 - Web Server (Port 5000)
python start_web_server.py

# Terminal 2 - MCP Server (Port 8020)
python start_mcp_server.py
```

**Option B: Individual servers**
```bash
# Web Server only
python web_chat_server.py

# MCP Server only
cd mcp && python ultimate_fastmcp_server.py
```

### 3. Access the Interfaces

- 🌐 **Web Chat**: http://localhost:5000
- 🔗 **MCP Server**: http://localhost:8020/mcp

## 📋 Project Structure

```
breakwater/
├── 🌐 web_chat_server.py          # Flask web server with chat interface
├── 📄 templates/chat.html         # Web chat interface
├── 🔧 mcp/                        # MCP server and related components
│   ├── ultimate_fastmcp_server.py # Main MCP server
│   ├── cache/                     # NRP knowledge base cache
│   └── docs/                      # Documentation and examples
├── ☸️ nrp_k8s_system/             # Core K8s operations
│   ├── intelligent_router.py     # Main routing logic
│   ├── core/                     # Core utilities
│   └── systems/                  # K8s operations
├── 📦 requirements.txt            # All dependencies
├── 🔧 setup.py                   # Automated setup script
├── 🚀 start_web_server.py        # Web server launcher
├── 🚀 start_mcp_server.py        # MCP server launcher
└── 📄 README.md                  # This file
```

## Components

### Intent Classification
- Uses NRP LLM to analyze user input
- Classifies as COMMAND, EXPLANATION, or UNCLEAR
- Fallback to keyword-based classification if LLM fails

### Command Handler  
- Routes kubectl operations to `k8s_operations.py`
- **Full CRUD Operations**: Create, read, update, delete for pods and deployments
- **List & Inspect**: list, get, describe for pods, services, deployments, jobs, etc.
- **Utility Functions**: logs, exec commands for debugging
- Works in 'gsoc' namespace by default

### Explanation Handler
- Provides comprehensive NRP+K8s guidance
- Generates contextual examples based on user questions  
- Covers GPU requests, storage setup, job scheduling, etc.

## Examples

### K8s Commands

**Listing & Inspection:**
```bash
"list my pods"           → Shows pods in gsoc namespace
"get services"           → Lists services  
"describe pod myapp"     → Pod details
"show deployments"       → Deployment list
"list nodes"             → Cluster nodes
"logs my-pod"            → Pod logs
```

**Resource Creation:**
```bash
"create pod my-app"                    → Creates basic pod
"create pod nginx-pod image=nginx"     → Creates nginx pod
"create deployment web-app"            → Creates basic deployment  
"create deployment api replicas=3"     → Creates deployment with 3 replicas
"deploy nginx image=nginx:latest"      → Creates nginx deployment
```

**Resource Management:**
```bash
"delete pod my-app"         → Deletes pod
"delete deployment web-app" → Deletes deployment
"remove pod nginx-pod"      → Alternative delete syntax
```

**Vague Commands (System interprets intelligently):**
```bash
"make a pod"            → Creates default pod
"deploy something"      → Creates default deployment  
"show my stuff"         → Lists pods
"create nginx"          → Creates nginx pod/deployment
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

1. **New K8s Operations**: Add functions to `systems/k8s_operations.py` and update `KNOWN_ACTIONS` registry
2. **New Intent Types**: Extend `UserIntent` enum and classification logic  
3. **New Handlers**: Create handler functions in `intelligent_router.py`
4. **YAML Templates**: Add new resource templates in `k8s_operations.py` for standardized deployments

### Testing
```bash
# Install development dependencies
pip install -e ".[dev]"

# Test basic functionality
python test_integration.py

# Test specific operations
cd nrp_k8s_system
python intelligent_router.py "list pods"
python intelligent_router.py "create pod test-nginx image=nginx"

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