import asyncio
import os
import asyncpg
from redis.asyncio import Redis
from dotenv import load_dotenv

async def test_connections():
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL")
    redis_url = os.environ.get("REDIS_URL")
    
    print(f"Testing DB: {db_url}")
    try:
        conn = await asyncio.wait_for(asyncpg.connect(db_url), timeout=5)
        print("✅ DB Connection Successful")
        await conn.close()
    except Exception as e:
        print(f"❌ DB Connection Failed: {e}")

    print(f"Testing Redis: {redis_url}")
    try:
        r = Redis.from_url(redis_url)
        await asyncio.wait_for(r.ping(), timeout=5)
        print("✅ Redis Connection Successful")
        await r.aclose()
    except Exception as e:
        print(f"❌ Redis Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connections())
