import asyncio
import httpx
import os

async def login_and_update_config():
    # Login credentials - try admin first, or create new user
    email = "admin@suryacaller.com"
    password = os.getenv("ADMIN_PASSWORD", "admin123")
    name = "Admin User"
    
    # Get API keys from environment variables
    groq_api_key = os.getenv("GROQ_API_KEY")
    sarvam_api_key = os.getenv("SARVAM_API_KEY")
    
    if not groq_api_key:
        print("❌ Error: GROQ_API_KEY environment variable not set!")
        print("   Please set it using:")
        print("   export GROQ_API_KEY='your-groq-api-key'")
        return
    
    if not sarvam_api_key:
        print("❌ Error: SARVAM_API_KEY environment variable not set!")
        print("   Please set it using:")
        print("   export SARVAM_API_KEY='your-sarvam-api-key'")
        return
    
    async with httpx.AsyncClient() as client:
        # Try to login first
        print(f"Attempting to login as {email}...")
        response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        
        # If login fails, try to signup
        if response.status_code != 200:
            print(f"Login failed (expected for new user). Creating account...")
            response = await client.post(
                "http://localhost:8000/api/v1/auth/signup",
                json={"email": email, "password": password, "name": name}
            )
            
            if response.status_code != 200:
                print(f"Signup failed: {response.text}")
                return
            
            print(f"✓ Account created successfully!")
        
        token = response.json()["token"]
        print(f"✓ Authentication successful! Token obtained.")
        
        # Get current user config
        print("\nFetching current configuration...")
        response = await client.get(
            "http://localhost:8000/api/v1/user/configurations/user",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            print(f"Failed to fetch config: {response.text}")
            return
        
        current_config = response.json()
        print(f"✓ Current configuration retrieved.")
        print(f"  LLM Provider: {current_config.get('llm', {}).get('provider', 'N/A')}")
        print(f"  TTS Provider: {current_config.get('tts', {}).get('provider', 'N/A')}")
        print(f"  STT Provider: {current_config.get('stt', {}).get('provider', 'N/A')}")
        
        # Update with API keys from environment variables
        print("\nUpdating configuration with API keys from environment variables...")
        new_config = {
            "llm": {
                "provider": "groq",
                "api_key": groq_api_key,
                "model": "llama-3.1-8b-instant"
            },
            "tts": {
                "provider": "sarvam",
                "api_key": sarvam_api_key,
                "model": "bulbul:v2",
                "voice": "anushka"
            },
            "stt": current_config.get("stt", {
                "provider": "deepgram",
                "api_key": "",
                "model": "nova-2"
            }),
            "embeddings": current_config.get("embeddings", {
                "provider": "openai",
                "api_key": "",
                "model": "text-embedding-ada-002"
            })
        }
        
        response = await client.put(
            "http://localhost:8000/api/v1/user/configurations/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=new_config
        )
        
        if response.status_code != 200:
            print(f"Failed to update config: {response.text}")
            return
        
        updated_config = response.json()
        print(f"✓ Configuration updated successfully!")
        print(f"  LLM: {updated_config.get('llm', {}).get('provider')} ({updated_config.get('llm', {}).get('model')})")
        print(f"  TTS: {updated_config.get('tts', {}).get('provider')} ({updated_config.get('tts', {}).get('model')})")
        print(f"  STT: {updated_config.get('stt', {}).get('provider')} ({updated_config.get('stt', {}).get('model')})")
        print(f"  Embeddings: {updated_config.get('embeddings', {}).get('provider')} ({updated_config.get('embeddings', {}).get('model')})")

if __name__ == "__main__":
    asyncio.run(login_and_update_config())
