import os
import sys
from pathlib import Path

# Add the api directory to the path
api_path = Path(__file__).parent
sys.path.insert(0, str(api_path))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Start uvicorn
import uvicorn

if __name__ == "__main__":
    print("\n🚀 Starting SuryaCaller Backend Server...")
    print("=" * 60)
    print("Backend API will be available at: http://localhost:8000")
    print("Health check: http://localhost:8000/health")
    print("=" * 60)
    print("\nServer starting...\n")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
