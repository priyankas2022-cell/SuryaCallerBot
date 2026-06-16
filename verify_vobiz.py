import asyncio
import httpx
import os
import json
import asyncpg
import pathlib
import traceback
from dotenv import load_dotenv

# Load env variables
load_dotenv(pathlib.Path("api/.env"))
load_dotenv(pathlib.Path(".env"))

async def test_vobiz_keys():
    print("=" * 60)
    print("VOBIZ TELEPHONY SETUP & VERIFICATION")
    print("=" * 60)

    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    # Step 0: Update DB config
    print("\n[Step 0] Updating database organization configurations to use Vobiz...")
    try:
        conn = await asyncpg.connect(db_url)
        vobiz_config = {
            "provider": "vobiz",
            "auth_id": "MA_4BH012XY",
            "auth_token": "QFbFu6JxzNr5bqAsUW2k80DLMi8cdxP4BXPPPhNlZnD0igrJ4IHZhq3Ne6xp2spg",
            "from_numbers": ["+918049280336"]
        }
        vobiz_config_json = json.dumps(vobiz_config)
        
        orgs = await conn.fetch("SELECT id FROM organizations;")
        if not orgs:
            print("  No organizations found in database to update.")
        else:
            for org in orgs:
                org_id = org['id']
                # Try updating
                res = await conn.execute(
                    "UPDATE organization_configurations SET value = $1 WHERE organization_id = $2 AND key = 'TELEPHONY_CONFIGURATION';",
                    vobiz_config_json, org_id
                )
                if res == "UPDATE 0" or res == "UPDATE 0 0" or "0" in res:
                    # Insert new row
                    await conn.execute(
                        "INSERT INTO organization_configurations (organization_id, key, value) VALUES ($1, 'TELEPHONY_CONFIGURATION', $2);",
                        org_id, vobiz_config_json
                    )
                    print(f"  [SUCCESS] Inserted new Vobiz TELEPHONY_CONFIGURATION for Org {org_id}")
                else:
                    print(f"  [SUCCESS] Updated existing TELEPHONY_CONFIGURATION to Vobiz for Org {org_id}")
        await conn.close()
    except Exception as e:
        print(f"  [FAILED] DB Update Error: {repr(e)}")
        traceback.print_exc()

    # 1. Check from environment variables
    env_auth_id = os.getenv("VOBIZ_AUTH_ID")
    env_auth_token = os.getenv("VOBIZ_AUTH_TOKEN")
    env_did_number = os.getenv("VOBIZ_DID_NUMBER")

    print("\n[Step 1] Checking environment configuration...")
    if env_auth_id and env_auth_token and env_did_number:
        print(f"  [OK] Found Vobiz config in environment variables:")
        print(f"    Auth ID: {env_auth_id}")
        print(f"    Auth Token: {env_auth_token[:4]}...{env_auth_token[-4:] if len(env_auth_token) > 8 else '***'}")
        print(f"    DID Number: {env_did_number}")
        
        # Test connectivity
        print("\n  Testing environment credentials against Vobiz API...")
        await verify_credentials_api(env_auth_id, env_auth_token)
    else:
        print("  [WARNING] Vobiz credentials not completely found in environment.")

    # 2. Check from database
    print("\n[Step 2] Checking database organization configurations...")
    try:
        conn = await asyncpg.connect(db_url)
        configs = await conn.fetch("SELECT organization_id, value FROM organization_configurations WHERE key = 'TELEPHONY_CONFIGURATION';")
        
        if not configs:
            print("  No TELEPHONY_CONFIGURATION found in database.")
        else:
            for row in configs:
                org_id = row['organization_id']
                config_val = row['value']
                if isinstance(config_val, str):
                    try:
                        config = json.loads(config_val)
                    except Exception:
                        config = {}
                else:
                    config = config_val
                
                provider = config.get('provider') if isinstance(config, dict) else None
                print(f"\n  Found configuration for Org {org_id}:")
                print(f"    Provider: {provider}")
                
                if provider == 'vobiz':
                    auth_id = config.get('auth_id')
                    auth_token = config.get('auth_token')
                    from_numbers = config.get('from_numbers', [])
                    print(f"    Auth ID: {auth_id}")
                    print(f"    Auth Token: {auth_token[:4]}...{auth_token[-4:] if auth_token and len(auth_token) > 8 else '***'}")
                    print(f"    DID Numbers: {from_numbers}")
                    
                    if auth_id and auth_token:
                        print(f"    Testing database credentials against Vobiz API...")
                        await verify_credentials_api(auth_id, auth_token)
                else:
                    print(f"    Skipping non-vobiz provider: {provider}")
                    
        await conn.close()
    except Exception as e:
        print(f"  [FAILED] DB Error: {repr(e)}")
        traceback.print_exc()

async def verify_credentials_api(auth_id: str, auth_token: str):
    url = f"https://api.vobiz.ai/api/v1/Account/{auth_id}/"
    headers = {
        "X-Auth-ID": auth_id,
        "X-Auth-Token": auth_token,
    }
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                print(f"    [SUCCESS] VALID CREDENTIALS! Response code: 200")
                try:
                    res_json = response.json()
                    print(f"       Account Name: {res_json.get('name', 'N/A')}")
                    print(f"       Account Status: {res_json.get('status', 'N/A')}")
                except Exception:
                    print(f"       Response text: {response.text[:200]}")
            elif response.status_code == 401:
                print(f"    [FAILED] INVALID CREDENTIALS! (401 Unauthorized)")
            else:
                print(f"    [WARNING] API Response: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"    [FAILED] Network or request error: {repr(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_vobiz_keys())
