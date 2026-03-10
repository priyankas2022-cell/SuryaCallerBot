"""
SuryaCaller Backend - MINIMAL Startup
Only loads essential services, skips optional AI providers
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
    print(f"❌ Missing: {missing}")
    sys.exit(1)

print(f"✅ DATABASE_URL: OK")
print(f"✅ REDIS_URL: OK")
print(f"✅ MINIO_ENDPOINT: {os.environ.get('MINIO_ENDPOINT', 'not set')}")

# Monkey-patch problematic imports before loading app
print(f"\n{'='*60}")
print("⚙️  APPLYING COMPATIBILITY FIXES")
print(f"{'='*60}")

# Mock google.cloud.speech_v2 if not available
try:
    from google.cloud import speech_v2
    print("✅ google.cloud.speech_v2 available")
except ImportError:
    print("⚠️  Mocking google.cloud.speech_v2 (will disable Google STT)")
    import types
    speech_v2_mock = types.ModuleType('google.cloud.speech_v2')
    speech_v2_mock.SpeechClient = None
    speech_v2_mock.RecognitionConfig = None
    sys.modules['google.cloud.speech_v2'] = speech_v2_mock

# Start server directly without full app import to avoid pipecat service_factory
print(f"\n{'='*60}")
print("🚀 STARTING MINIMAL SERVER")
print(f"{'='*60}")
print(f"📍 URL: http://localhost:8000")
print(f"📖 API: http://localhost:8000/api/v1")
print(f"🏥 Health: http://localhost:8000/health")
print(f"📚 Docs: http://localhost:8000/docs")
print(f"{'='*60}\n")

# Import and run minimal FastAPI app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("✅ Minimal backend started")
    yield
    # Shutdown
    print("👋 Shutting down")

app = FastAPI(title="SuryaCaller Minimal", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "SuryaCaller Minimal Backend", "status": "running"}

# Start uvicorn
import uvicorn

uvicorn.run(
    "start_minimal:app",
    host="0.0.0.0",
    port=8000,
    reload=False,
    log_level="info"
)
