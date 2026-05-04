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

async def query_run():
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT id, state, is_completed, logs, initial_context, call_type, mode FROM workflow_runs ORDER BY id DESC LIMIT 5"))
        runs = result.fetchall()
        
        output = []
        for r in runs:
            data = {
                "id": r[0],
                "state": r[1],
                "completed": r[2],
                "mode": r[6]
            }
            logs = r[3]
            if logs and isinstance(logs, list):
                data["last_logs"] = logs[-10:]
            elif logs and isinstance(logs, dict):
                data["logs"] = dict(list(logs.items())[-10:]) if len(logs) > 10 else logs
            output.append(data)
            
        with open("d:/dograh-main/dograh-main/runs_output.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

asyncio.run(query_run())
