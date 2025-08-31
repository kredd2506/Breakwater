#!/bin/bash
# NRP K8s System Setup Script

set -e

echo "🚀 Setting up NRP K8s System..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ required. Current version: $python_version"
    exit 1
fi
echo "✅ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env from template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from template..."
    cp config/default.env .env
    echo "📝 Please edit .env with your NRP credentials"
else
    echo "✅ .env file already exists"
fi

# Create cache directory
mkdir -p cache/router_cache
echo "✅ Cache directory created"

# Check kubectl
if command -v kubectl &> /dev/null; then
    echo "✅ kubectl is installed"
    
    # Check kubectl connectivity (optional)
    if kubectl cluster-info &> /dev/null; then
        echo "✅ kubectl can connect to cluster"
    else
        echo "⚠️  kubectl installed but cannot connect to cluster"
        echo "   Make sure your kubeconfig is properly configured"
    fi
else
    echo "⚠️  kubectl not found - install it for full functionality"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your NRP_API_KEY"
echo "2. Ensure kubectl is configured for your cluster"
echo "3. Test the system:"
echo "   source venv/bin/activate"
echo "   python -m nrp_k8s_system.intelligent_router 'list pods'"
echo ""
echo "For interactive mode:"
echo "   python -m nrp_k8s_system.intelligent_router"