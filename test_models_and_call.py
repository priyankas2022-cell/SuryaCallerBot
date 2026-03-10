import asyncio
import httpx
from datetime import datetime

# Simple workflow definition - just start and end
SIMPLE_WORKFLOW_DEFINITION = {
    "nodes": [
        {
            "id": "1",
            "type": "startCall",
            "position": {"x": 0, "y": 0},
            "data": {
                "name": "Start",
                "prompt": "Hello! This is a test call from SuryaCaller AI voice agent. How can I help you today?",
                "is_start": True,
                "allow_interrupt": False,
                "add_global_prompt": False,
            },
        },
        {
            "id": "2",
            "type": "endCall",
            "position": {"x": 0, "y": 200},
            "data": {
                "name": "End",
                "prompt": "Thank you for your time. Goodbye!",
                "is_end": True,
            },
        }
    ],
    "edges": [
        {
            "id": "1-2",
            "source": "1",
            "target": "2",
            "data": {"label": "End", "condition": "End the call"},
        }
    ],
}

async def test_and_call():
    # Login credentials
    email = "admin@suryacaller.com"
    password = "admin123"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("SURYACALLER - Model Test & Call Generation")
        print("=" * 60)
        
        # Step 1: Login
        print("\n[Step 1] Authenticating...")
        response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        
        if response.status_code != 200:
            # Try signup if login fails
            print("  Creating new account...")
            response = await client.post(
                "http://localhost:8000/api/v1/auth/signup",
                json={"email": email, "password": password, "name": "Admin User"}
            )
        
        token = response.json()["token"]
        print(f"  ✓ Authentication successful")
        
        # Step 2: Get current configuration
        print("\n[Step 2] Fetching model configuration...")
        response = await client.get(
            "http://localhost:8000/api/v1/user/configurations/user",
            headers={"Authorization": f"Bearer {token}"}
        )
        config = response.json()
        
        print(f"  LLM: {config['llm']['provider']} / {config['llm']['model']}")
        print(f"  TTS: {config['tts']['provider']} / {config['tts']['model']} (Voice: {config['tts']['voice']})")
        print(f"  STT: {config['stt']['provider']} / {config['stt']['model']}")
        
        # Step 3: Validate configuration
        print("\n[Step 3] Validating API keys...")
        response = await client.get(
            "http://localhost:8000/api/v1/user/configurations/user/validate?validity_ttl_seconds=60",
            headers={"Authorization": f"Bearer {token}"}
        )
        validation = response.json()
        
        if validation.get('status') == []:
            print(f"  ✓ Configuration is valid")
        else:
            print(f"  ⚠ Validation issues: {validation}")
        
        # Step 4: Create a simple workflow
        print("\n[Step 4] Creating test voice agent workflow...")
        workflow_name = f"Test Voice Agent - {datetime.now().strftime('%Y%m%d %H%M%S')}"
        
        response = await client.post(
            "http://localhost:8000/api/v1/workflow/create/definition",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "name": workflow_name,
                "workflow_definition": SIMPLE_WORKFLOW_DEFINITION
            }
        )
        
        if response.status_code == 200:
            workflow = response.json()
            workflow_id = workflow['id']
            print(f"  ✓ Workflow created: ID {workflow_id}")
            print(f"    Name: {workflow['name']}")
        else:
            print(f"  ✗ Failed to create workflow: {response.text}")
            return
        
        # Step 5: Check telephony configuration
        print("\n[Step 5] Checking telephony provider...")
        response = await client.get(
            "http://localhost:8000/api/v1/telephony",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            telephony_configs = response.json()
            if isinstance(telephony_configs, list) and len(telephony_configs) > 0:
                print(f"  ✓ Telephony provider configured: {telephony_configs[0].get('provider', 'Unknown')}")
                telephony_configured = True
            else:
                telephony_configured = False
        else:
            telephony_configured = False
        
        if not telephony_configured:
            print("  ⚠ WARNING: No telephony provider configured!")
            print("  To make actual phone calls, you need to configure:")
            print("    - Twilio, Vobiz, Cloudonix, or Looptalk")
            print("    - Go to: http://localhost:3000/telephony-configurations")
            print("\n  For testing purposes, you can:")
            print("    1. Use the workflow in WebRTC mode (browser-based)")
            print("    2. Configure a telephony provider first")
        else:
            print(f"  ✓ Telephony provider configured")
        
        # Step 6: Initiate a call (if telephony is configured)
        print("\n[Step 6] Call initiation options...")
        print(f"""
Your voice agent is now ready! Here's what you can do:

1. **WebRTC Test Call** (No phone required):
   - Open: http://localhost:3000/workflow/{workflow_id}
   - Click "Test Workflow" to test via browser

2. **Phone Call** (Requires telephony config):
   - Configure telephony at: http://localhost:3000/telephony-configurations
   - Then use the initiate-call endpoint:
     
     POST http://localhost:8000/api/v1/initiate-call
     {{
       "workflow_id": {workflow_id},
       "phone_number": "+91XXXXXXXXXX"
     }}

3. **Campaign** (Bulk calling):
   - Create a campaign with contacts
   - System will automatically call all numbers

Workflow Details:
  - ID: {workflow_id}
  - Name: {workflow_name}
  - Status: Active
  - Uses: Groq LLM + Sarvam TTS/STT

The AI agent will say:
  "Hello! This is a test call from SuryaCaller AI voice agent. 
   How can I help you today?"
""")
        
        print("=" * 60)
        print("SETUP COMPLETE!")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_and_call())
