import os
import sys
from pathlib import Path

# Add the root directory and pipecat/src to the path
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))
sys.path.insert(0, str(root_path / "pipecat" / "src"))
os.environ["PYTHONPATH"] = f"{root_path}{os.pathsep}{root_path / 'pipecat' / 'src'}"

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Start uvicorn
import uvicorn

if __name__ == "__main__":
    backend_url = os.getenv("BACKEND_API_ENDPOINT", "http://localhost:8000")
    print("\nStarting SuryaCaller Backend Server...")
    print("=" * 60)
    print(f"Backend API available at: {backend_url}")
    print(f"Health check: {backend_url}/api/v1/health")
    print("=" * 60)
    print("\nServer starting...\n")
    
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
