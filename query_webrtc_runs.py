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
            
        # asyncpg needs postgresql:// prefix
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        
        conn = await asyncpg.connect(db_url)
        
        # Query recent WebRTC runs
        rows = await conn.fetch("""
            SELECT id, workflow_id, state, is_completed, created_at, logs, gathered_context
            FROM workflow_runs
            WHERE mode = 'smallwebrtc'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        runs = []
        for row in rows:
            run = dict(row)
            # Convert datetime to string for JSON serialization
            run['created_at'] = run['created_at'].isoformat()
            
            # Extract last few logs if they exist
            logs = run.get('logs')
            if logs:
                if isinstance(logs, list):
                    run['logs_summary'] = logs[-5:]
                elif isinstance(logs, dict):
                    # Some logs are dicts with 'realtime_feedback_events'
                    fb = logs.get('realtime_feedback_events')
                    if fb and isinstance(fb, list):
                        run['logs_summary'] = fb[-5:]
            
            runs.append(run)
            
        with open("webrtc_runs_detailed.json", "w", encoding='utf-8') as f:
            json.dump(runs, f, indent=2, ensure_ascii=False)
            
        print(f"Successfully dumped {len(runs)} recent WebRTC runs to webrtc_runs_detailed.json")
        
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
