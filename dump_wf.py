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

async def read_workflow():
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get workflow ID 10 or whichever is there
        result = await session.execute(text("SELECT id, workflow_id, workflow_json FROM workflow_definitions WHERE is_current = true ORDER BY id DESC LIMIT 1"))
        row = result.fetchone()
        if row:
            with open("d:/dograh-main/dograh-main/wf_dump.json", "w") as f:
                json.dump(row[2], f, indent=2)
            print("Dumped to wf_dump.json")
        else:
            print("No workflows found.")

asyncio.run(read_workflow())
