import asyncio
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

async def query_db():
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT id, name FROM workflows LIMIT 10"))
        workflows = result.fetchall()
        print("Workflows:")
        for w in workflows:
            print(f"- ID: {w[0]}, Name: {w[1]}")
            
        print("\nNodes:")
        try:
            result2 = await session.execute(text("SELECT id, workflow_id, name, prompt, document_uuids FROM workflow_nodes LIMIT 10"))
            for n in result2.fetchall():
                print(f"- Node ID: {n[0]}, WF: {n[1]}, Name: {n[2]}, DocUUIDs: {n[4]}")
                print(f"  Prompt: {str(n[3])[:100]}")
        except Exception as e:
            print("Error querying workflow_nodes:", e)

asyncio.run(query_db())
