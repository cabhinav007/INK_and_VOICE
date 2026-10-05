import uvicorn
import os
import sys

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting Ink & Voice FastAPI backend server...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
