#!/usr/bin/env python
"""
Run script for unlimited file uploads
"""

import os
import sys
import subprocess

def main():
    """Start Streamlit with unlimited file upload configuration"""
    
    print("🚀 Starting APS Wallet Dashboard with UNLIMITED file uploads")
    print("=" * 60)
    
    # Create necessary directories
    os.makedirs("temp_uploads", exist_ok=True)
    os.makedirs("exports", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Set environment variables
    os.environ['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '0'  # Unlimited
    os.environ['STREAMLIT_SERVER_MAX_MESSAGE_SIZE'] = '0'  # Unlimited
    os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'true'
    os.environ['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'true'
    
    print("Configuration:")
    print(f"  Max Upload Size: {os.environ.get('STREAMLIT_SERVER_MAX_UPLOAD_SIZE')} (0 = unlimited)")
    print(f"  Max Message Size: {os.environ.get('STREAMLIT_SERVER_MAX_MESSAGE_SIZE')} (0 = unlimited)")
    print()
    print("Dashboard will be available at: http://localhost:8501")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Run Streamlit with our app
    try:
        subprocess.run([
            'streamlit', 'run', 'app.py',
            '--server.maxUploadSize', '0',
            '--server.maxMessageSize', '0',
            '--server.port', '8501',
            '--server.address', '0.0.0.0',
            '--server.enableCORS', 'true',
            '--server.enableXsrfProtection', 'true',
            '--logger.level', 'info'
        ])
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
