# NRP.ai FastMCP Server Collection

A comprehensive collection of FastMCP servers implementing NRP (National Research Platform) integration with advanced features including tools, resources, prompts, context awareness, elicitation, and structured logging.

## 📁 Project Structure

```
mcp/
├── core/                          # Core MCP Components
│   ├── tools/                     # Tool-based servers
│   │   ├── k8s_infogent_server.py        # Kubernetes operations server
│   │   ├── advanced_infogent_server.py   # Enhanced tool operations
│   │   ├── simplified_advanced_server.py # Lightweight tool server
│   │   └── enhanced_server.py            # General enhanced server
│   ├── resources/                 # Resource-based servers
│   │   ├── nrp_resources_server.py       # Basic NRP resources
│   │   ├── enhanced_nrp_resources_server.py # Enhanced resources
│   │   ├── ultimate_nrp_resources_server.py # Ultimate resources
│   │   └── enhanced_ultimate_server.py   # Enhanced ultimate
│   └── prompts/                   # Prompt-based servers
│       ├── nrp_prompts_server.py         # Basic prompts server
│       └── advanced_nrp_prompts_server.py # FastMCP prompts (Port 8010)
├── advanced/                      # Advanced FastMCP Features
│   ├── context/                   # Context-aware capabilities
│   │   └── context_aware_nrp_server.py   # FastMCP context (Port 8011)
│   ├── elicitation/              # Progressive elicitation
│   │   └── elicitation_enhanced_nrp_server.py # FastMCP elicitation (Port 8012)
│   └── logging/                   # Structured logging
│       └── logging_enhanced_nrp_server.py # FastMCP logging (Port 8013)
├── tests/                         # Comprehensive test suites
│   ├── test_advanced_prompts.py          # Prompts testing
│   ├── test_context_aware_server.py      # Context testing
│   ├── test_elicitation_server.py        # Elicitation testing
│   ├── test_logging_server.py            # Logging testing
│   ├── test_enhanced_resources.py        # Resources testing
│   ├── test_nrp_prompts.py              # NRP prompts testing
│   ├── test_nrp_resources.py            # NRP resources testing
│   ├── my_client.py                      # Basic client
│   ├── enhanced_client.py                # Enhanced client
│   └── advanced_test_client.py           # Advanced testing client
├── examples/                      # Example implementations
│   ├── k8s_client.py                     # Kubernetes client example
│   ├── my_server.py                      # Basic server example
│   ├── quick_k8s_test.py                # K8s testing example
│   ├── enhanced_content_extractor.py     # Content extraction
│   ├── extract_nrp_yaml.py              # YAML extraction
│   └── nrp_crawler_and_indexer.py       # Data crawling
├── docs/                          # Documentation and data
│   ├── storage/                          # Runtime storage
│   ├── nrp_crawled_data/                # Crawled NRP data
│   ├── nrp_resources/                   # Resource collections
│   ├── enhanced_nrp_resources/          # Enhanced resources
│   └── ultimate_nrp_resources/          # Ultimate resource sets
└── ultimate_fastmcp_server.py      # 🚀 ULTIMATE: All concepts unified (Port 8020)
```

## 🚀 Quick Start

### Running Core Servers

**Tools Servers:**
```bash
cd core/tools
python k8s_infogent_server.py          # Kubernetes operations
python advanced_infogent_server.py     # Enhanced tools
```

**Resource Servers:**
```bash
cd core/resources
python nrp_resources_server.py         # Basic resources
python enhanced_nrp_resources_server.py # Enhanced resources
```

**Prompt Servers:**
```bash
cd core/prompts
python nrp_prompts_server.py           # Basic prompts
python advanced_nrp_prompts_server.py  # FastMCP prompts (Port 8010)
```

### Running Advanced FastMCP Servers

**Context-Aware Server:**
```bash
cd advanced/context
python context_aware_nrp_server.py     # Port 8011
```

**Elicitation Server:**
```bash
cd advanced/elicitation
python elicitation_enhanced_nrp_server.py # Port 8012
```

**Logging Server:**
```bash
cd advanced/logging
python logging_enhanced_nrp_server.py  # Port 8013
```

### 🚀 Running the ULTIMATE Unified Server

**Ultimate FastMCP Server (ALL Concepts Integrated):**
```bash
python ultimate_fastmcp_server.py      # Port 8020 - All FastMCP concepts unified!
```

This is the crown jewel - a single server that integrates ALL FastMCP concepts:
- Advanced Prompts + Context + Elicitation + Logging + Progress + Server Flags

## 🧪 Testing

### Individual Component Testing
```bash
cd tests
python test_advanced_prompts.py        # Test prompts system
python test_context_aware_server.py    # Test context features
python test_elicitation_server.py      # Test elicitation
python test_logging_server.py          # Test logging features
```

### Client Testing
```bash
cd tests
python my_client.py                    # Basic client testing
python enhanced_client.py              # Enhanced client testing
python advanced_test_client.py         # Advanced testing
```

### Ultimate Server Testing
```bash
cd tests
python test_ultimate_fastmcp_server.py # Test ALL concepts integrated
```

## ⚡ FastMCP Features Implemented

### 1. **Advanced Prompts System** (Port 8010)
- **File:** `core/prompts/advanced_nrp_prompts_server.py`
- **Features:**
  - 6 comprehensive prompt templates
  - Pydantic enums and validation
  - PromptMessage with TextContent objects
  - Structured parameter handling

### 2. **Context-Aware Capabilities** (Port 8011)
- **File:** `advanced/context/context_aware_nrp_server.py`
- **Features:**
  - Logging with context metadata
  - Progress reporting with structured updates
  - State management with persistent storage
  - Client elicitation for input collection
  - LLM sampling for intelligent responses
  - Request metadata and session tracking

### 3. **Progressive Elicitation** (Port 8012)
- **File:** `advanced/elicitation/elicitation_enhanced_nrp_server.py`
- **Features:**
  - Multi-turn progressive elicitation
  - Structured response types and validation
  - Enhanced error handling with context
  - Server flags for runtime configuration
  - Smart defaults and auto-retry capabilities

### 4. **Structured Logging** (Port 8013)
- **File:** `advanced/logging/logging_enhanced_nrp_server.py`
- **Features:**
  - Multi-level logging (debug, info, warning, error)
  - Structured metadata with rich context
  - Performance tracking with timing metrics
  - Security logging with compliance metadata
  - Session correlation and request tracking
  - Runtime configuration management

### 5. **🚀 Ultimate FastMCP Server** (Port 8020) - **ALL CONCEPTS UNIFIED**
- **File:** `ultimate_fastmcp_server.py`
- **Features:**
  - **ALL CONCEPTS INTEGRATED**: Every FastMCP capability in one server
  - **Advanced Prompts**: Structured validation with progress integration
  - **Context Awareness**: Logging, state, progress, and elicitation combined
  - **Progressive Elicitation**: Multi-turn with context preservation and progress tracking
  - **Structured Logging**: Performance, security, and compliance with session correlation
  - **Real-time Progress**: Multiple patterns (percentage, absolute, indeterminate, multi-stage)
  - **Server Flags**: Runtime configuration affecting all integrated features
  - **Enhanced Error Handling**: Recovery context with all capabilities available
  - **Session Management**: Unified state across all FastMCP concepts
  - **Enterprise-grade**: Production-ready with SOC2 compliance and audit trails

## 🔧 Configuration

### Environment Variables
```bash
# Required for NRP integration
NRP_API_KEY=your_nrp_api_key_here
NRP_BASE_URL=https://llm.nrp-nautilus.io/
NRP_MODEL=gemma3

# Optional fallback
OPENAI_API_KEY=fallback_key
OPENAI_BASE_URL=fallback_endpoint
```

### Port Assignments
- **8010:** Advanced Prompts Server
- **8011:** Context-Aware Server
- **8012:** Elicitation Server
- **8013:** Logging Server
- **8020:** 🚀 **Ultimate FastMCP Server (ALL CONCEPTS UNIFIED)**

## 🏗️ Architecture

### Core Components
- **Tools:** Direct operational capabilities (K8s, content processing)
- **Resources:** Data access and management
- **Prompts:** Template-based interaction patterns

### Advanced Features
- **Context:** Enhanced MCP object capabilities
- **Elicitation:** Progressive user input collection
- **Logging:** Enterprise-grade structured logging

## 📖 Key Technical Patterns

### FastMCP Prompts
```python
@mcp.prompt()
async def nrp_deployment_assistant(gpu_type: GPUType = GPUType.A100) -> PromptMessage:
    return PromptMessage(
        role="user",
        content=TextContent(type='text', text=prompt_content)
    )
```

### Context Operations
```python
@mcp.tool()
async def context_tool(ctx: Context, param: str) -> str:
    await ctx.info("Processing request")
    await ctx.report_progress(0.5, "Halfway complete")
    ctx.set_state("key", "value")
    return result
```

### Structured Logging
```python
StructuredLogger.log_with_metadata(
    level="info",
    message="Operation completed",
    category="performance",
    metadata={"duration": 1.23, "status": "success"}
)
```

## 🔄 Migration Notes

This restructured organization preserves all incremental progress while providing:
- **Clear separation** of core vs advanced features
- **Logical grouping** by functionality type
- **Consolidated testing** with organized test suites
- **Improved maintainability** with reduced file sprawl
- **Enhanced documentation** with comprehensive examples

## 🤝 Contributing

1. Follow the established directory structure
2. Add tests for new features in `tests/`
3. Update documentation for new capabilities
4. Ensure FastMCP compatibility for advanced features

## 📄 License

Part of the NRP K8s System project for intelligent routing and management.