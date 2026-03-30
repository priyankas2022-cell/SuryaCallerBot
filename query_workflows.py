import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv
import pathlib
import os

load_dotenv(pathlib.Path("api/.env"))
db_url = os.environ.get("DATABASE_URL")
# SQLAlchemy asyncpg URL
db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

async def query_db():
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT id, name, workflow_definition FROM workflows LIMIT 10"))
        workflows = result.fetchall()
        print("Workflows:")
        for w in workflows:
            print(f"- ID: {w[0]}, Name: {w[1]}")
            # print(f"  Definition: {str(w[2])[:100]}...")
            
        print("\nWorkflow Definitions (Versions):")
        result2 = await session.execute(text("SELECT id, workflow_id, workflow_hash, is_current FROM workflow_definitions LIMIT 10"))
        for d in result2.fetchall():
            print(f"- Def ID: {d[0]}, WF: {d[1]}, Hash: {d[2]}, IsCurrent: {d[3]}")

asyncio.run(query_db())
