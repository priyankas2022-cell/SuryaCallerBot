"""
SuryaCaller Backend Startup Script
This script properly loads environment variables and starts the backend server
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get the directory structure
current_dir = Path(__file__).parent
project_root = current_dir.parent

# Add project root to Python path
sys.path.insert(0, str(project_root))

# Load environment variables from api/.env
env_file = current_dir / "api" / ".env"
if env_file.exists():
    print(f"✅ Loading environment from: {env_file}")
    load_dotenv(env_file)
else:
    print(f"⚠️ Warning: .env file not found at {env_file}")
    print("Using system environment variables")

# Verify critical environment variables
required_vars = ["DATABASE_URL", "REDIS_URL"]
missing_vars = []

for var in required_vars:
    if var not in os.environ:
        missing_vars.append(var)

if missing_vars:
    print(f"\n❌ ERROR: Missing required environment variables:")
    for var in missing_vars:
        print(f"   - {var}")
    print(f"\nPlease ensure your .env file contains these variables")
    sys.exit(1)

print(f"\n✅ Environment variables loaded successfully")
print(f"   DATABASE_URL: {os.environ.get('DATABASE_URL')[:30]}...")
print(f"   REDIS_URL: {os.environ.get('REDIS_URL')[:30]}...")

# Now start uvicorn
import uvicorn

print("\n" + "=" * 70)
print("🚀 STARTING SURYACALLER BACKEND SERVER")
print("=" * 70)
print(f"\nServer Configuration:")
print(f"  • Host: 0.0.0.0")
print(f"  • Port: 8000")
print(f"  • Reload: Enabled (development mode)")
print(f"  • Log Level: info")
print(f"\nEndpoints:")
print(f"  • API Base: http://localhost:8000/api/v1")
print(f"  • Health Check: http://localhost:8000/health")
print(f"  • Docs: http://localhost:8000/docs")
print("=" * 70)
print("\nServer starting...\n")

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
