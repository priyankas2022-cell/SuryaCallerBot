"""
SuryaCaller Backend Server - Direct Startup
Loads environment and starts the backend
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get directories
current_dir = Path(__file__).parent
project_root = current_dir.parent

# Add to path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "pipecat" / "src"))

# Load environment
env_file = current_dir / ".env"
print(f"\n🔧 Loading environment from: {env_file}")
if env_file.exists():
    load_dotenv(env_file)
    print("✅ Environment loaded successfully")
else:
    print(f"❌ ERROR: .env file not found at {env_file}")
    sys.exit(1)

# Verify required vars
required = ["DATABASE_URL", "REDIS_URL"]
missing = [v for v in required if v not in os.environ]
if missing:
    print(f"\n❌ Missing environment variables: {missing}")
    sys.exit(1)

print(f"✅ DATABASE_URL: {os.environ['DATABASE_URL'][:40]}...")
print(f"✅ REDIS_URL: {os.environ['REDIS_URL'][:40]}...")

# Start server
import uvicorn

print("\n" + "="*60)
print("🚀 STARTING BACKEND SERVER")
print("="*60)
print(f"📍 URL: http://localhost:8000")
print(f"📖 API: http://localhost:8000/api/v1")
print(f"🏥 Health: http://localhost:8000/health")
print(f"📚 Docs: http://localhost:8000/docs")
print("="*60)
print()

uvicorn.run(
    "app:app",
    host="0.0.0.0",
    port=8000,
    reload=False,
    log_level="info"
)
