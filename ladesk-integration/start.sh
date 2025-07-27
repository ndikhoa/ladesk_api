#!/bin/bash

echo "🎯 LADESK INTEGRATION PROJECT"
echo "================================================"

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    echo "Please install Python 3.7+ and try again"
    exit 1
fi

# Kiểm tra virtual environment
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
fi

# Kích hoạt virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Cài đặt dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Tạo thư mục logs
if [ ! -d "logs" ]; then
    echo "📁 Creating logs directory..."
    mkdir logs
fi

# Tạo file .env nếu chưa có
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo "📝 Creating .env file..."
        cp env.example .env
    fi
fi

# Chạy ứng dụng
echo "🚀 Starting Ladesk Integration API..."
echo ""
echo "🌐 Server will be available at: http://localhost:3000"
echo "📊 Health check: http://localhost:3000/health"
echo "📝 Logs: logs/app.log"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py 