import logging
import asyncio
from typing import Optional
import io
import base64
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings

from config import Config

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        if Config.TTS_PROVIDER.lower() == "elevenlabs":
            self.client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
            self.provider = "elevenlabs"
        else:
            # Could implement Cartesia here as alternative
            logger.warning("Cartesia TTS not implemented, falling back to ElevenLabs")
            self.client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
            self.provider = "elevenlabs"
    
    async def generate_audio(self, text: str) -> Optional[bytes]:
        """Generate audio from text using TTS service"""
        try:
            if self.provider == "elevenlabs":
                return await self._generate_elevenlabs_audio(text)
            
        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            return None
    
    async def _generate_elevenlabs_audio(self, text: str) -> Optional[bytes]:
        """Generate audio using ElevenLabs TTS"""
        try:
            # Use async wrapper for ElevenLabs API call
            audio_generator = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.text_to_speech.convert(
                    voice_id=Config.VOICE_ID,
                    text=text,
                    model_id="eleven_turbo_v2",
                    voice_settings=VoiceSettings(
                        stability=0.75,
                        similarity_boost=0.85,
                        style=0.0,
                        use_speaker_boost=True
                    )
                )
            )
            
            # Convert generator to bytes
            audio_bytes = b""
            for chunk in audio_generator:
                audio_bytes += chunk
            
            logger.info(f"Generated {len(audio_bytes)} bytes of audio")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return None
    
    async def _generate_cartesia_audio(self, text: str) -> Optional[bytes]:
        """Generate audio using Cartesia TTS (placeholder for future implementation)"""
        # TODO: Implement Cartesia TTS integration
        logger.warning("Cartesia TTS not yet implemented")
        return None
    
    def get_usage_summary(self) -> dict:
        """Get TTS usage summary for metrics"""
        return {
            "provider": self.provider,
            "voice_id": Config.VOICE_ID,
            "model": "eleven_turbo_v2" if self.provider == "elevenlabs" else "unknown"
        }
