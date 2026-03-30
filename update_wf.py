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

async def update_workflow():
    with open("d:/dograh-main/dograh-main/wf_dump.json", "r") as f:
        wf = json.load(f)
    
    # Update global node prompt (usually id 0)
    for node in wf.get("nodes", []):
        if node.get("type") == "globalNode":
            prompt = node["data"]["prompt"]
            # Enforce Devanagari Hindi
            prompt = prompt.replace(
                "YOU MUST only REPLY IN the language in which  you got the last user input  - simple words, don't mix languages - Use informal but professional language - use simple language and simple everyday words at tenth standard level. Only use roman alphabets.",
                "YOU MUST ALWAYS REPLY ONLY IN HINDI, using the DEVANAGARI script. Never use english letters for your responses. This is critical for the text-to-speech engine to work. Use simple words."
            )
            # Add Knowledge Base Instructions
            prompt += "\n\n## KNOWLEDGE BASE REFERENCES\nYou have access to referred topic documents via your knowledge base tool. Whenever the user asks a question about the reference, company, details, or if you need factual data, YOU MUST use the `retrieve_from_knowledge_base` function call to find the reference before answering."
            node["data"]["prompt"] = prompt
            break
            
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # We need to update both workflow_definitions AND workflows table depending on exactly how it's used
        # We'll just update the latest one
        result = await session.execute(text("SELECT id, workflow_id FROM workflow_definitions WHERE is_current = true ORDER BY id DESC LIMIT 1"))
        row = result.fetchone()
        if row:
            def_id = row[0]
            wf_id = row[1]
            
            # Update workflow_definitions
            await session.execute(
                text("UPDATE workflow_definitions SET workflow_json = :json WHERE id = :id"),
                {"json": json.dumps(wf), "id": def_id}
            )
            
            # Update workflows fallback
            await session.execute(
                text("UPDATE workflows SET workflow_definition = :json WHERE id = :id"),
                {"json": json.dumps(wf), "id": wf_id}
            )
            await session.commit()
            print("Successfully updated database.")
        else:
            print("No workflow found.")

asyncio.run(update_workflow())
