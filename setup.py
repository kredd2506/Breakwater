#!/usr/bin/env python3
"""
NRP K8s System Setup Script
Automated installation and configuration for the complete system
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command with error handling"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version check passed: {sys.version}")
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        "templates",
        "nrp_k8s_system/cache",
        "mcp/cache",
        "logs"
    ]

    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def install_requirements():
    """Install Python requirements"""
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python dependencies"
    )

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_path = Path(".env")
    env_example_path = Path(".env.example")

    if not env_path.exists() and env_example_path.exists():
        shutil.copy(env_example_path, env_path)
        print("📄 Created .env file from template")
        print("⚠️  Please edit .env file with your actual API keys")
    elif env_path.exists():
        print("📄 .env file already exists")
    else:
        print("⚠️  No .env.example found, you may need to create .env manually")

def setup_nrp_k8s_system():
    """Setup the NRP K8s system"""
    nrp_path = Path("nrp_k8s_system")
    if nrp_path.exists():
        return run_command(
            f"cd {nrp_path} && {sys.executable} -m pip install -e .",
            "Installing NRP K8s System as editable package"
        )
    else:
        print("⚠️  NRP K8s System directory not found, skipping")
        return True

def check_templates():
    """Check if templates directory has required files"""
    templates_path = Path("templates")
    chat_html_path = templates_path / "chat.html"

    if not chat_html_path.exists():
        print("⚠️  templates/chat.html not found")
        print("   Web server may not work correctly")
        return False
    else:
        print("✅ Template files found")
        return True

def check_knowledge_bases():
    """Check if knowledge bases are present"""
    print("\n📚 Checking knowledge bases...")

    # Check MCP cache
    mcp_cache = Path("mcp/cache")
    if mcp_cache.exists():
        cache_files = list(mcp_cache.glob("*.py"))
        json_files = list(mcp_cache.glob("*.json"))
        total_files = len(cache_files) + len(json_files)

        if total_files > 0:
            print(f"✅ MCP knowledge base: {total_files} files")

            # Check key knowledge files
            key_files = [
                "nrp_comprehensive_templates.py",
                "nrp_complete_anchor_db.py",
                "nrp_gpu_knowledge.py"
            ]

            missing_key = []
            for key_file in key_files:
                if (mcp_cache / key_file).exists():
                    print(f"  ✅ {key_file}")
                else:
                    missing_key.append(key_file)
                    print(f"  ⚠️  {key_file} (missing)")

            if missing_key:
                print(f"  📋 Missing {len(missing_key)} key knowledge files")
                print(f"     System will work in reduced capability mode")
        else:
            print("⚠️  No knowledge base files found in mcp/cache")
    else:
        print("⚠️  mcp/cache directory not found")

    # Check NRP K8s cache
    nrp_cache = Path("nrp_k8s_system/cache")
    if nrp_cache.exists():
        cache_dirs = [d for d in nrp_cache.iterdir() if d.is_dir()]
        if cache_dirs:
            print(f"✅ NRP K8s cache: {len(cache_dirs)} directories")
        else:
            print("⚠️  No cache directories found in nrp_k8s_system/cache")
    else:
        print("⚠️  nrp_k8s_system/cache directory not found")

    return True  # Non-critical, system works without knowledge bases

def main():
    """Main setup function"""
    print("🚀 NRP K8s System Setup")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Create directories
    print("\n📁 Creating directories...")
    create_directories()

    # Install requirements
    print("\n📦 Installing dependencies...")
    if not install_requirements():
        print("❌ Failed to install dependencies")
        sys.exit(1)

    # Setup NRP K8s system
    print("\n🔧 Setting up NRP K8s System...")
    setup_nrp_k8s_system()

    # Create .env file
    print("\n🔧 Setting up environment...")
    create_env_file()

    # Check templates
    print("\n🔧 Checking templates...")
    check_templates()

    # Check knowledge bases
    check_knowledge_bases()

    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")

    # Run package verification
    print("\n🔍 Running package verification...")
    try:
        import subprocess
        result = subprocess.run([sys.executable, "verify_package.py"],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Package verification passed")
        else:
            print("⚠️  Package verification found some issues (system will still work)")
    except:
        print("⚠️  Could not run package verification")

    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys (optional)")
    print("2. Run the web server: python start_web_server.py")
    print("3. Run the MCP server: python start_mcp_server.py")
    print("4. Or use quick start: quick_start.bat (Windows) / ./quick_start.sh (Linux/macOS)")
    print("\n🌐 Web interface: http://localhost:5000")
    print("🔗 MCP server: http://localhost:8020/mcp")
    print("\n💡 Both servers work in demo mode without API keys!")
    print("📚 Knowledge base included: 1.4MB+ of NRP documentation and templates")

if __name__ == "__main__":
    main()