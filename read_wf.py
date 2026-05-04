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
        # Get the first workflow definition
        result = await session.execute(text("SELECT id, workflow_id, workflow_json FROM workflow_definitions ORDER BY id DESC LIMIT 1"))
        row = result.fetchone()
        if row:
            print(f"Def ID: {row[0]}, WF ID: {row[1]}")
            wf_json = row[2]
            print(json.dumps(wf_json, indent=2))
        else:
            print("No workflows found.")

asyncio.run(read_workflow())
