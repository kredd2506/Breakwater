# NRP K8s System - Complete Installation Guide

## 🎯 One-Command Installation

### Windows
```cmd
git clone <your-repo-url>
cd breakwater
quick_start.bat
```

### Linux/macOS
```bash
git clone <your-repo-url>
cd breakwater
chmod +x quick_start.sh
./quick_start.sh
```

The quick start scripts will automatically:
1. ✅ Check Python version
2. 📦 Install all dependencies
3. 📁 Create necessary directories
4. 🔧 Setup environment configuration
5. 🚀 Let you choose which servers to start

## 📋 Manual Installation Steps

### 1. Prerequisites Check
```bash
# Check Python version (3.8+ required)
python --version

# Check Git
git --version

# Check internet connection
ping google.com
```

### 2. Clone Repository
```bash
git clone <your-repo-url>
cd breakwater
```

### 3. Run Setup
```bash
python setup.py
```

### 4. Configure Environment (Optional)
```bash
# Edit .env file with your API keys
cp .env.example .env
# Then edit .env with your preferred editor
```

### 5. Start Servers
```bash
# Option A: Web Server
python start_web_server.py

# Option B: MCP Server
python start_mcp_server.py

# Option C: Both (manual)
# Terminal 1:
python start_web_server.py
# Terminal 2:
python start_mcp_server.py
```

## 🔧 Dependencies Overview

The system installs these key components:

### Web Server Dependencies
- `flask>=2.3.0` - Web framework
- `openai>=1.0.0` - LLM integration
- `asyncio` - Async operations

### MCP Server Dependencies
- `fastmcp>=0.1.0` - MCP protocol
- `kubernetes>=20.0.0` - K8s operations
- `langchain-openai>=0.1.0` - NRP integration

### Shared Dependencies
- `python-dotenv>=1.0.0` - Environment config
- `pydantic>=2.0.0` - Data validation
- `requests>=2.28.0` - HTTP operations
- `beautifulsoup4>=4.11.0` - Web scraping

## 📁 Directory Structure After Installation

```
breakwater/
├── 📦 requirements.txt            # ✅ Created
├── 🔧 setup.py                   # ✅ Created
├── 📄 .env                       # ✅ Created from template
├── 🚀 start_web_server.py        # ✅ Created
├── 🚀 start_mcp_server.py        # ✅ Created
├── 🖥️ quick_start.bat             # ✅ Created (Windows)
├── 🖥️ quick_start.sh              # ✅ Created (Linux/macOS)
├── 📋 logs/                      # ✅ Created (empty)
└── 📄 README.md                  # ✅ Updated
```

## ✅ Verification Steps

### 1. Check Installation
```bash
# Check if setup completed successfully
python -c "import flask, fastmcp, kubernetes; print('✅ All dependencies installed')"

# Check if servers can be imported
python -c "import web_chat_server; print('✅ Web server OK')"
python -c "import sys; sys.path.append('mcp'); import ultimate_fastmcp_server; print('✅ MCP server OK')"
```

### 2. Test Web Server
```bash
python start_web_server.py
# Should show: "Starting NRP K8s Web Server..."
# Then open: http://localhost:5000
```

### 3. Test MCP Server
```bash
python start_mcp_server.py
# Should show: "Starting NRP K8s MCP Server..."
# Available at: http://localhost:8020/mcp
```

### 4. Test Both Servers
```bash
# Web interface
curl http://localhost:5000

# MCP endpoint
curl http://localhost:8020/mcp
```

## 🚨 Troubleshooting

### Python Version Issues
```bash
# Check Python version
python --version

# If < 3.8, install newer Python:
# Windows: Download from python.org
# macOS: brew install python@3.11
# Linux: sudo apt update && sudo apt install python3.11
```

### Port Conflicts
```bash
# Check what's using port 5000
netstat -tulpn | grep :5000

# Check what's using port 8020
netstat -tulpn | grep :8020

# Kill processes if needed
kill -9 <PID>
```

### Missing Dependencies
```bash
# Reinstall all dependencies
pip install --upgrade -r requirements.txt

# Install specific missing packages
pip install flask fastmcp kubernetes langchain-openai
```

### Template Files Missing
```bash
# Check if templates exist
ls -la templates/

# Should contain chat.html
# If missing, restore from git or recreate
```

### Permission Issues (Linux/macOS)
```bash
# Make scripts executable
chmod +x quick_start.sh
chmod +x start_web_server.py
chmod +x start_mcp_server.py
chmod +x setup.py
```

### Environment Variables
```bash
# Check if .env was created
ls -la .env*

# Should see:
# .env          (your config)
# .env.example  (template)

# If .env missing, copy from example
cp .env.example .env
```

## 🌟 Success Indicators

When everything works correctly, you should see:

### Web Server Success
```
🚀 Starting NRP K8s Web Server...
✅ Flask is available
✅ Port 5000 is available
✅ Loading environment from .env
🌐 Starting Flask web server...
   Web interface: http://localhost:5000
```

### MCP Server Success
```
🚀 Starting NRP K8s MCP Server...
✅ FastMCP is available
✅ Port 8020 is available
✅ Found X knowledge base files
🔧 Starting FastMCP server...
   MCP endpoint: http://localhost:8020/mcp
   Available tools: 14 total (8 K8s + 6 FastMCP)
```

## 🚀 Next Steps

After successful installation:

1. **Web Interface**: Open http://localhost:5000 and start chatting
2. **MCP API**: Connect your client to http://localhost:8020/mcp
3. **Documentation**: Check `mcp/docs/` for examples
4. **Configuration**: Edit `.env` for your specific needs

## 📞 Getting Help

- 📖 Read the main `README.md`
- 🔧 Check `mcp/SETUP_GUIDE.md` for MCP-specific help
- 🧪 Run test scripts in `mcp/` directory
- 🐛 Check GitHub issues
- 💬 Use the web chat interface for system help

---

**You're all set! The NRP K8s System is ready to use! 🎉**