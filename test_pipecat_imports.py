import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import asyncio
from dotenv import load_dotenv
load_dotenv('api/.env')

from api.services.pipecat.audio_config import create_audio_config
from api.services.pipecat.service_factory import create_stt_service, create_tts_service, create_llm_service
from api.enums import WorkflowRunMode

class STTConfig:
    provider = "sarvam"
    api_key = os.getenv("SARVAM_API_KEY", "")
    model = "saarika:v2.5"
    language = "hi-IN"

class TTSConfig:
    provider = "sarvam"
    api_key = os.getenv("SARVAM_API_KEY", "")
    model = "bulbul:v3"
    voice = "ritu"
    language = "hi-IN"

class LLMConfig:
    provider = "groq"
    api_key = os.getenv("GROQ_API_KEY", "")
    model = "llama-3.3-70b-versatile"

class UserConfig:
    stt = STTConfig()
    tts = TTSConfig()
    llm = LLMConfig()

async def test():
    print("Creating audio config...")
    audio_config = create_audio_config(WorkflowRunMode.TWILIO.value)
    
    print("Creating STT service...")
    stt = create_stt_service(UserConfig(), audio_config)
    print("STT service created:", stt)
    
    print("Creating TTS service...")
    tts = create_tts_service(UserConfig(), audio_config)
    print("TTS service created:", tts)
    
    print("Creating LLM service...")
    llm = create_llm_service(UserConfig())
    print("LLM service created:", llm)

if __name__ == "__main__":
    asyncio.run(test())
