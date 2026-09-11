import uvicorn
import os
import sys

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Py SIH Weather Decision Assistant Server...")
    print("Mobile Web App: http://127.0.0.1:8000")
    print("Plan For What Matters: http://127.0.0.1:8000/plan")
    print("API Documentation: http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
