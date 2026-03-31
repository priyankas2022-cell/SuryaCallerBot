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

async def update_workflow2():
    with open("wf_dump.json", "r") as f:
        wf = json.load(f)
    
    # Update start node prompt (usually id 1)
    for node in wf.get("nodes", []):
        if node.get("type") == "startCall":
            prompt = node["data"]["prompt"]
            prompt = prompt.replace(
                'At this point greet the user by saying "hi there"',
                'At this point greet the user by saying a warm Hindi greeting like "Namaste"'
            )
            node["data"]["prompt"] = prompt
            
        elif node.get("type") == "globalNode":
            prompt = node["data"]["prompt"]
            prompt = prompt.replace("YOU MUST ALWAYS REPLY ONLY IN HINDI, using the DEVANAGARI script.", "YOU MUST ALWAYS REPLY ONLY IN HINDI, using the DEVANAGARI script. It is absolutely critical that every single word you speak, even the first greeting, is written in Devanagari Hindi script (e.g. नमस्ते). Do not use any English words or Roman alphabet characters at all.")
            node["data"]["prompt"] = prompt

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT id, workflow_id FROM workflow_definitions WHERE is_current = true ORDER BY id DESC LIMIT 1"))
        row = result.fetchone()
        if row:
            def_id = row[0]
            wf_id = row[1]
            
            await session.execute(
                text("UPDATE workflow_definitions SET workflow_json = :json WHERE id = :id"),
                {"json": json.dumps(wf), "id": def_id}
            )
            await session.execute(
                text("UPDATE workflows SET workflow_definition = :json WHERE id = :id"),
                {"json": json.dumps(wf), "id": wf_id}
            )
            await session.commit()
            print("Successfully updated database.")
        else:
            print("No workflow found.")

asyncio.run(update_workflow2())
