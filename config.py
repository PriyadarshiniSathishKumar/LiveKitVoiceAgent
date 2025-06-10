import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Livekit Configuration
    LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://localhost:7880")
    LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
    LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
    
    # STT Configuration
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
    
    # LLM Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    
    # TTS Configuration
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "")
    TTS_PROVIDER = os.getenv("TTS_PROVIDER", "elevenlabs")
    VOICE_ID = os.getenv("VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    
    # Agent Configuration
    AGENT_NAME = os.getenv("AGENT_NAME", "AI-Voice-Agent")
    TARGET_LATENCY = 2.0  # seconds
    
    # Metrics Configuration
    METRICS_DIR = "metrics"
    EXCEL_OUTPUT_DIR = "call_logs"
