import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv
import pathlib
import os

load_dotenv(pathlib.Path("api/.env"))
db_url = os.environ.get("DATABASE_URL")
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

async def read_config():
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT id, user_id, configuration FROM user_configurations LIMIT 10"))
        configs = result.fetchall()
        for row in configs:
            print(f"Config ID: {row[0]}, User ID: {row[1]}")
            conf = row[2]
            # Hide the actual keys to prevent spilling, just show if they exist
            summary = {}
            for k, v in conf.items():
                if isinstance(v, dict):
                    summary[k] = {vk: ("SET" if vv else "EMPTY") if "key" in vk else vv for vk, vv in v.items()}
            print(json.dumps(summary, indent=2))

asyncio.run(read_config())
