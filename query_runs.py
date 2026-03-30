import asyncio
import os
import json
import asyncpg
from dotenv import load_dotenv

load_dotenv("api/.env")

async def main():
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            print("DATABASE_URL not found")
            return
            
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        
        conn = await asyncpg.connect(db_url)
        
        # Query ALL recent runs
        rows = await conn.fetch("""
            SELECT id, workflow_id, state, is_completed, mode, created_at, logs, gathered_context
            FROM workflow_runs
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        runs = []
        for row in rows:
            run = dict(row)
            run['created_at'] = run['created_at'].isoformat()
            runs.append(run)
            
        with open("recent_runs.json", "w", encoding='utf-8') as f:
            json.dump(runs, f, indent=2, ensure_ascii=False)
            
        print(f"Successfully dumped {len(runs)} recent runs to recent_runs.json")
        
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
