from sqlalchemy.ext.asyncio import create_async_engine
import asyncio
import os
from dotenv import load_dotenv

load_dotenv('api/.env')

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"Connecting to: {DATABASE_URL[:30]}...")

async def query_users():
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, email, provider_id FROM users"))
        users = result.fetchall()
        print("\nUsers in database:")
        for user in users:
            print(f"  ID: {user.id}, Email: {user.email}, Provider ID: {user.provider_id}")
    
    await engine.dispose()

from sqlalchemy import text
asyncio.run(query_users())
