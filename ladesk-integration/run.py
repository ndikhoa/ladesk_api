#!/usr/bin/env python3
"""
Script khởi tạo và chạy Ladesk Integration API
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

def setup_environment():
    """Khởi tạo môi trường"""
    print("🔧 Setting up environment...")
    
    # Tạo thư mục logs nếu chưa có
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    print(f"✅ Created logs directory: {logs_dir}")
    
    # Kiểm tra file .env
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from env.example...")
        try:
            with open(env_example, 'r') as src:
                with open(env_file, 'w') as dst:
                    dst.write(src.read())
            print("✅ Created .env file")
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️ No .env file found and no env.example available")

def check_dependencies():
    """Kiểm tra dependencies"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'flask',
        'requests', 
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - missing")
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def check_database():
    """Kiểm tra database"""
    print("🗄️ Checking database...")
    
    try:
        from database import db
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def start_application():
    """Khởi động ứng dụng"""
    print("🚀 Starting Ladesk Integration API...")
    
    try:
        # Import và chạy app
        from app import app
        
        print(f"✅ Application started successfully")
        print(f"🌐 Server running on: http://localhost:3000")
        print(f"📊 Health check: http://localhost:3000/health")
        print(f"📝 Logs: logs/app.log")
        print("\nPress Ctrl+C to stop the server")
        
        # Chạy Flask app
        app.run(
            host='0.0.0.0',
            port=3000,
            debug=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False
    
    return True

def run_tests():
    """Chạy test suite"""
    print("🧪 Running test suite...")
    
    try:
        result = subprocess.run([sys.executable, "test_api.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")

def main():
    """Main function"""
    print("🎯 LADESK INTEGRATION PROJECT")
    print("=" * 50)
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        return
    
    # Check database
    if not check_database():
        print("\n❌ Database setup failed")
        return
    
    # Menu options
    while True:
        print("\n" + "=" * 50)
        print("📋 Available options:")
        print("1. Start API Server")
        print("2. Run Test Suite")
        print("3. Health Check")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            start_application()
        elif choice == "2":
            run_tests()
        elif choice == "3":
            try:
                import requests
                response = requests.get("http://localhost:3000/health", timeout=5)
                print(f"Health Check Status: {response.status_code}")
                print(f"Response: {response.json()}")
            except Exception as e:
                print(f"Health check failed: {e}")
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please select 1-4.")

if __name__ == "__main__":
    main() 