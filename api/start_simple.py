"""
SuryaCaller Backend - Simple Startup
Loads environment and starts the server with minimal dependencies
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
print(f"\n{'='*60}")
print("🔧 LOADING ENVIRONMENT")
print(f"{'='*60}")
print(f"Looking for .env at: {env_file}")

if env_file.exists():
    load_dotenv(env_file)
    print("✅ Environment loaded successfully")
else:
    print(f"❌ ERROR: .env file not found at {env_file}")
    sys.exit(1)

# Verify required vars
print(f"\n📊 VERIFYING CONFIGURATION")
print(f"{'='*60}")
required = ["DATABASE_URL", "REDIS_URL"]
missing = [v for v in required if v not in os.environ]
if missing:
    print(f"❌ Missing environment variables: {missing}")
    sys.exit(1)

print(f"✅ DATABASE_URL configured")
print(f"✅ REDIS_URL configured")
print(f"✅ MINIO_ENDPOINT: {os.environ.get('MINIO_ENDPOINT', 'not set')}")
print(f"✅ GROQ API Key: {'configured' if os.environ.get('GROQ_API_KEY') else 'not set'}")
print(f"✅ SARVAM API Key: {'configured' if os.environ.get('SARVAM_API_KEY') else 'not set'}")

# Try to import app
print(f"\n{'='*60}")
print("📦 LOADING APPLICATION")
print(f"{'='*60}")

try:
    from api.app import app
    print("✅ Application loaded successfully")
except Exception as e:
    print(f"❌ Error loading application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Start server
import uvicorn

print(f"\n{'='*60}")
print("🚀 STARTING SERVER")
print(f"{'='*60}")
print(f"📍 URL: http://localhost:8000")
print(f"📖 API: http://localhost:8000/api/v1")
print(f"🏥 Health: http://localhost:8000/health")
print(f"📚 Docs: http://localhost:8000/docs")
print(f"{'='*60}\n")

uvicorn.run(
    "api.app:app",
    host="0.0.0.0",
    port=8000,
    reload=False,
    log_level="info",
    workers=1
)
