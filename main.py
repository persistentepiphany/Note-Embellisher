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
    from main import app
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)