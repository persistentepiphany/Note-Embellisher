#!/usr/bin/env python3
"""
Root-level launcher for Render deployment - MINIMAL VERSION
"""

import os

if __name__ == "__main__":
    try:
        from app_minimal import app
        import uvicorn
        
        port = int(os.environ.get("PORT", 8000))
        print(f"Starting minimal server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Error starting server: {e}")
        import sys
        sys.exit(1)