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
        # Let's list all tables first:
        result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = result.fetchall()
        print("Tables in DB:")
        for t in tables:
            print("-", t[0])
            
asyncio.run(query_db())
