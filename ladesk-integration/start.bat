@echo off
echo 🎯 LADESK INTEGRATION PROJECT
echo ================================================

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Kiểm tra virtual environment
if not exist "venv" (
    echo 🔧 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Kích hoạt virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Cài đặt dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

REM Tạo thư mục logs
if not exist "logs" (
    echo 📁 Creating logs directory...
    mkdir logs
)

REM Tạo file .env nếu chưa có
if not exist ".env" (
    if exist "env.example" (
        echo 📝 Creating .env file...
        copy env.example .env
    )
)

REM Chạy ứng dụng
echo 🚀 Starting Ladesk Integration API...
echo.
echo 🌐 Server will be available at: http://localhost:3000
echo 📊 Health check: http://localhost:3000/health
echo 📝 Logs: logs/app.log
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause 