import asyncio
import os
import asyncpg
from dotenv import load_dotenv

async def list_tables():
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://")
    
    print(f"Connecting to: {db_url}")
    try:
        conn = await asyncpg.connect(db_url)
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        print("Tables in 'public' schema:")
        for table in tables:
            print(f"- {table['table_name']}")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_tables())
