import os
import json
import asyncio

# Load environment before any api imports
def load_env():
    env_path = os.path.join("api", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    os.environ[key] = value

load_env()

# Now we can import
try:
    from api.db import db_client
except KeyError as e:
    print(f"Failed to import db_client due to missing environment variable: {e}")
    exit(1)

async def get_recent_runs(user_id=1, limit=10):
    try:
        # get_all_workflow_runs returns list of WorkflowRunModel
        runs = await db_client.get_all_workflow_runs()
        
        # Filter for recent ones manually if needed, or just sort
        if runs:
            # Sort by created_at desc
            runs.sort(key=lambda x: x.created_at, reverse=True)
            
            run_data = []
            for r in runs[:limit]:
                # end_reason might be in gathered_context
                gc = r.gathered_context or {}
                run_data.append({
                    'id': r.id,
                    'workflow_id': r.workflow_id,
                    'status': "Completed" if r.is_completed else "Running/Pending",
                    'call_disposition': gc.get('call_disposition'),
                    'mapped_disposition': gc.get('mapped_call_disposition'),
                    'created_at': r.created_at.isoformat() if r.created_at else None
                })
            print(json.dumps(run_data, indent=2))
        else:
            print("No runs found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_recent_runs())
