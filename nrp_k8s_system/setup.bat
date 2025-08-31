@echo off
REM NRP K8s System Setup Script for Windows

echo 🚀 Setting up NRP K8s System...

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python is installed

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Create .env from template if it doesn't exist
if not exist ".env" (
    echo ⚙️ Creating .env from template...
    copy config\default.env .env
    echo 📝 Please edit .env with your NRP credentials
) else (
    echo ✅ .env file already exists
)

REM Create cache directory
if not exist "cache" mkdir cache
if not exist "cache\router_cache" mkdir cache\router_cache
echo ✅ Cache directory created

REM Check kubectl
kubectl version --client >nul 2>&1
if errorlevel 1 (
    echo ⚠️ kubectl not found - install it for full functionality
) else (
    echo ✅ kubectl is installed
    
    REM Check kubectl connectivity (optional)
    kubectl cluster-info >nul 2>&1
    if errorlevel 1 (
        echo ⚠️ kubectl installed but cannot connect to cluster
        echo    Make sure your kubeconfig is properly configured
    ) else (
        echo ✅ kubectl can connect to cluster
    )
)

echo.
echo 🎉 Setup complete!
echo.
echo Next steps:
echo 1. Edit .env with your NRP_API_KEY
echo 2. Ensure kubectl is configured for your cluster
echo 3. Test the system:
echo    venv\Scripts\activate.bat
echo    python -m nrp_k8s_system.intelligent_router "list pods"
echo.
echo For interactive mode:
echo    python -m nrp_k8s_system.intelligent_router
echo.
pause