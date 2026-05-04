import asyncio
import httpx
import json
import psycopg2
from loguru import logger

async def test_twilio_keys():
    conn = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = conn.cursor()
    
    cur.execute("SELECT organization_id, value FROM organization_configurations WHERE key = 'TELEPHONY_CONFIGURATION';")
    configs = cur.fetchall()
    
    for org_id, config_json in configs:
        config = config_json
        if config.get('provider') != 'twilio':
            continue
            
        sid = config.get('account_sid')
        token = config.get('auth_token')
        
        print(f"\nTesting Org {org_id} (SID: {sid[:8]}...):")
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}.json"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, auth=(sid, token))
                if response.status_code == 200:
                    print(f"VALID! (Name: {response.json().get('friendly_name')})")
                else:
                    print(f"INVALID: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_twilio_keys())
