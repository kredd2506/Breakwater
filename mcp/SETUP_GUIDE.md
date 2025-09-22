# Ultimate FastMCP Server Setup Guide

## Complete Setup Instructions for the Integrated K8s + FastMCP Server

### Prerequisites

1. **Python 3.8+** installed
2. **Git** installed
3. **NRP API access** (optional - will work in demo mode without it)

### Step 1: Clone and Navigate to Project

```bash
git clone <your-repo-url>
cd breakwater/mcp
```

### Step 2: Install Dependencies

```bash
# Install FastMCP and required packages
pip install fastmcp
pip install kubernetes
pip install langchain-openai
pip install python-dotenv
pip install openai
pip install pydantic
pip install requests
pip install beautifulsoup4
```

### Step 3: Environment Configuration (Optional)

Create a `.env` file in the `mcp/` directory:

```bash
# Optional: For full NRP functionality
NRP_API_KEY=your_nrp_api_key_here
NRP_BASE_URL=https://llm.nrp-nautilus.io/
NRP_MODEL=gemma3

# Optional: OpenAI fallback
OPENAI_API_KEY=fallback_openai_key
OPENAI_BASE_URL=openai_endpoint
```

**Note:** The server works in demo mode without these environment variables!

### Step 4: Start the Ultimate FastMCP Server

```bash
cd "D:\Gsoc Gitlab\ocean\breakwater\mcp"
python ultimate_fastmcp_server.py
```

You should see output like:
```
Starting Ultimate FastMCP NRP.ai Server...

Integrated FastMCP Capabilities:
- Advanced Prompts with structured validation
- Context-aware logging, state management, and progress reporting
- Progressive elicitation with multi-turn patterns
- Structured logging with performance and security metadata
- Real-time progress reporting with multiple patterns
- LLM sampling for intelligent text generation and analysis
- Server flags for runtime configuration
- Enhanced error handling and recovery

NEW: Kubernetes Operations & Infogent Architecture:
- K8s resource management (list, describe, create, delete)
- Intelligent natural language K8s queries
- Pod and deployment operations with progress tracking
- Kubernetes logs retrieval and cluster information
- NRP-powered intent classification and routing
- Comprehensive K8s operations with FastMCP integration

K8s Available: True
NRP Chat Available: True/False
Current Namespace: gsoc

Server will be available at: http://127.0.0.1:8022/mcp
```

### Step 5: Test the Server

#### Option A: Quick Test with our Test Client

```bash
# In a new terminal window
cd "D:\Gsoc Gitlab\ocean\breakwater\mcp"
python test_k8s_infogent_integration.py
```

#### Option B: Test Specific Questions

```bash
# Test Nautilus-specific questions
python test_nautilus_question.py
```

#### Option C: Test Individual Capabilities

```bash
# Test just the LLM sampling fixes
python test_sampling_fixes.py
```

### Step 6: Available Tools and Capabilities

The Ultimate FastMCP Server provides **14 tools total**:

#### K8s Operations (8 tools):
- `k8s_list_resources` - List pods, deployments, services, jobs
- `k8s_describe_resource` - Get detailed resource information
- `k8s_create_pod` - Create pods with resource specifications
- `k8s_create_deployment` - Create deployments with replica management
- `k8s_delete_resource` - Delete K8s resources
- `k8s_get_logs` - Retrieve pod logs
- `intelligent_k8s_query` - **Infogent functionality** with NRP-powered intent classification
- `k8s_get_cluster_info` - Get cluster and namespace information

#### FastMCP Concepts (6 tools):
- `ultimate_progressive_elicitation_demo` - Multi-turn elicitation patterns
- `ultimate_llm_sampling_demo` - 5-stage LLM sampling with fallbacks
- `intelligent_configuration_generator` - AI-powered config generation
- `ultimate_server_configuration` - Runtime server configuration
- `ultimate_logging_demonstration` - Structured logging with metadata
- `ultimate_gpu_deployment_with_progress` - GPU deployment with progress tracking

### Step 7: Using the Server

#### Example 1: Ask Nautilus Questions
```python
from fastmcp import Client

async def ask_question():
    client = Client("http://localhost:8022/mcp")
    async with client:
        result = await client.call_tool("intelligent_k8s_query", {
            "params": {
                "query": "Should users run sleep in batch jobs on Nautilus, or optimize for short runtime?",
                "context": "Nautilus cluster best practices"
            }
        })
        print(result.data)
```

#### Example 2: List K8s Resources
```python
async def list_pods():
    client = Client("http://localhost:8022/mcp")
    async with client:
        result = await client.call_tool("k8s_list_resources", {
            "resource_type": "pods"
        })
        print(result.data)
```

#### Example 3: Use LLM Sampling
```python
async def sample_llm():
    client = Client("http://localhost:8022/mcp")
    async with client:
        result = await client.call_tool("ultimate_llm_sampling_demo", {
            "sampling_type": "comprehensive",
            "content": "Kubernetes deployment strategies",
            "temperature": 0.7,
            "max_tokens": 500,
            "enable_structured_output": True
        })
        print(result.data)
```

### Troubleshooting

#### Port Already in Use
If you see "port already in use" error:
```bash
# Check what's using port 8022
netstat -ano | findstr :8022

# Kill the process if needed
taskkill /PID <process_id> /F

# Or change the port in ultimate_fastmcp_server.py (line 2299)
```

#### Missing Dependencies
```bash
# Install missing packages
pip install <package_name>

# Or install all at once
pip install fastmcp kubernetes langchain-openai python-dotenv openai pydantic requests beautifulsoup4
```

#### NRP Connection Issues
- Server works in demo mode without NRP credentials
- Check your `.env` file for correct API keys
- Verify NRP API access at https://llm.nrp-nautilus.io/

### Server Features

✅ **All 6 FastMCP Concepts Integrated**
✅ **Complete K8s Operations**
✅ **Infogent Intelligence with Intent Classification**
✅ **NRP-Powered Explanations**
✅ **Fallback Handling for Offline Operation**
✅ **Real-time Progress Tracking**
✅ **Structured Logging with Metadata**
✅ **Context-Aware State Management**

### Demo Mode vs Full Mode

**Demo Mode** (no credentials needed):
- All K8s operations show demo data
- LLM sampling uses fallback responses
- All FastMCP concepts work normally

**Full Mode** (with NRP credentials):
- Real K8s cluster integration (if connected)
- Full NRP-powered LLM responses
- Intelligent explanations and analysis

### Success Indicators

When everything is working correctly, you should see:
- Server starts on http://127.0.0.1:8022/mcp
- Test clients connect successfully
- 14 tools available (8 K8s + 6 FastMCP)
- Intelligent responses to Nautilus questions
- Progress tracking and structured logging

**You now have the Ultimate FastMCP Server with complete K8s infogent integration running! 🎉**