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
    from api.db.models import UserConfigurationModel
except KeyError as e:
    print(f"Failed to import db_client due to missing environment variable: {e}")
    exit(1)

async def get_user_config(user_id=1):
    try:
        # Check if the table exists and get the config
        config = await db_client.get_user_configurations(user_id)
        if config:
            # Mask sensitive tokens for logging
            config_dict = config.model_dump()
            
            def mask_key(d, key):
                if d and key in d and d[key]:
                    val = d[key]
                    d[key] = f"{val[:4]}...{val[-4:]}" if len(val) > 8 else "***"

            if config_dict.get('stt'): mask_key(config_dict['stt'], 'api_key')
            if config_dict.get('tts'): mask_key(config_dict['tts'], 'api_key')
            if config_dict.get('llm'): mask_key(config_dict['llm'], 'api_key')
            if config_dict.get('embeddings'): mask_key(config_dict['embeddings'], 'api_key')
            
            print(json.dumps(config_dict, indent=2))
        else:
            print(f"No configuration found for user {user_id}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_user_config())
