"""Startup script that loads .env before launching uvicorn."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the api directory
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(Path(__file__).parent)],
    )
