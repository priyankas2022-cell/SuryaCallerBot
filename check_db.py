import asyncio
import os

# Load environment
def load_env():
    env_path = os.path.join("api", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    value = value.strip('"').strip("'")
                    os.environ[key] = value

load_env()

from api.db import db_client
from api.db.models import UserModel, WorkflowModel
from sqlalchemy.future import select

async def check_db():
    async with db_client.async_session() as session:
        # Check users
        user_result = await session.execute(select(UserModel))
        users = user_result.scalars().all()
        print(f"Users found: {len(users)}")
        for u in users:
            print(f"  ID: {u.id}, Email: {u.email}, Superuser: {u.is_superuser}")
            
        # Check workflows
        wf_result = await session.execute(select(WorkflowModel))
        workflows = wf_result.scalars().all()
        print(f"Workflows found: {len(workflows)}")
        for w in workflows:
            print(f"  ID: {w.id}, Name: {w.name}, User ID: {w.user_id}")

if __name__ == "__main__":
    asyncio.run(check_db())
