#!/usr/bin/env python3
"""
Root-level launcher for Render deployment
This file starts the FastAPI app from the backend directory
"""

import sys
import os

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Change working directory to backend
os.chdir(backend_path)

# Import and run the FastAPI app
if __name__ == "__main__":
    try:
        from main import app
        import uvicorn
        
        port = int(os.environ.get("PORT", 8000))
        print(f"Starting server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except ImportError as e:
        print(f"Import error: {e}")
        print("Available modules:")
        import pkgutil
        for importer, modname, ispkg in pkgutil.iter_modules():
            print(f"  {modname}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)