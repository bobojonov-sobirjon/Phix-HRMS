#!/usr/bin/env python3
"""
Start server and run setup script
This script starts the FastAPI server and runs the setup
"""

import subprocess
import time
import requests
import sys
import os

def check_server_running():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Phix HRMS server...")
    
    try:
        # Start the server in the background
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        for i in range(30):  # Wait up to 30 seconds
            if check_server_running():
                print("✅ Server is running!")
                return process
            time.sleep(1)
            print(f"   Checking... ({i+1}/30)")
        
        print("❌ Server failed to start within 30 seconds")
        return None
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def run_setup():
    """Run the setup script"""
    print("\n🔧 Running setup script...")
    
    try:
        result = subprocess.run([sys.executable, "setup_email.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Setup completed successfully!")
            print(result.stdout)
        else:
            print("❌ Setup failed!")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error running setup: {e}")

def main():
    """Main function"""
    print("🎯 Phix HRMS Server Setup")
    print("=" * 40)
    
    # Check if server is already running
    if check_server_running():
        print("✅ Server is already running!")
    else:
        # Start server
        process = start_server()
        if not process:
            print("❌ Failed to start server")
            return
    
    # Run setup
    run_setup()
    
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. The server is running at: http://localhost:8000")
    print("2. API documentation: http://localhost:8000/docs")
    print("3. Test the authentication endpoints")
    print("4. Check your email for OTP codes")
    
    print("\n🔗 Quick test URLs:")
    print("   Health check: http://localhost:8000/health")
    print("   API root: http://localhost:8000/api/v1/auth")
    
    # Keep the script running
    try:
        print("\n⏹️  Press Ctrl+C to stop the server...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        if 'process' in locals():
            process.terminate()

if __name__ == "__main__":
    main() 