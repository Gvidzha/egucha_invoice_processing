"""
Main entry point for the Invoice Processing API
"""
import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the FastAPI app
from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
